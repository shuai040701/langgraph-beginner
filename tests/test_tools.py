from graph_app.tools import run_tool, safe_calculate, text_stats


def test_safe_calculate_supports_basic_arithmetic():
    assert safe_calculate("1 + 2 * (3 + 4)") == 15


def test_safe_calculate_rejects_function_calls():
    try:
        safe_calculate("__import__('os').system('echo bad')")
    except ValueError as exc:
        assert "Only simple arithmetic" in str(exc)
    else:
        raise AssertionError("unsafe expression should fail")


def test_text_stats_counts_text_shape():
    result = text_stats("hello world\nhi")

    assert "14" in result
    assert "12" in result
    assert "3" in result
    assert "2" in result


def test_run_tool_dispatches_tools():
    assert run_tool("calculator", {"expression": "2 ** 5"}) == "32"
    assert "Asia/Shanghai" in run_tool("current_time", {"timezone": "Asia/Shanghai"})
