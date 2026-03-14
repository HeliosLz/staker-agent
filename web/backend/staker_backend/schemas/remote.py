"""Schemas for remote operations."""
from __future__ import annotations

from marshmallow import Schema, fields, validates_schema, ValidationError


class RemotePreflightSchema(Schema):
    host = fields.String(required=True)
    user = fields.String(load_default=None, allow_none=True)
    port = fields.Integer(load_default=22)
    ssh_key = fields.String(load_default=None, allow_none=True)

    @validates_schema
    def validate_values(self, data, **kwargs):
        port = data.get("port", 22)
        errors = {}
        if port <= 0 or port > 65535:
            errors["port"] = ["Port must be between 1 and 65535"]

        if errors:
            raise ValidationError(errors)


class RemoteDeploymentConfigSchema(Schema):
    network = fields.String(required=True)
    client = fields.String(required=True)
    fee_recipient = fields.String(load_default=None, allow_none=True)
    withdrawal_address = fields.String(load_default=None, allow_none=True)


class RemoteDeploySchema(Schema):
    connection = fields.Nested(RemotePreflightSchema, required=True)
    deployment = fields.Nested(RemoteDeploymentConfigSchema, required=True)
