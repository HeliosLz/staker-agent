"""
Validator key generation and management
Supports both solo staking and Lido CSM
"""
import logging
import os
import re
import subprocess
import shutil

from core.exceptions import KeyGenerationError, UserCancelledError
from core.validation import validate_evm_address

logger = logging.getLogger(__name__)

# Lido CSM withdrawal vault addresses keyed by network.
# Canonical source: web/backend/staker_backend/constants.py (LIDO_CSM_ADDRESSES).
# Duplicated here to keep core/ free of web-backend imports.
_LIDO_WITHDRAWAL_VAULTS = {
    "mainnet": "0xb9d7934878b5fb9610b3fe8a5e441e8fad7e293f",
    "hoodi": "0x4473dCDDbf77679A643BdB654dbd86D67F8d32f2",
    "holesky": "0xF0179dEC45a37423EAD4FaD5fCb136197872EAd9",
}


def _eip55_checksum(address: str) -> str:
    """Compute EIP-55 mixed-case checksum for an Ethereum address."""
    from Crypto.Hash import keccak
    addr = address.lower().replace("0x", "")
    k = keccak.new(digest_bits=256)
    k.update(addr.encode("ascii"))
    hash_hex = k.hexdigest()
    checksummed = "0x"
    for i, c in enumerate(addr):
        if c in "0123456789":
            checksummed += c
        elif int(hash_hex[i], 16) >= 8:
            checksummed += c.upper()
        else:
            checksummed += c.lower()
    return checksummed


