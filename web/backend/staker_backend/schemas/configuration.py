"""Configuration request schema."""
from __future__ import annotations

from marshmallow import Schema, fields, validates_schema, ValidationError

from ..constants import VALID_NETWORKS, VALID_CLIENTS


class ConfigRequestSchema(Schema):
    network = fields.String(required=True)
    client = fields.String(required=True)
    fee_recipient = fields.String(load_default=None, allow_none=True)
    withdrawal_address = fields.String(load_default=None, allow_none=True)

    VALID_NETWORKS = set(VALID_NETWORKS)
    VALID_CLIENTS = set(VALID_CLIENTS)

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
