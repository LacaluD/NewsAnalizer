import asyncio
import json

import aiohttp

from src.ai_core import AIAnalyze
from src.contracts import PipelineResult


class AsyncJsonResponseCtx:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self.payload


class DummySession:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error

    def post(self, *_args, **_kwargs):
        if self.error:
            raise self.error
        return self.response


def test_extract_and_validate_tag_success_case() -> None:
    analyzer = AIAnalyze()
    text, tag = analyzer.extract_and_validate_tag("Body text\n#Bitcoin")
    assert text == "Body text" and tag == "#Bitcoin"


def test_extract_and_validate_tag_failure_case_no_tag() -> None:
    analyzer = AIAnalyze()
    text, tag = analyzer.extract_and_validate_tag("Body text only")
    assert text == "Body text only" and tag is None


def test_extract_and_validate_tag_edge_case_spaces() -> None:
    analyzer = AIAnalyze()
    text, tag = analyzer.extract_and_validate_tag("Body\n#ETH   ")
    assert text == "Body" and tag == "#ETH"


def test_call_llm_success_case(mocker) -> None:
    analyzer = AIAnalyze()
    payload = {"model": "m", "choices": [{"message": {"content": "ok #BTC"}}]}
    session = DummySession(response=AsyncJsonResponseCtx(payload))
    mocker.patch.object(
        AIAnalyze, "session", new_callable=mocker.PropertyMock, return_value=session
    )

    result = asyncio.run(analyzer._call_llm("p:", "c"))

    assert result.success is True and result.text == "ok" and result.tag == "#BTC"


def test_call_llm_failure_case_bad_payload(mocker) -> None:
    analyzer = AIAnalyze()
    payload = {"model": "m", "not_choices": []}
    session = DummySession(response=AsyncJsonResponseCtx(payload))
    mocker.patch.object(
        AIAnalyze, "session", new_callable=mocker.PropertyMock, return_value=session
    )

    result = asyncio.run(analyzer._call_llm("p:", "c"))

    assert result.success is False


def test_call_llm_failure_case_network_error(mocker) -> None:
    analyzer = AIAnalyze()
    session = DummySession(error=aiohttp.ClientError("boom"))
    mocker.patch.object(
        AIAnalyze, "session", new_callable=mocker.PropertyMock, return_value=session
    )

    result = asyncio.run(analyzer._call_llm("p:", "c"))

    assert result.error == "AI request failed due to network or response format error."


def test_extract_facts_success_case_json(mocker) -> None:
    analyzer = AIAnalyze()
    mocker.patch.object(
        analyzer, "_call_llm", return_value=PipelineResult.ok('{"k": 1}', "#K")
    )

    result = asyncio.run(analyzer.extract_facts("article"))

    assert (
        result.success is True
        and json.loads(result.text) == {"k": 1}
        and result.tag == "#K"
    )


def test_extract_facts_failure_case_upstream_error(mocker) -> None:
    analyzer = AIAnalyze()
    mocker.patch.object(
        analyzer, "_call_llm", return_value=PipelineResult.fail("failed")
    )

    result = asyncio.run(analyzer.extract_facts("article"))

    assert result.success is False


def test_extract_facts_edge_case_non_json(mocker) -> None:
    analyzer = AIAnalyze()
    mocker.patch.object(
        analyzer, "_call_llm", return_value=PipelineResult.ok("plain facts", "#TAG")
    )

    result = asyncio.run(analyzer.extract_facts("article"))

    assert (
        result.success is True and result.text == "plain facts" and result.tag == "#TAG"
    )


def test_send_for_ai_analyze_failure_case_empty_text() -> None:
    analyzer = AIAnalyze()
    result = asyncio.run(analyzer.send_for_ai_analyze("   "))
    assert result.success is False


def test_send_for_ai_analyze_failure_case_short_article() -> None:
    analyzer = AIAnalyze()
    result = asyncio.run(analyzer.send_for_ai_analyze("word " * 50))
    assert result.error == "Article too short for meaningful analysis."


def test_send_for_ai_analyze_failure_case_opinion_category() -> None:
    analyzer = AIAnalyze()
    result = asyncio.run(
        analyzer.send_for_ai_analyze("word " * 110, category="opinion")
    )
    assert result.success is False


def test_send_for_ai_analyze_failure_case_extract_step(mocker) -> None:
    analyzer = AIAnalyze()
    mocker.patch.object(
        analyzer, "extract_facts", return_value=PipelineResult.fail("x")
    )

    result = asyncio.run(analyzer.send_for_ai_analyze("word " * 110, category="news"))

    assert result.error == "AI extraction step failed. Please retry later."


def test_send_for_ai_analyze_failure_case_analyze_step(mocker) -> None:
    analyzer = AIAnalyze()
    mocker.patch.object(
        analyzer, "extract_facts", return_value=PipelineResult.ok("facts", "#EX")
    )
    mocker.patch.object(analyzer, "_call_llm", return_value=PipelineResult.fail("x"))

    result = asyncio.run(analyzer.send_for_ai_analyze("word " * 110, category="news"))

    assert result.error == "AI analysis step failed. Please retry later."


def test_send_for_ai_analyze_success_case(mocker) -> None:
    analyzer = AIAnalyze()
    mocker.patch.object(
        analyzer, "extract_facts", return_value=PipelineResult.ok("facts", "#EX")
    )
    mocker.patch.object(
        analyzer, "_call_llm", return_value=PipelineResult.ok("final", "#AN")
    )

    result = asyncio.run(analyzer.send_for_ai_analyze("word " * 110, category="news"))

    assert result.success is True and result.text == "final" and result.tag == "#AN"


def test_send_for_ai_analyze_edge_case_fallback_to_extract_tag(mocker) -> None:
    analyzer = AIAnalyze()
    mocker.patch.object(
        analyzer, "extract_facts", return_value=PipelineResult.ok("facts", "#EX")
    )
    mocker.patch.object(
        analyzer, "_call_llm", return_value=PipelineResult.ok("final", None)
    )

    result = asyncio.run(analyzer.send_for_ai_analyze("word " * 110, category="news"))

    assert result.tag == "#EX"


def test_send_for_ai_analize_alias_success_case(mocker) -> None:
    analyzer = AIAnalyze()
    mocked = mocker.patch.object(
        analyzer, "send_for_ai_analyze", return_value=PipelineResult.ok("final", "#T")
    )

    result = asyncio.run(analyzer.send_for_ai_analize("word " * 110, category="news"))

    assert result.success is True and mocked.call_count == 1


def test_send_for_ai_analize_alias_failure_case(mocker) -> None:
    analyzer = AIAnalyze()
    mocker.patch.object(
        analyzer, "send_for_ai_analyze", return_value=PipelineResult.fail("bad")
    )

    result = asyncio.run(analyzer.send_for_ai_analize("word " * 110, category="news"))

    assert result.success is False and result.error == "bad"


def test_send_for_ai_analize_alias_edge_case_none_text(mocker) -> None:
    analyzer = AIAnalyze()
    mocked = mocker.patch.object(
        analyzer, "send_for_ai_analyze", return_value=PipelineResult.fail("empty")
    )

    result = asyncio.run(analyzer.send_for_ai_analize(None, category=None))

    assert result.error == "empty" and mocked.call_args.kwargs == {
        "article_text": None,
        "category": None,
    }