class KeyManager:
    def __init__(self, eth_docker_path: str):
        self.eth_docker_path = eth_docker_path
        self.keys_path = os.path.join(self.eth_docker_path, '.eth', 'validator_keys')

    def check_eth_docker(self):
        """Check if eth-docker is installed"""
        if not os.path.exists(self.eth_docker_path):
            raise KeyGenerationError("eth-docker not found.")

    def generate_keys(
        self,
        network='holesky',
        num_validators=1,
        withdrawal_address=None,
        use_lido_csm=False,
        keystore_password=None,
    ):
        """
        Generate validator keys using deposit-cli via pexpect.

        When *keystore_password* is provided the entire process runs
        non-interactively and returns the generated mnemonic.
        When it is ``None`` the command runs with an inherited TTY
        (legacy interactive mode for CLI usage).
        """
        self.check_eth_docker()

        # Determine withdrawal address
        if use_lido_csm:
            vault = _LIDO_WITHDRAWAL_VAULTS.get(network)
            if not vault:
                raise KeyGenerationError(f'Lido CSM not available on {network}')
            withdrawal_address = vault

        if withdrawal_address:
            try:
                validate_evm_address(withdrawal_address, "withdrawal_address")
            except ValueError as exc:
                raise KeyGenerationError(str(exc)) from exc

        # Docker availability check
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True, text=True, timeout=5, shell=False,
            )
            if result.returncode != 0:
                raise KeyGenerationError('Docker is not installed or not running.')
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise KeyGenerationError('Docker is not installed or not running.')

        # Ensure .eth dir exists
        os.makedirs(os.path.join(self.eth_docker_path, '.eth'), exist_ok=True)

        if keystore_password is not None:
            return self._generate_keys_auto(
                network=network,
                num_validators=num_validators,
                withdrawal_address=withdrawal_address,
                use_lido_csm=use_lido_csm,
                keystore_password=keystore_password,
            )
        else:
            return self._generate_keys_interactive(
                network=network,
                num_validators=num_validators,
                withdrawal_address=withdrawal_address,
                use_lido_csm=use_lido_csm,
            )

    # ------------------------------------------------------------------
    # Container cleanup
    # ------------------------------------------------------------------

    def _cleanup_stale_containers(self) -> None:
        """Remove leftover deposit-cli containers and orphan networks."""
        try:
            subprocess.run(
                ['docker', 'compose', '-f', 'deposit-cli.yml', 'rm', '-f', '-s'],
                cwd=self.eth_docker_path,
                capture_output=True, text=True, timeout=30,
            )
        except Exception as exc:
            logger.warning("Failed to clean up stale deposit-cli containers: %s", exc)
        try:
            subprocess.run(
                ['docker', 'compose', '-f', 'deposit-cli.yml', 'down', '--remove-orphans'],
                cwd=self.eth_docker_path,
                capture_output=True, text=True, timeout=30,
            )
        except Exception as exc:
            logger.warning("Failed to clean up orphan networks: %s", exc)

    # ------------------------------------------------------------------
    # Automated generation via pexpect (used by web pipeline)
    # ------------------------------------------------------------------

    def _generate_keys_auto(
        self, *, network, num_validators, withdrawal_address, use_lido_csm, keystore_password,
    ):
        kwargs = dict(
            network=network, num_validators=num_validators,
            withdrawal_address=withdrawal_address, use_lido_csm=use_lido_csm,
            keystore_password=keystore_password,
        )
        self._cleanup_stale_containers()
        try:
            return self._generate_keys_auto_inner(**kwargs)
        except KeyGenerationError:
            logger.warning("First key generation attempt failed, retrying after cleanup...")
            self._cleanup_stale_containers()
            return self._generate_keys_auto_inner(**kwargs)

    def _generate_keys_auto_inner(
        self, *, network, num_validators, withdrawal_address, use_lido_csm, keystore_password,
    ):
        import pexpect

        checksummed = _eip55_checksum(withdrawal_address) if withdrawal_address else ''

        cmd = (
            f'docker compose -f deposit-cli.yml run --rm '
            f'deposit-cli-new '
            f'--num_validators {num_validators} '
            f'--chain {network}'
        )
        if checksummed:
            cmd += f' --eth1_withdrawal_address {checksummed}'

        logger.info("Starting deposit-cli: %s", cmd)

        child = pexpect.spawn(
            '/bin/bash', ['-c', cmd],
            cwd=self.eth_docker_path,
            env={**os.environ, 'NETWORK': network, 'TERM': 'dumb'},
            timeout=300,
            encoding='utf-8',
        )

        try:
            # 1. UI language
            child.expect(r'language.*\[.*English.*\]', timeout=120)
            child.sendline('3')

            # 2. "Press any key to continue..." (internet warning)
            child.expect(r'Press any key', timeout=30)
            child.sendline('')

            # 3-6. The remaining prompts (mnemonic language, password, withdrawal
            #       address confirmation) come in varying order depending on whether
            #       flags were passed via CLI.  Use a flexible loop that handles
            #       each prompt as it appears, until we see the mnemonic "Press any key".

            while True:
                idx = child.expect([
                    r'mnemonic.*word list',           # 0: mnemonic language
                    r'[Cc]reate a password|password.*keystore',  # 1: password
                    r'[Rr]epeat.*keystore.*password|Repeat your keystore password',  # 2: repeat password
                    r'[Rr]epeat your withdrawal',     # 3: confirm withdrawal
                    r'withdrawal address.*\[',        # 4: enter withdrawal
                    r'[Cc]ompounding.*\[no\]|regular validator',  # 5: compounding vs regular
                    r'Press any key',                 # 6: done with prompts
                ], timeout=60)

                if idx == 0:
                    child.sendline('4')
                elif idx == 1:
                    child.sendline(keystore_password)
                elif idx == 2:
                    child.sendline(keystore_password)
                elif idx == 3:
                    child.sendline(checksummed)
                elif idx == 4:
                    child.sendline(checksummed if withdrawal_address else '')
                elif idx == 5:
                    child.sendline('')  # default: no (regular validators)
                else:
                    # idx == 6: "Press any key" — mnemonic is now displayed
                    break

            # 7. The loop broke on "Press any key when you have written down
            #    your mnemonic."  The mnemonic is in child.before.
            output_before = child.before or ''

            mnemonic = None
            for line in output_before.split('\n'):
                words = line.strip().split()
                if len(words) == 24 and all(w.isalpha() for w in words):
                    mnemonic = line.strip()
                    break

            if not mnemonic:
                raise KeyGenerationError(
                    'Could not capture mnemonic from deposit-cli output.'
                )

            # Press key to continue past the mnemonic display
            child.sendline('')

            # 8. "Please type your mnemonic ... to confirm"
            child.expect(r'type your mnemonic', timeout=30)
            child.sendline(mnemonic)

            # 9. Wait for key generation to complete, then final "Press any key"
            #    There may be multiple "Press any key" prompts — keep responding
            while True:
                idx = child.expect([r'Press any key', pexpect.EOF], timeout=120)
                if idx == 0:
                    child.sendline('')
                else:
                    break

            child.close()

            # chown in the entrypoint may fail on macOS, causing a non-zero
            # exit code even though keys were generated.  We check for the
            # actual keystore files instead of trusting the exit code.

        except pexpect.TIMEOUT as exc:
            child.close(force=True)
            self._cleanup_stale_containers()
            raise KeyGenerationError(
                f'deposit-cli timed out. Last output: {child.before[-300:] if child.before else "N/A"}'
            ) from exc
        except pexpect.EOF:
            child.close()
            self._cleanup_stale_containers()
            raise KeyGenerationError(
                f'deposit-cli exited unexpectedly. Last output: {child.before[-300:] if child.before else "N/A"}'
            )

        deposit_data_path = self._find_deposit_data()
        has_keystore = os.path.isdir(self.keys_path) and any(
            f.startswith('keystore') for f in os.listdir(self.keys_path)
        )
        if not has_keystore:
            raise KeyGenerationError('deposit-cli ran but no keystore files were created.')

        return {
            'status': 'success',
            'message': 'Keys generated successfully',
            'keys_path': self.keys_path,
            'deposit_data_path': deposit_data_path,
            'network': network,
            'use_lido_csm': use_lido_csm,
            'withdrawal_address': withdrawal_address,
            'mnemonic': mnemonic,
        }

    # ------------------------------------------------------------------
    # Interactive generation (legacy CLI mode)
    # ------------------------------------------------------------------

    def _generate_keys_interactive(
        self, *, network, num_validators, withdrawal_address, use_lido_csm,
    ):
        cmd = [
            'docker', 'compose',
            '-f', 'deposit-cli.yml',
            'run', '--rm',
            'deposit-cli-new',
            '--num_validators', str(num_validators),
            '--chain', network,
        ]
        if withdrawal_address:
            cmd.extend(['--eth1_withdrawal_address', _eip55_checksum(withdrawal_address)])

        result = subprocess.run(
            cmd,
            cwd=self.eth_docker_path,
            env={**os.environ, 'NETWORK': network},
            shell=False,
        )

        if result.returncode == 0:
            deposit_data_path = self._find_deposit_data()
            return {
                'status': 'success',
                'message': 'Keys generated successfully',
                'keys_path': self.keys_path,
                'deposit_data_path': deposit_data_path,
                'network': network,
                'use_lido_csm': use_lido_csm,
                'withdrawal_address': withdrawal_address,
            }
        else:
            raise KeyGenerationError('Key generation failed.')

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_deposit_data(self):
        """Find the deposit_data.json file"""
        try:
            if os.path.exists(self.keys_path):
                for file in os.listdir(self.keys_path):
                    if 'deposit_data' in file and file.endswith('.json'):
                        return os.path.join(self.keys_path, file)
        except Exception:
            pass
        return None

    def get_keys_info(self):
        """Get information about existing keys"""
        info = {
            'exists': False,
            'keys_path': self.keys_path,
            'deposit_data_files': [],
            'keystore_files': []
        }

        if not os.path.exists(self.keys_path):
            return info

        try:
            files = os.listdir(self.keys_path)
            if not files:
                return info

            info['exists'] = True
            info['deposit_data_files'] = [f for f in files if 'deposit_data' in f]
            info['keystore_files'] = [f for f in files if 'keystore' in f]
            return info

        except Exception as e:
            raise KeyGenerationError(f"Error listing keys: {str(e)}")

    def import_keys(self, keys_path):
        """Import existing keys"""
        if not os.path.exists(keys_path):
            raise KeyGenerationError(f"Path not found: {keys_path}")

        try:
            os.makedirs(self.keys_path, exist_ok=True)
            copied_files = []

            if os.path.isdir(keys_path):
                files = os.listdir(keys_path)
                for file in files:
                    src = os.path.join(keys_path, file)
                    dst = os.path.join(self.keys_path, file)
                    shutil.copy2(src, dst)
                    copied_files.append(file)
            else:
                filename = os.path.basename(keys_path)
                dst = os.path.join(self.keys_path, filename)
                shutil.copy2(keys_path, dst)
                copied_files.append(filename)

            return {
                'status': 'success',
                'copied_files': copied_files,
                'keys_path': self.keys_path
            }

        except Exception as e:
            raise KeyGenerationError(f"Error importing keys: {str(e)}")
