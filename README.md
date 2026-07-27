# env-doctor

> Diagnose and validate `.env` files against a schema — catch missing, extra, and misconfigured environment variables **before** they break your app.

## Project overview

**env-doctor** is a small command-line tool that inspects your environment
configuration (`.env` files, exported shell vars, or CI secrets manifests) and
checks them against a declarative schema. It reports what's missing, what's
unexpected, what's malformed, and what's about to bite you in production.

Think of it as a linter + health check for your environment variables.

## Motivation

Environment misconfiguration is one of the most common — and most avoidable —
causes of "works on my machine" failures and production incidents:

- A new required variable is added in code but nobody updates the deployment.
- A `.env.example` drifts out of sync with the real variables the app needs.
- A value is present but empty, or a URL/port/boolean is malformed.
- Secrets get committed, or a stray variable leaks between environments.

env-doctor makes these problems **loud and early**: a single command in local
dev, CI, or a container entrypoint that fails fast with a clear diagnosis
instead of a cryptic runtime crash three layers deep.

## Use cases

- **Local onboarding** — a new developer clones the repo and runs
  `env-doctor check` to see exactly which variables they still need to set.
- **CI gate** — block a build/deploy when required env vars are missing or
  malformed.
- **Container entrypoint** — validate the environment before the main process
  boots, failing with a readable error.
- **Drift detection** — compare `.env` against `.env.example` (or a schema) and
  flag additions/removals on both sides.

## How to use

1. Install from source:
   ```bash
   git clone https://github.com/rwrife/env-doctor.git
   cd env-doctor

   # preferred isolated install
   pipx install .

   # or install into the active Python environment
   pip install .
   ```
2. Confirm the command is available:
   ```bash
   env-doctor --help
   ```
3. Create a schema describing the variables your app expects (see example
   below), or generate one from an existing `.env`:
   ```bash
   env-doctor init --from .env > env.schema.yaml
   ```
4. Run a check against your environment:
   ```bash
   env-doctor check --schema env.schema.yaml --env .env
   ```

## Example commands and workflows

```bash
# Validate the current process environment against a schema
env-doctor check --schema env.schema.yaml

# Validate a specific .env file, strict mode (unexpected vars are errors)
env-doctor check --schema env.schema.yaml --env .env.production --strict

# Emit machine-readable JSON for CI
env-doctor check --schema env.schema.yaml --env .env --json

# Diff two env sources and show drift
env-doctor diff --a .env.example --b .env

# Generate a starter schema from an existing .env
env-doctor init --from .env > env.schema.yaml
```

Example `env.schema.yaml`:

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
    default: "false"
  API_KEY:
    required: true
    type: string
    secret: true
```

See [`docs/schema-format.md`](./docs/schema-format.md) for the formal schema
specification and loader validation rules.

Example output:

```
env-doctor: checking .env against env.schema.yaml

  ✗ DATABASE_URL   missing (required)
  ✗ PORT           "abc" is not a valid int
  ⚠ LEGACY_TOKEN   present but not in schema (unexpected)
  ✓ DEBUG          ok (default applied: false)
  ✓ API_KEY        ok

2 errors, 1 warning — environment is NOT healthy
```

Example JSON output (`--json`):

```json
{
  "counts": {
    "invalid": 1,
    "missing": 0,
    "ok": 1,
    "unexpected": 1
  },
  "errors": 1,
  "items": [
    {
      "message": "ok",
      "name": "APP_NAME",
      "source": "env",
      "status": "ok",
      "value": "demo"
    },
    {
      "message": "expected int but got 'abc'",
      "name": "PORT",
      "source": "env",
      "status": "invalid",
      "value": "abc"
    },
    {
      "message": "present but not declared in schema",
      "name": "EXTRA",
      "source": "env",
      "status": "unexpected",
      "value": "1"
    }
  ],
  "schema": "env.schema.yaml",
  "source": ".env",
  "strict": false,
  "warnings": 1
}
```

Exit codes (`check`):

- `0` — healthy (or warnings only in non-strict mode)
- `1` — one or more errors (invalid/missing), or warnings promoted to errors by `--strict`
- `2` — CLI/schema/.env usage errors (bad args, malformed schema/.env)

## Current status / next milestones

- [x] Repository bootstrapped with README and PLAN
- [x] Define the schema format (`env.schema.yaml`) and parser
- [x] Implement `check` command with required/type/range validation
- [x] Implement `diff` command for env drift
- [x] Implement `init` schema generation from an existing `.env`
- [x] Machine-readable output (`--json`) and non-zero exit codes for CI
- [x] Minimal GitHub Actions workflow runs install + test checks
- [x] Packaging and installation instructions

See [PLAN.md](./PLAN.md) for scope, technical approach, and milestones.

---

_This project is part of an automated tool-lab experiment (topic:
`auto-tool-lab`)._
