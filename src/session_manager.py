"""Shared aiohttp client session manager."""

import aiohttp


class SessionManager:
    """Create and reuse a single aiohttp ClientSession."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    def get(self) -> aiohttp.ClientSession:
        """Return an open session, creating one when needed."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the shared session when it is still open."""
        if self._session and not self._session.closed:
            await self._session.close()


session_manager = SessionManager()
