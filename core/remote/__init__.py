"""
Remote deployment helpers.

This package provides thin wrappers around SSH, Ansible execution,
and preflight checks that enable remote deployment of validator stacks.
"""

from .ssh_client import SSHClient, SSHCommandError
from .ansible_runner import AnsibleRunner, AnsibleExecutionError
from .preflight import RemotePreflightResult, RemotePreflightChecker
from .deploy_manager import RemoteDeployManager, RemoteConnectionOptions, RemoteDeploymentConfig

__all__ = [
    "SSHClient",
    "SSHCommandError",
    "AnsibleRunner",
    "AnsibleExecutionError",
    "RemotePreflightResult",
    "RemotePreflightChecker",
    "RemoteDeployManager",
    "RemoteConnectionOptions",
    "RemoteDeploymentConfig",
]
