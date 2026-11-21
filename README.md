# Lumen Brain Python SDK

Python client for [BrainAPI v2](https://github.com/Lumen-Labs/brainapi2).

```bash
pip install lumen-brain
```

Requires Python 3.9+.

## Authentication

Every request except a few system/health calls needs a BrainAPI personal access token (PAT). Pass it as `pat=` or set `BRAINPAT_TOKEN` (also accepted: `LUMEN_BRAIN_PAT`, `LUMEN_BRAIN_API_KEY`).

By default the SDK sends `Authorization: Bearer <pat>`. To send the OpenAPI `BrainPAT` header instead:

```python
from lumen_brain import LumenBrain

brain = LumenBrain(pat="your-pat", brain_id="my-brain", auth_scheme="brainpat")
```

Identify the brain with `X-Brain-ID`. Set a client default (`brain_id=` or `LUMEN_BRAIN_ID`) and override it per call.

## Regional hosts

Managed BrainAPI is served at:

```text
https://system.<region>.brainapi.lumen-labs.ai
```

Known regions: `europe-central2` (default), `us-east1`.

```python
from lumen_brain import LumenBrain, regional_base_url

brain = LumenBrain(pat="your-pat", brain_id="my-brain", region="us-east1")
# or an explicit host
brain = LumenBrain(
    pat="your-pat",
    brain_id="my-brain",
    base_url="https://system.europe-central2.brainapi.lumen-labs.ai",
)
assert regional_base_url("europe-central2").endswith("europe-central2.brainapi.lumen-labs.ai")
```

Pass either `region` or `base_url`, not both. Environment: `LUMEN_BRAIN_REGION` / `LUMEN_BRAIN_BASE_URL`.

## Usage

Ingest is asynchronous on the server: `ingest` / `save` return a `task_id` (HTTP 202). Use `wait_for_task` when you need the job to finish. Chat and query both map to `POST /retrieve/context`.

```python
from lumen_brain import LumenBrain

with LumenBrain(pat="your-pat", brain_id="my-brain", region="europe-central2") as brain:
    accepted = brain.ingest(text="Ada joined the design team in Berlin in 2024.")
    brain.wait_for_task(accepted.task_id)

    ctx = brain.context(
        "Who is on the design team?",
        as_of="2025-06-01T00:00:00Z",
        include_validity_unknown=True,
    )
    print(ctx.text_context)

    hits = brain.search("design team Berlin", as_of="2025-06-01T00:00:00Z")
    facts = brain.list_facts(state="unverified")
    if facts.facts:
        brain.verify_fact(facts.facts[0].fact_id, note="checked against source")

    conflicts = brain.list_conflicts(status="open")
    entities = brain.list_entities(query_text="Ada")
```

Async client:

```python
from lumen_brain import AsyncLumenBrain

async with AsyncLumenBrain(pat="your-pat", brain_id="my-brain") as brain:
    ctx = await brain.query("Who is on the design team?")
    print(ctx.text_context)
```

### Compatibility aliases

`LumenBrainDriver` / `AsyncLumenBrainDriver` still exist. `save_message` and `inject_knowledge` ingest text and, by default, poll the task. `query_memory` calls `context`. `fetch_info` calls `entity_info`. Prefer the v2 names in new code.

## Errors

Failed responses raise `BrainAPIError` with `status_code`, `code`, `detail`, `resolution`, and `request_id` when the server returns the v2 error envelope.

## License

MIT
