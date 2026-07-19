# PLAN — env-doctor

## Scope

env-doctor is a single-purpose CLI that validates environment configuration
against a declarative schema and reports problems clearly.

In scope:

- A YAML schema format describing expected variables (name, required, type,
  constraints, default, secret flag).
- A `check` command that validates a `.env` file and/or the live process
  environment against the schema.
- A `diff` command that compares two env sources and reports drift.
- An `init` command that scaffolds a schema from an existing `.env`.
- Human-readable output plus a `--json` mode and CI-friendly exit codes.

## Tech approach

- **Language:** Python 3.11+ (broadly available, easy `pipx`/`pip` install,
  strong stdlib for parsing).
- **Dependencies:** keep minimal — `PyYAML` for schema parsing; stdlib only for
  everything else where practical.
- **Layout:**
  - `env_doctor/cli.py` — argument parsing and command dispatch.
  - `env_doctor/schema.py` — schema loading and validation model.
  - `env_doctor/checks.py` — type/constraint validators (int, url, bool, etc.).
  - `env_doctor/dotenv.py` — a small, dependency-free `.env` parser.
  - `tests/` — unit tests per module.
- **Validation model:** each variable resolves to a status of `ok`, `missing`,
  `invalid`, or `unexpected`. The overall run fails (non-zero exit) if any
  errors exist; warnings do not fail unless `--strict`.
- **Output:** default human-readable table with ✓/⚠/✗ markers; `--json` emits a
  structured report for CI consumption.

## Milestones

1. **M1 — Schema + parser:** define `env.schema.yaml`, load and normalize it,
   with tests covering valid/invalid schemas.
2. **M2 — check command:** required/type/range validation against `.env` and the
   process environment; readable output and correct exit codes.
3. **M3 — diff command:** compare two env sources, report added/removed/changed.
4. **M4 — init command:** generate a starter schema from an existing `.env`.
5. **M5 — CI polish:** `--json`, `--strict`, docs, and packaging metadata.

## Non-goals

- Managing or storing secrets (env-doctor validates, it does not vault).
- Encrypting/decrypting env files.
- Runtime injection of variables into a process (it checks, it does not run).
- Cloud-provider-specific secret backends (may be a future plugin, not core).
