"""Schema for the full deployment pipeline request."""
from __future__ import annotations

from marshmallow import Schema, fields


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
