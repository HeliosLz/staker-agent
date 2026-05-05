"""Deployment request schemas."""
from __future__ import annotations

from marshmallow import Schema, fields, ValidationError, validates_schema

from core.validation import is_valid_evm_address
from ..constants import VALID_NETWORKS, LIDO_CSM_NETWORKS


class KeyGenerationSchema(Schema):
    network = fields.String(load_default="holesky")
    num_validators = fields.Integer(load_default=1)
    withdrawal_address = fields.String(load_default=None, allow_none=True)
    use_lido_csm = fields.Boolean(load_default=False)

    VALID_NETWORKS = set(VALID_NETWORKS)
    LIDO_CSM_NETWORKS = set(LIDO_CSM_NETWORKS)

    @validates_schema
    def validate_values(self, data, **kwargs):
        network = data.get("network")
        use_lido_csm = data.get("use_lido_csm")
        errors = {}

        if network not in self.VALID_NETWORKS:
            errors["network"] = [f"Invalid network '{network}'. Allowed: {', '.join(sorted(self.VALID_NETWORKS))}"]

        if use_lido_csm and network not in self.LIDO_CSM_NETWORKS:
            errors["use_lido_csm"] = ["Lido CSM is only available on mainnet, hoodi, and holesky"]

        if data.get("num_validators", 1) <= 0:
            errors["num_validators"] = ["Number of validators must be positive"]

        addr = data.get("withdrawal_address")
        if addr is not None and not is_valid_evm_address(addr):
            errors["withdrawal_address"] = [
                "Must be a valid EVM address (0x followed by 40 hex characters)"
            ]

        if errors:
            raise ValidationError(errors)


class KeyImportSchema(Schema):
    keys_path = fields.String(required=True)
