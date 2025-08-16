# Lumen Brain Python Client

A Python client library for interacting with the Lumen Brain API.
GitHub: https://github.com/Lumen-Labs/lumen-brain

## Features

On-demand memory/context driver to interact with the Lumen Brain API and improve the context and responses of LLMs without finetuning.

## Installation

```bash
pip install lumen-brain
```

## Usage

### Async Client

```python
from lumen_brain import AsyncLumenBrainDriver

# Initialize the client
client = AsyncLumenBrainDriver(api_key="your-api-key")

# Save a message
await client.save_message(
    memory_uuid="your-memory-uuid", # the unique identifier provided by your app, if not provided, a new memory will be created
    type="message",
    content="Your message content",
    role="user",

    # Optional Fields
    conversation_id="your-conversation-id", # If not provided, a new conversation will be created
    metadata={"key": "value"}
)

# Query memory
# The result will be a MemoryUpdateResponse object with a context field
# the context field can be appended to the message that will be sent to the agent to improve the agent's response
# allowing the agent to have a more accurate and relevant context around the user's message
result = await client.query_memory(
    text="Your query",
    memory_uuid="your-memory-uuid", # the unique identifier provided by your app, if not provided, a new memory will be created
    conversation_id="your-conversation-id"
)

# Inject knowledge
# additional knowledge can be injected into the memory, for example if you are synking the user's emails, files etc.
# works also if you want the agent to answer better arount a specific topic like documents etc.

await client.inject_knowledge(
    memory_uuid="your-memory-uuid", # the unique identifier provided by your app, if not provided, a new memory will be created
    type="message",
    content="Your message content",
    resource_type="file",

    # Optional Fields
    metadata={"key": "value"}
)
```

### Sync Client

```python
from lumen_brain import LumenBrainDriver

# Initialize the client
client = LumenBrainDriver(api_key="your-api-key")

# Save a message
client.save_message(
    memory_uuid="your-memory-uuid",
    type="message",
    content="Your message content",
    role="user"
)

# Query memory
result = client.query_memory(
    text="Your query",
    memory_uuid="your-memory-uuid",
    conversation_id="your-conversation-id"
)
```

### Fetch info

```python

result = client.fetch_info(
    memory_uuid="your-memory-uuid", # the unique identifier provided by your app, if not provided, a new memory will be created
    entities=["john"], # the entities that are related to the information to be retrieved
    info="wedding date", # the information to be retrieved
    depth=2 # the higher relation depth that will be looked for
)
result.nodes # the nodes that are related to the information to be retrieved
result.most_relevant_relation # the most relevant relation between the entities and the information to be retrieved
result.most_relevant_confidence # the confidence of the most relevant relation (0-1)
```

## License

This project is licensed under the MIT License.
