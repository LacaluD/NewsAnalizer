import asyncio

from src.session_manager import SessionManager


class DummySession:
    def __init__(self, closed: bool = False):
        self.closed = closed
        self.close_calls = 0

    async def close(self):
        self.close_calls += 1
        self.closed = True


def test_get_creates_session_success_case(mocker) -> None:
    manager = SessionManager()
    fake = DummySession(closed=False)
    ctor = mocker.patch("src.session_manager.aiohttp.ClientSession", return_value=fake)

    session = manager.get()

    assert session is fake and ctor.call_count == 1


def test_get_reuses_open_session_edge_case(mocker) -> None:
    manager = SessionManager()
    fake = DummySession(closed=False)
    mocker.patch("src.session_manager.aiohttp.ClientSession", return_value=fake)

    first = manager.get()
    second = manager.get()

    assert first is second


def test_get_recreates_closed_session_failure_case(mocker) -> None:
    manager = SessionManager()
    first = DummySession(closed=True)
    second = DummySession(closed=False)
    mocker.patch(
        "src.session_manager.aiohttp.ClientSession", side_effect=[first, second]
    )

    created_first = manager.get()
    created_second = manager.get()

    assert created_first is first and created_second is second


def test_close_closes_open_session_success_case() -> None:
    manager = SessionManager()
    manager._session = DummySession(closed=False)

    asyncio.run(manager.close())

    assert manager._session.close_calls == 1


def test_close_skips_when_session_missing_edge_case() -> None:
    manager = SessionManager()
    asyncio.run(manager.close())
    assert manager._session is None


def test_close_skips_when_already_closed_failure_case() -> None:
    manager = SessionManager()
    manager._session = DummySession(closed=True)

    asyncio.run(manager.close())

    assert manager._session.close_calls == 0
