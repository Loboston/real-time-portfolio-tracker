import uuid

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """
    Tracks active WebSocket connections per portfolio.
    Maps portfolio_id → set of connected WebSockets.
    """

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, portfolio_id: uuid.UUID) -> None:
        await websocket.accept()
        if portfolio_id not in self._connections:
            self._connections[portfolio_id] = set()
        self._connections[portfolio_id].add(websocket)
        logger.info("websocket connected", portfolio_id=str(portfolio_id))

    def disconnect(self, websocket: WebSocket, portfolio_id: uuid.UUID) -> None:
        if portfolio_id in self._connections:
            self._connections[portfolio_id].discard(websocket)
            if not self._connections[portfolio_id]:
                del self._connections[portfolio_id]
        logger.info("websocket disconnected", portfolio_id=str(portfolio_id))

    async def broadcast_to_portfolio(self, portfolio_id: uuid.UUID, message: dict) -> None:
        connections = self._connections.get(portfolio_id, set())
        if not connections:
            return

        dead = set()
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead.add(websocket)

        # Prune dead connections
        for websocket in dead:
            self.disconnect(websocket, portfolio_id)

    def get_subscribed_portfolio_ids(self) -> set[uuid.UUID]:
        return set(self._connections.keys())


# Single shared instance used across the app
manager = ConnectionManager()
