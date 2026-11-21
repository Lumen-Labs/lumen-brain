# Changelog

## 0.4.0

Rewrite of the Python SDK for BrainAPI v2.

- Auth is a BrainPAT via `Authorization: Bearer <pat>` (default) or the `BrainPAT` header (`auth_scheme="brainpat"`), plus `X-Brain-ID`.
- Regional hosts use `https://system.<region>.brainapi.lumen-labs.ai` (`europe-central2`, `us-east1`). The v1 host `api.brainapi.lumen-labs.ai` is no longer used.
- New methods cover ingest, retrieve/search/context (`as_of` / validity), facts/verification, conflicts, graph/entity, tasks, and system brains.
- Sync (`LumenBrain`) and async (`AsyncLumenBrain`) clients share the same API. `LumenBrainDriver` remains as an alias.
- v1 `save_message` / `inject_knowledge` / `query_memory` / `fetch_info` remain as compatibility wrappers around v2 ingest/context/entity-info.
- Runtime dependencies are `httpx` and `pydantic` v2. `requests`, `aiohttp`, `python-dotenv`, and `build` are no longer required to use the package.

This version is not published to PyPI from this change. Publishing requires the owner's PyPI credentials.

## 0.3.3

Released on PyPI on 2025-10-11. Git `main` still listed `0.3.2`; the published sdist/wheel matches commit `d5e8cc6` (`fix(inject): handled injection error`) except for `version = "0.3.3"` in `pyproject.toml`. No other code differences.

## 0.3.2

Last version recorded on git `main` before the v2 rewrite.
