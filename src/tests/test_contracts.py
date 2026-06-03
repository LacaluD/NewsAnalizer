from src.contracts import PipelineResult


def test_pipeline_result_ok_success_case() -> None:
    result = PipelineResult.ok(text="summary", tag="#BTC")
    assert result == PipelineResult(
        success=True, text="summary", tag="#BTC", error=None
    )


def test_pipeline_result_ok_without_tag_edge_case() -> None:
    result = PipelineResult.ok(text="summary")
    assert result.tag is None


def test_pipeline_result_ok_empty_text_edge_case() -> None:
    result = PipelineResult.ok(text="")
    assert result.text == ""


def test_pipeline_result_fail_failure_case() -> None:
    result = PipelineResult.fail("network error")
    assert result == PipelineResult(
        success=False, text=None, tag=None, error="network error"
    )


def test_pipeline_result_fail_empty_message_edge_case() -> None:
    result = PipelineResult.fail("")
    assert result.error == ""


def test_pipeline_result_fail_has_no_payload_failure_case() -> None:
    result = PipelineResult.fail("bad")
    assert result.text is None and result.tag is None
