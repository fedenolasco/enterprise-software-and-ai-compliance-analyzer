"""WebSocket handler for live workflow node transitions."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/workflow/{thread_id}")
async def workflow_websocket(websocket: WebSocket, thread_id: str) -> None:
    """WebSocket endpoint for live workflow execution updates.

    Sends node transition events as the workflow progresses.
    """
    await websocket.accept()
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "thread_id": thread_id,
            "message": f"WebSocket connected for workflow thread {thread_id}",
        })

        # Keep connection alive and listen for messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "thread_id": thread_id})
                elif message.get("type") == "get_state":
                    # Return current workflow state if available
                    from ui_api.routers.workflow import _workflow_states

                    state = _workflow_states.get(thread_id)
                    if state:
                        await websocket.send_json({
                            "type": "state",
                            "thread_id": thread_id,
                            "state": state,
                            "workflow_status": state.get("workflow_status", "UNKNOWN"),
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "thread_id": thread_id,
                            "message": f"Workflow thread not found: {thread_id}",
                        })
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_json({"type": "keepalive", "thread_id": thread_id})

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
