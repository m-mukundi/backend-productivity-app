from marshmallow import Schema, fields, validate

from models import VALID_STATUSES


class RegisterSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=2, max=80))
    password = fields.String(required=True, validate=validate.Length(min=6, max=128))
    password_confirmation = fields.String(required=True)


class LoginSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)


def flatten_errors(messages):
    """Flatten marshmallow's {field: [msg, ...]} error dict into a flat list of strings."""
    flat = []
    for field, field_messages in messages.items():
        for message in field_messages:
            flat.append(f"{field}: {message}" if field != "_schema" else message)
    return flat


class TaskCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=120))
    description = fields.String(required=False, allow_none=True, load_default="")
    status = fields.String(
        required=False,
        load_default="pending",
        validate=validate.OneOf(VALID_STATUSES),
    )


class TaskUpdateSchema(Schema):
    title = fields.String(required=False, validate=validate.Length(min=1, max=120))
    description = fields.String(required=False, allow_none=True)
    status = fields.String(required=False, validate=validate.OneOf(VALID_STATUSES))
