"""Schema for the full deployment pipeline request."""
from __future__ import annotations

from marshmallow import Schema, fields, validates, ValidationError

from core.validation import is_valid_evm_address


class FullDeploySchema(Schema):
    network = fields.String(required=True)
    client = fields.String(required=True)
    fee_recipient = fields.String(load_default=None)
    withdrawal_address = fields.String(load_default=None)
    num_validators = fields.Integer(load_default=1)
    use_lido_csm = fields.Boolean(load_default=False)
    skip_keys = fields.Boolean(load_default=False)
    keystore_password = fields.String(load_default=None)
    remote = fields.Dict(load_default=None)

    @validates("fee_recipient")
    def validate_fee_recipient(self, value):
        if value is not None and not is_valid_evm_address(value):
            raise ValidationError("Must be a valid EVM address (0x + 40 hex chars)")

    @validates("withdrawal_address")
    def validate_withdrawal_address(self, value):
        if value is not None and not is_valid_evm_address(value):
            raise ValidationError("Must be a valid EVM address (0x + 40 hex chars)")
