"""
Validator key generation and management
Supports both solo staking and Lido CSM
"""
import os
import subprocess
import shutil
from core.exceptions import KeyGenerationError, UserCancelledError

# Lido CSM withdrawal vaults (official addresses)
LIDO_WITHDRAWAL_VAULT_MAINNET = "0xb9d7934878b5fb9610b3fe8a5e441e8fad7e293f"
LIDO_EL_REWARDS_VAULT_MAINNET = "0x388C818CA8B9251b393131C08a736A67ccB19297"
LIDO_WITHDRAWAL_VAULT_HOODI = "0x4473dCDDbf77679A643BdB654dbd86D67F8d32f2"
LIDO_EL_REWARDS_VAULT_HOODI = "0x9b108015fe433F173696Af3Aa0CF7CDb3E104258"
LIDO_WITHDRAWAL_VAULT_HOLESKY = "0xF0179dEC45a37423EAD4FaD5fCb136197872EAd9"
LIDO_EL_REWARDS_VAULT_HOLESKY = "0xE73a3602b99f1f913e72F8bdcBC235e206794Ac8"

class KeyManager:
    def __init__(self, eth_docker_path=None):
        self.eth_docker_path = eth_docker_path or os.path.expanduser('~/eth-docker')
        self.keys_path = os.path.join(self.eth_docker_path, '.eth', 'validator_keys')

    def check_eth_docker(self):
        """Check if eth-docker is installed"""
        if not os.path.exists(self.eth_docker_path):
            raise KeyGenerationError("eth-docker not found.")

    def generate_keys(self, network='holesky', num_validators=1, withdrawal_address=None, use_lido_csm=False):
        """
        Generate validator keys using deposit-cli

        Args:
            network: Network to generate keys for (mainnet, holesky, sepolia)
            num_validators: Number of validators to create
            withdrawal_address: Custom withdrawal address, or None to use Lido CSM vault
            use_lido_csm: If True, use Lido CSM withdrawal vault automatically

        Returns:
            dict with status, message, and paths
        """
        self.check_eth_docker()

        # Determine withdrawal address
        if use_lido_csm:
            if network == 'mainnet':
                withdrawal_address = LIDO_WITHDRAWAL_VAULT_MAINNET
            elif network == 'hoodi':
                withdrawal_address = LIDO_WITHDRAWAL_VAULT_HOODI
            elif network == 'holesky':
                withdrawal_address = LIDO_WITHDRAWAL_VAULT_HOLESKY
            else:
                raise KeyGenerationError(f'Lido CSM not available on {network}')

        # Check if Docker is available
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                shell=False
            )
            if result.returncode != 0:
                raise KeyGenerationError('Docker is not installed or not running.')
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise KeyGenerationError('Docker is not installed or not running.')

        # Prepare docker compose command
        try:
            # Create .eth directory if it doesn't exist
            eth_dir = os.path.join(self.eth_docker_path, '.eth')
            os.makedirs(eth_dir, exist_ok=True)

            # Build the command
            cmd = [
                'docker', 'compose',
                'run', '--rm',
                'deposit-cli-new',
                '--num_validators', str(num_validators),
                '--chain', network
            ]

            if withdrawal_address:
                cmd.extend(['--eth1_withdrawal_address', withdrawal_address])

            # Run the command interactively
            result = subprocess.run(
                cmd,
                cwd=self.eth_docker_path,
                env={**os.environ, 'NETWORK': network},
                shell=False
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
                    'withdrawal_address': withdrawal_address
                }
            else:
                raise KeyGenerationError('Key generation failed.')

        except Exception as e:
            if isinstance(e, KeyGenerationError):
                raise
            raise KeyGenerationError(f"Error generating keys: {str(e)}")

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
            # Ensure destination directory exists
            os.makedirs(self.keys_path, exist_ok=True)
            copied_files = []

            # Copy files
            if os.path.isdir(keys_path):
                files = os.listdir(keys_path)
                for file in files:
                    src = os.path.join(keys_path, file)
                    dst = os.path.join(self.keys_path, file)
                    shutil.copy2(src, dst)
                    copied_files.append(file)
            else:
                # Single file
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
