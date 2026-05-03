"""Configuration request schema."""
from __future__ import annotations

from marshmallow import Schema, fields, validates_schema, validates, ValidationError

from core.validation import is_valid_evm_address

from ..constants import VALID_NETWORKS, VALID_CLIENTS


class ConfigRequestSchema(Schema):
    network = fields.String(required=True)
    client = fields.String(required=True)
    fee_recipient = fields.String(load_default=None, allow_none=True)
    withdrawal_address = fields.String(load_default=None, allow_none=True)

    VALID_NETWORKS = set(VALID_NETWORKS)
    VALID_CLIENTS = set(VALID_CLIENTS)

    @validates("fee_recipient")
    def validate_fee_recipient(self, value):
        if value is not None and not is_valid_evm_address(value):
            raise ValidationError("Must be a valid EVM address (0x + 40 hex chars)")

    @validates("withdrawal_address")
    def validate_withdrawal_address(self, value):
        if value is not None and not is_valid_evm_address(value):
            raise ValidationError("Must be a valid EVM address (0x + 40 hex chars)")

    @validates_schema
    def validate_values(self, data, **kwargs):
        network = data.get("network")
        client = data.get("client")

        errors = {}
        if network and network not in self.VALID_NETWORKS:
            errors["network"] = [f"Invalid network '{network}'. Allowed: {', '.join(sorted(self.VALID_NETWORKS))}"]
        if client and client not in self.VALID_CLIENTS:
            errors["client"] = [f"Invalid client '{client}'. Allowed: {', '.join(sorted(self.VALID_CLIENTS))}"]

        if errors:
            raise ValidationError(errors)
