"""
File: /async_driver.py
Created Date: Tuesday July 22nd 2025
Author: Christian Nonis <alch.infoemail@gmail.com>
-----
Last Modified: Tuesday July 22nd 2025 12:32:18 pm
Modified By: the developer formerly known as Christian Nonis at <alch.infoemail@gmail.com>
-----
"""

from typing import List, Literal, Optional

import aiohttp
from .constants.endpoints import (
    API_KEY_HEADER,
    MEMORY_CONTENT_TYPES,
    MemoryEndpoints,
    MemoryQueryResponse,
    MemoryUpdateResponse,
    InfoRetrievalResult,
)


class AsyncLumenBrainDriver:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Lumen Brain API key is required")

        self.api_key = api_key

    async def save_message(
        self,
        memory_uuid: str,
        content: str,
        role: Optional[Literal["user", "assistant"]] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> MemoryUpdateResponse:
        """
        Request body for the memory update endpoint.

        Args:
            memory_uuid: The UUID of the memory to update, you can provide yours or let the API generate one.
            content: The text content of the message to save.
            role: Literal["user", "assistant"].
            conversation_id: The optional ID of the current conversation, if not provided a new conversation will be created.
            metadata: The optional metadata to add to the memory.
        """

        task_id = None
        conversation_id = None
        memory_id = None

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url=MemoryEndpoints.UPDATE.value,
                    headers={API_KEY_HEADER: self.api_key},
                    json={
                        "memory_uuid": memory_uuid,
                        "type": "message",
                        "content": content,
                        "role": role,
                        "conversation_id": conversation_id,
                        "metadata": metadata,
                    },
                ) as response:
                    result = await response.json()
                    task_id = result.get("task_id")
                    conversation_id = result.get("conversation_id")
                    memory_id = result.get("memory_id")
            except Exception as e:
                print("[LUMEN BRAIN] Error saving message", e)
                raise e

            if not conversation_id or memory_id:
                return {
                    "error": "Failed to save message",
                    "task_id": task_id,
                }

            if result.get("error"):
                return {
                    "status": "error",
                    "error": result.get("error"),
                }
            return MemoryUpdateResponse(**result)

    async def inject_knowledge(
        self,
        memory_uuid: str,
        content: str,
        resource_type: Optional[MEMORY_CONTENT_TYPES] = None,
        metadata: Optional[dict] = None,
    ) -> MemoryUpdateResponse:
        """
        Request body for the memory update endpoint.

        Args:
            memory_uuid: The UUID of the memory to update, you can provide yours or let the API generate one.
            content: The text content of the message to save.
            resource_type: Literal["file", "event", "webpage", "email"].
            metadata: The optional metadata to add to the memory.
        """
        task_id = None
        conversation_id = None
        memory_id = None

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url=MemoryEndpoints.UPDATE.value,
                    headers={API_KEY_HEADER: self.api_key},
                    json={
                        "memory_uuid": memory_uuid,
                        "type": resource_type,
                        "content": content,
                        "resource_type": resource_type,
                        "metadata": metadata,
                    },
                ) as response:
                    result = await response.json()
                    task_id = result.get("task_id")
                    memory_id = result.get("memory_id")
                    conversation_id = result.get("conversation_id")
            except Exception as e:
                print("[LUMEN BRAIN] Error injecting knowledge", e)
                raise e

            if not conversation_id or memory_id:
                return {
                    "error": "Failed to inject knowledge",
                    "task_id": task_id,
                }

            if result.get("error"):
                return {
                    "status": "error",
                    "error": result.get("error"),
                }
            return MemoryUpdateResponse(**result)

    async def query_memory(
        self, text: str, memory_uuid: str, conversation_id: str
    ) -> MemoryQueryResponse:
        """
        Request body for the memory query endpoint.

        Args:
            text: The text to query the memory with (usually the same message as the one that was sent to the agent).
            memory_uuid: The UUID of the memory to query (usually it's related to a user).
            conversation_id: The optional ID of the current conversation, if not provided a new conversation will be created.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=MemoryEndpoints.QUERY.value,
                headers={API_KEY_HEADER: self.api_key},
                json={
                    "text": text,
                    "memory_uuid": memory_uuid,
                    "conversation_id": conversation_id,
                },
            ) as response:
                result = await response.json()
                try:
                    if result.get("error"):
                        return {
                            "status": "error",
                            "error": result.get("error"),
                        }
                    return MemoryQueryResponse(**result)
                except Exception as e:
                    print("[LUMEN BRAIN] Error querying memory", e)
                    raise e

    async def fetch_info(
        self, memory_uuid: str, entities: List[str], info: str, depth: int = 2
    ) -> InfoRetrievalResult:
        """
        Fetch information and relationships about entities in the memory

        Args:
            memory_uuid: The UUID of the memory to query (usually it's related to a user).
            entities: The entities that are related to the information to be retrieved.
            info: The information to be retrieved.
            depth: The higher relation depth that will be looked for.
        """
        if not memory_uuid:
            raise ValueError("Memory UUID is required")
        if not entities:
            raise ValueError("Entities are required and must be a list of strings")
        if not info:
            raise ValueError("Info is required and must be a string")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=MemoryEndpoints.QUERY_ENTITIES.value,
                headers={API_KEY_HEADER: self.api_key},
                params={
                    "memory_uuid": memory_uuid,
                    "entities": entities,
                    "info": info,
                    "depth": depth,
                },
            ) as response:
                result = await response.json()
                try:
                    if result.get("error"):
                        return {
                            "status": "error",
                            "error": result.get("error"),
                        }
                    return InfoRetrievalResult(**result)
                except Exception as e:
                    print("[LUMEN BRAIN] Error fetching info", e)
                    raise e
