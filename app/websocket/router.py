import uuid

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.dependencies import async_session_factory
from app.repositories import portfolio_repo
from app.websocket.manager import manager

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.websocket("/ws/portfolios/{portfolio_id}")
async def websocket_endpoint(websocket: WebSocket, portfolio_id: uuid.UUID):
    # JWT comes in as a query parameter: /ws/portfolios/{id}?token=...
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    user_id = decode_access_token(token)
    if not user_id:
        await websocket.close(code=4001)
        return

    # Verify the portfolio exists and belongs to this user
    async with async_session_factory() as session:
        portfolio = await portfolio_repo.get_by_id(session, portfolio_id)

    if not portfolio or str(portfolio.user_id) != user_id:
        await websocket.close(code=4003)
        return

    await manager.connect(websocket, portfolio_id)

    try:
        while True:
            # Keep the connection alive — we don't expect messages from the client
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, portfolio_id)
