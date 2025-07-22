"""
File: /sync_driver.py
Created Date: Tuesday July 22nd 2025
Author: Christian Nonis <alch.infoemail@gmail.com>
-----
Last Modified: Tuesday July 22nd 2025 12:32:11 pm
Modified By: the developer formerly known as Christian Nonis at <alch.infoemail@gmail.com>
-----
"""

import time
from typing import Literal, Optional

import requests
from .constants.endpoints import (
    ALL_MEMORY_CONTENT_TYPES,
    API_KEY_HEADER,
    MEMORY_CONTENT_TYPES,
    MemoryEndpoints,
    MemoryQueryResponse,
    MemoryUpdateResponse,
)


class LumenBrainDriver:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Lumen Brain API key is required")

        self.api_key = api_key

    def save_message(
        self,
        memory_uuid: str,
        type: ALL_MEMORY_CONTENT_TYPES,
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

        try:
            response = requests.post(
                url=MemoryEndpoints.UPDATE.value,
                headers={API_KEY_HEADER: self.api_key},
                json={
                    "memory_id": memory_uuid,
                    "type": type,
                    "content": content,
                    "role": role,
                    "conversation_id": conversation_id,
                    "metadata": metadata,
                },
            )
            result = response.json()
            task_id = result.get("task_id")
        except Exception as e:
            print("[LUMEN BRAIN] Error saving message", e)
            raise e

        result = None

        while not result:
            try:
                result_res = requests.get(
                    url=f"{MemoryEndpoints.TASKS.value}/{task_id}",
                    headers={API_KEY_HEADER: self.api_key},
                )
                if result_res.status_code == 200:
                    result = result_res.json()
                    break
            except Exception as e:
                print("[LUMEN BRAIN] Error polling task", e)
                raise e
            time.sleep(1)

        return result

    def inject_knowledge(
        self,
        memory_uuid: str,
        type: ALL_MEMORY_CONTENT_TYPES,
        content: str,
        resource_type: Optional[MEMORY_CONTENT_TYPES] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> MemoryUpdateResponse:
        """
        Request body for the memory update endpoint.

        Args:
            memory_uuid: The UUID of the memory to update, you can provide yours or let the API generate one.
            content: The text content of the message to save.
            resource_type: Literal["file", "event", "webpage", "email"].
            conversation_id: The optional ID of the current conversation, if not provided a new conversation will be created.
            metadata: The optional metadata to add to the memory.
        """
        task_id = None

        try:
            response = requests.post(
                url=MemoryEndpoints.UPDATE.value,
                headers={API_KEY_HEADER: self.api_key},
                json={
                    "memory_id": memory_uuid,
                    "type": type,
                    "content": content,
                    "resource_type": resource_type,
                    "conversation_id": conversation_id,
                    "metadata": metadata,
                },
            )
            result = response.json()
            task_id = result.get("task_id")
        except Exception as e:
            print("[LUMEN BRAIN] Error injecting knowledge", e)
            raise e

        result = None

        while not result:
            try:
                result_res = requests.get(
                    url=f"{MemoryEndpoints.TASKS.value}/{task_id}",
                    headers={API_KEY_HEADER: self.api_key},
                )
                if result_res.status_code == 200:
                    result = result_res.json()
                    break
            except Exception as e:
                print("[LUMEN BRAIN] Error polling knowledge injection task", e)
                raise e
            time.sleep(1)

        return result

    def query_memory(
        self, text: str, memory_uuid: str, conversation_id: str
    ) -> MemoryQueryResponse:
        """
        Request body for the memory query endpoint.

        Args:
            text: The text to query the memory with (usually the same message as the one that was sent to the agent).
            memory_uuid: The UUID of the memory to query (usually it's related to a user).
            conversation_id: The optional ID of the current conversation, if not provided a new conversation will be created.
        """
        response = requests.post(
            url=MemoryEndpoints.QUERY.value,
            headers={API_KEY_HEADER: self.api_key},
            json={
                "text": text,
                "memory_id": memory_uuid,
                "conversation_id": conversation_id,
            },
        )
        result = response.json()
        return result


if __name__ == "__main__":
    client = LumenBrainDriver(api_key="your-api-key")
    client.save_message(
        memory_uuid="your-memory-uuid",
        type="message",
        content="Your message content",
        role="user",
    )
