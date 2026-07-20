# env.schema.yaml format

`env-doctor` expects a top-level `variables` mapping.

Each entry under `variables` is one environment variable definition with these
supported fields:

- `required` (`bool`) — whether the variable must be present
- `type` (`string`) — one of: `string`, `int`, `float`, `bool`, `url`
- `min` (`number`) — optional lower bound for numeric (`int`/`float`) variables
- `max` (`number`) — optional upper bound for numeric (`int`/`float`) variables
- `default` (any YAML scalar) — optional default value
- `secret` (`bool`) — whether the variable should be treated as secret

## Example

```yaml
variables:
  DATABASE_URL:
    required: true
    type: url

  PORT:
    required: true
    type: int
    min: 1
    max: 65535

  DEBUG:
    required: false
    type: bool
    default: false

  API_KEY:
    required: true
    type: string
    secret: true
```

## Loader behavior

- Malformed YAML raises a `SchemaError` with a clear message.
- Unsupported field names are rejected.
- Unsupported `type` values are rejected.
- Non-boolean `required` / `secret` values are rejected.
- `min` / `max` must be numeric and only apply to numeric types.
- `min > max` is rejected.
