"""
File: /async_driver.py
Created Date: Tuesday July 22nd 2025
Author: Christian Nonis <alch.infoemail@gmail.com>
-----
Last Modified: Tuesday July 22nd 2025 12:32:18 pm
Modified By: the developer formerly known as Christian Nonis at <alch.infoemail@gmail.com>
-----
"""

import asyncio
from typing import Literal, Optional

import aiohttp
from .constants.endpoints import (
    API_KEY_HEADER,
    MEMORY_CONTENT_TYPES,
    MemoryEndpoints,
    MemoryQueryResponse,
    MemoryUpdateResponse,
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

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url=MemoryEndpoints.UPDATE.value,
                    headers={API_KEY_HEADER: self.api_key},
                    json={
                        "memory_id": memory_uuid,
                        "type": "message",
                        "content": content,
                        "role": role,
                        "conversation_id": conversation_id,
                        "metadata": metadata,
                    },
                ) as response:
                    result = await response.json()
                    task_id = result.get("task_id")
            except Exception as e:
                print("[LUMEN BRAIN] Error saving message", e)
                raise e

            result = None

            while not result:
                try:
                    async with session.get(
                        url=f"{MemoryEndpoints.TASKS.value}/{task_id}",
                        headers={API_KEY_HEADER: self.api_key},
                    ) as result_res:
                        if result_res.status == 200:
                            result = await result_res.json()
                            break
                except Exception as e:
                    print("[LUMEN BRAIN] Error polling task", e)
                    raise e
                await asyncio.sleep(1)

            return result

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

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url=MemoryEndpoints.UPDATE.value,
                    headers={API_KEY_HEADER: self.api_key},
                    json={
                        "memory_id": memory_uuid,
                        "type": resource_type,
                        "content": content,
                        "resource_type": resource_type,
                        "metadata": metadata,
                    },
                ) as response:
                    result = await response.json()
                    task_id = result.get("task_id")
            except Exception as e:
                print("[LUMEN BRAIN] Error injecting knowledge", e)
                raise e

            result = None

            while not result:
                try:
                    async with session.get(
                        url=f"{MemoryEndpoints.TASKS.value}/{task_id}",
                        headers={API_KEY_HEADER: self.api_key},
                    ) as result_res:
                        if result_res.status == 200:
                            result = await result_res.json()
                            break
                except Exception as e:
                    print("[LUMEN BRAIN] Error polling knowledge injection task", e)
                    raise e
                await asyncio.sleep(1)

            return result

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
                    "memory_id": memory_uuid,
                    "conversation_id": conversation_id,
                },
            ) as response:
                result = await response.json()
                return result
