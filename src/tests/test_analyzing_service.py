import asyncio

from src.bot.analyzing_service import AnalyzingTGService
from src.contracts import PipelineResult


class DummyParser:
    def __init__(self, result):
        self.result = result

    async def extract_text(self, _url: str):
        return self.result


class DummyAI:
    def __init__(self, result: PipelineResult):
        self.result = result

    async def send_for_ai_analyze(self, article_data: str, category: str = ""):
        return self.result


def test_init_success_case_with_explicit_ai() -> None:
    service = AnalyzingTGService(
        news_parser=DummyParser("text"), ai_analyzer=DummyAI(PipelineResult.ok("ok"))
    )
    assert service.ai_analyzer is not None


def test_init_success_case_without_ai_dependency_uses_default() -> None:
    service = AnalyzingTGService(news_parser=DummyParser("text"), ai_analyzer=None)
    assert service.ai_analyzer is not None


def test_init_edge_case_preserves_parser() -> None:
    parser = DummyParser("body")
    service = AnalyzingTGService(
        news_parser=parser, ai_analyzer=DummyAI(PipelineResult.ok("ok"))
    )
    assert service.news_parser is parser


def test_init_failure_case_value_error_when_default_factory_returns_none(
    mocker,
) -> None:
    mocker.patch("src.bot.analyzing_service.AIAnalyze", return_value=None, create=True)

    try:
        _ = AnalyzingTGService(news_parser=DummyParser("body"), ai_analyzer=None)
    except ValueError as exc:
        assert "AI analyzer instance must be provided" in str(exc)
    else:
        raise AssertionError("Expected ValueError when AIAnalyze() resolves to None")


def test_parse_news_success_case() -> None:
    service = AnalyzingTGService(
        news_parser=DummyParser("article"),
        ai_analyzer=DummyAI(PipelineResult.ok("done", "#T")),
    )
    result = asyncio.run(service.parse_news("https://x"))
    assert result.success is True and result.tag == "#T"


def test_parse_news_failure_case_when_parser_returns_none() -> None:
    service = AnalyzingTGService(
        news_parser=DummyParser(None), ai_analyzer=DummyAI(PipelineResult.ok("done"))
    )
    result = asyncio.run(service.parse_news("https://x"))
    assert result.success is False


def test_parse_news_edge_case_empty_url_is_forwarded() -> None:
    service = AnalyzingTGService(
        news_parser=DummyParser("article"),
        ai_analyzer=DummyAI(PipelineResult.ok("done")),
    )
    result = asyncio.run(service.parse_news(""))
    assert result.success is True
