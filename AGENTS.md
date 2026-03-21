# AGENTS.md

## Purpose

This repository provides OpenAI API-compatible local servers for embeddings and rerank workloads.
The primary runtime is `docker compose`.
The system is intentionally stateless and does not use a database.

AI agents working in this repository must optimize for:

- predictable local development with `uv`
- reproducible container execution with `docker compose`
- explicit typing and schema validation
- OpenAPI-compatible FastAPI development
- small, task-scoped commits with clear intent

## Current Architecture

- `embeddings-api-server.py`: FastAPI application for `/v1/embeddings`
- `reranker-api-server.py`: FastAPI application for `/v1/rerank`
- `LoggerConfig.py`: shared logging configuration
- `compose.yaml`: canonical local orchestration entrypoint
- `Docker/`: container build definitions
- `pyproject.toml` and `uv.lock`: Python dependency management via `uv`

This repository does not persist application state.
Do not introduce a database, migration tool, or ORM unless the user explicitly requests that change.

## Source of Truth

When updating operational instructions or startup flows, keep these aligned:

- `AGENTS.md`
- `README.md`
- `compose.yaml`
- `Docker/` contents
- `pyproject.toml`

If one of these changes and another becomes stale, update both in the same task when feasible.

## Runtime Assumptions

- `docker compose` is the default way to run the system
- local direct execution with `uv run` is supported for development and debugging
- model artifacts are expected to be cached through mounted volumes
- GPU-oriented configuration in `compose.yaml` is intentional and must not be removed casually
- the application should remain usable without a database

## Required Engineering Standards

### Python and Tooling

- Use the repository's `uv` workflow for dependency and command execution.
- Prefer `uv sync` and `uv run ...` over direct `pip` or bare `python`.
- Keep `pyproject.toml` and `uv.lock` consistent.
- Use `ruff` for linting and formatting checks.
- Use `ty` for type checking when configured in the repository.

### Typing

- Add explicit type annotations to public functions, methods, and important module-level variables.
- Prefer built-in collection generics such as `list[str]` instead of legacy `typing.List`.
- Use `pydantic` models for request and response schemas and for custom structured domain data where appropriate.
- Avoid untyped dictionaries for public API contracts when a schema model can express the shape clearly.

### FastAPI and OpenAPI

- Preserve OpenAPI compatibility for every public API endpoint.
- Use FastAPI request/response models rather than undocumented ad hoc payloads when possible.
- If an endpoint behavior changes, ensure the generated OpenAPI schema still reflects reality.
- Prefer explicit `response_model` declarations for stable APIs when practical.

### Comments and Documentation

- The policy "comment every public class and method" is valid, but avoid verbose comments that simply create maintenance overhead.
- As a rule, keep public comments short and focused on:
  - summary
  - responsibility
  - implementation intent
  - side effects
  - exception conditions
- Every public class must have a docstring or comment that explains:
  - what it represents
  - why it exists
- Every public function or method must have a docstring or comment that explains:
  - what it does
  - important implementation intent or constraints
- Add comments to private methods when the logic is non-obvious, failure-prone, or domain-specific.
- Do not add low-value comments that merely restate the code literally.

### Testing

- Every public method introduced or changed by a task must have tests.
- Endpoint changes require API-level tests, not only helper-level tests.
- Prefer lightweight tests that avoid downloading heavy model assets unless the test explicitly covers integration behavior.
- Use mocks, fakes, or dependency overrides to keep unit and API tests fast and deterministic.
- If a change is not safely testable with the current structure, document the gap and improve the structure in the same task when reasonable.

### Logging and Error Handling

- Preserve structured, useful server logs.
- Do not log secrets or sensitive request contents casually.
- Return clear HTTP error responses for invalid input and unexpected failures.
- Keep logging behavior compatible with both direct execution and container execution.

## Docker Compose Rules

- Treat `compose.yaml` as the main local orchestration contract.
- Prefer validating multi-service behavior with `docker compose` commands when the task affects runtime integration.
- Do not hardcode host-only paths that would break container portability.
- Keep environment variable names aligned across:
  - `compose.yaml`
  - `.env` usage
  - application code
  - `README.md`
- If a service port, volume, or startup command changes, update documentation in the same task.

## No-Database Constraints

- Favor stateless request handling.
- Store temporary processing state in memory only when necessary and when bounded.
- Do not add persistence assumptions to APIs.
- Health checks, readiness checks, and startup validation must not assume a database dependency.

## Preferred Change Pattern

For non-trivial work, agents should generally proceed in this order:

1. Inspect the affected Python entrypoints, shared config, and compose setup.
2. Update schemas, typing, and comments first so the intended contract is explicit.
3. Implement behavior changes.
4. Add or update tests.
5. Run lint, type check, and tests.
6. Update `README.md` if behavior or operations changed.

## Validation Commands

Use the smallest relevant set for the task. Prefer `uv run` for Python tools.

Typical commands:

```sh
uv sync
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
docker compose config
docker compose up --build
```

If a command cannot be run because the tool is not yet configured, note that clearly in the final report and avoid claiming validation that did not happen.

## Commit Rules

- Keep commits task-scoped at minimum.
- Commit messages must include both:
  - a concise summary of the change
  - the reason or intent behind the change
- Before a commit, run the relevant lint, type-check, and test commands.
- Do not mix unrelated refactors with functional changes unless the refactor is required to make the functional change safe.

Recommended commit message style:

```text
feat: add typed request validation for rerank endpoint

Why:
- make the API contract explicit in OpenAPI
- prevent malformed payloads from reaching model execution
```

## What to Avoid

- introducing a database or persistent state without explicit user approval
- bypassing `uv` for Python dependency management
- making compose-only behavior diverge from local direct execution without documenting it
- adding silent fallback behavior that hides configuration errors
- weakening type information to avoid fixing a real issue
- skipping tests for changed public behavior without stating why
- changing ports, environment variables, or volume mounts without updating docs

## Definition of Done

A task is not complete unless all applicable items below are satisfied:

- code matches the requested behavior
- public APIs remain documented through FastAPI/OpenAPI
- types are explicit
- required comments/docstrings are present
- relevant tests are added or updated
- relevant checks have been run, or any unrun checks are explicitly reported
- `README.md` and compose-related docs are updated if runtime behavior changed
