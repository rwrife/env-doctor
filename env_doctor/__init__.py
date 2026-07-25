"""env-doctor core package."""

from .checks import CheckItem, CheckReport, validate_environment
from .diffing import DiffEntry, DiffReport, diff_environments, format_value
from .dotenv import DotenvParseError, load_dotenv, loads_dotenv
from .schema import EnvSchema, SchemaError, VariableDefinition, load_schema, loads_schema

__all__ = [
    "CheckItem",
    "CheckReport",
    "DiffEntry",
    "DiffReport",
    "DotenvParseError",
    "EnvSchema",
    "SchemaError",
    "VariableDefinition",
    "diff_environments",
    "format_value",
    "load_dotenv",
    "loads_dotenv",
    "load_schema",
    "loads_schema",
    "validate_environment",
]
