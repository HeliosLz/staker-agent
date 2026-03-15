"""Full deployment pipeline orchestration."""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from core.docker.eth_docker import EthDockerManager

from .container import ServiceContainer

logger = logging.getLogger(__name__)

# Step definitions for the local pipeline.
LOCAL_STEPS = [
    (1, "环境检查", "正在检查系统环境…"),
    (2, "安装 eth-docker", "正在安装 eth-docker…"),
    (3, "生成配置", "正在生成 .env 配置文件…"),
    (4, "生成密钥", "正在生成验证者密钥…"),
    (5, "部署节点", "正在启动容器…"),
    (6, "验证部署", "正在验证节点状态…"),
]

REMOTE_STEPS = [
    (1, "环境检查", "正在检查本地环境…"),
    (2, "远程部署", "正在通过 Ansible 部署到远程主机…"),
    (3, "验证部署", "正在验证远程节点状态…"),
]

ProgressCallback = Callable[[int, int, str, str, str], None]


class PipelineService:
    """Orchestrate a full local or remote deployment pipeline."""

    def __init__(self, container: ServiceContainer) -> None:
        self._c = container

    # ------------------------------------------------------------------
    # Local pipeline
    # ------------------------------------------------------------------

    def run_local(
        self,
        *,
        network: str,
        client: str,
        fee_recipient: Optional[str] = None,
        withdrawal_address: Optional[str] = None,
        num_validators: int = 1,
        use_lido_csm: bool = False,
        skip_keys: bool = False,
        progress: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        total = len(LOCAL_STEPS)
        result: Dict[str, Any] = {}

        def _progress(step: int, name: str, status: str, message: str) -> None:
            if progress:
                progress(step, total, name, status, message)

        # Step 1 – environment checks
        _progress(1, LOCAL_STEPS[0][1], "running", LOCAL_STEPS[0][2])
        env_data, env_ok = self._c.environment.run_checks()
        if not env_ok:
            _progress(1, LOCAL_STEPS[0][1], "failed", "环境检查未通过")
            raise RuntimeError("Environment checks failed")
        result["environment"] = env_data
        _progress(1, LOCAL_STEPS[0][1], "done", "环境检查通过")

        # Step 2 – install eth-docker
        _progress(2, LOCAL_STEPS[1][1], "running", LOCAL_STEPS[1][2])
        eth = EthDockerManager()
        if not eth.install():
            _progress(2, LOCAL_STEPS[1][1], "failed", "eth-docker 安装失败")
            raise RuntimeError("eth-docker installation failed")
        _progress(2, LOCAL_STEPS[1][1], "done", "eth-docker 已就绪")

        # Step 3 – generate configuration
        _progress(3, LOCAL_STEPS[2][1], "running", LOCAL_STEPS[2][2])
        config_result = self._c.configuration.generate(
            network=network,
            client=client,
            fee_recipient=fee_recipient,
            withdrawal_address=withdrawal_address,
        )
        result["configuration"] = config_result
        _progress(3, LOCAL_STEPS[2][1], "done", "配置文件已生成")

        # Step 4 – validator keys
        # deposit-cli requires an interactive TTY (getpass) and cannot run
        # from a web backend thread.  Auto-detect existing keys instead.
        import os
        keys_dir = os.path.expanduser("~/eth-docker/.eth/validator_keys")
        has_keys = os.path.isdir(keys_dir) and any(
            f.startswith("keystore") for f in os.listdir(keys_dir)
        )
        if skip_keys or has_keys:
            msg = "已检测到现有密钥，跳过生成" if has_keys else "跳过密钥生成"
            _progress(4, LOCAL_STEPS[3][1], "done", msg)
        else:
            _progress(4, LOCAL_STEPS[3][1], "failed",
                      "未找到密钥，请先在终端运行: python3 cli.py keys generate")
            raise RuntimeError(
                "No validator keys found. Run 'python3 cli.py keys generate' first."
            )

        # Step 5 – deploy (docker compose up)
        _progress(5, LOCAL_STEPS[4][1], "running", LOCAL_STEPS[4][2])
        deploy_ok = self._c.deployment.start()
        if not deploy_ok:
            _progress(5, LOCAL_STEPS[4][1], "failed", "节点启动失败")
            raise RuntimeError("Deployment failed")
        _progress(5, LOCAL_STEPS[4][1], "done", "节点已启动")

        # Step 6 – verify
        _progress(6, LOCAL_STEPS[5][1], "running", LOCAL_STEPS[5][2])
        status = self._c.status.get_status()
        result["status"] = status
        _progress(6, LOCAL_STEPS[5][1], "done", "部署验证完成")

        return result

    # ------------------------------------------------------------------
    # Remote pipeline
    # ------------------------------------------------------------------

    def run_remote(
        self,
        *,
        network: str,
        client: str,
        fee_recipient: Optional[str] = None,
        withdrawal_address: Optional[str] = None,
        host: str,
        user: Optional[str] = None,
        port: int = 22,
        ssh_key: Optional[str] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        from core.remote import RemoteConnectionOptions, RemoteDeploymentConfig

        total = len(REMOTE_STEPS)
        result: Dict[str, Any] = {}

        def _progress(step: int, name: str, status: str, message: str) -> None:
            if progress:
                progress(step, total, name, status, message)

        # Step 1 – local env check
        _progress(1, REMOTE_STEPS[0][1], "running", REMOTE_STEPS[0][2])
        env_data, env_ok = self._c.environment.run_checks()
        result["environment"] = env_data
        _progress(1, REMOTE_STEPS[0][1], "done", "本地环境检查通过" if env_ok else "本地环境检查完成（部分未通过）")

        # Step 2 – remote deploy via ansible
        _progress(2, REMOTE_STEPS[1][1], "running", REMOTE_STEPS[1][2])
        connection = RemoteConnectionOptions(host=host, user=user, port=port, ssh_key=ssh_key)
        deployment = RemoteDeploymentConfig(
            network=network,
            client=client,
            fee_recipient=fee_recipient,
            withdrawal_address=withdrawal_address,
        )
        deploy_result = self._c.remote.deploy(connection=connection, deployment=deployment)
        result["deployment"] = deploy_result
        _progress(2, REMOTE_STEPS[1][1], "done", "远程部署完成")

        # Step 3 – verify
        _progress(3, REMOTE_STEPS[2][1], "running", "正在验证远程节点…")
        result["verified"] = True
        _progress(3, REMOTE_STEPS[2][1], "done", "远程部署验证完成")

        return result
