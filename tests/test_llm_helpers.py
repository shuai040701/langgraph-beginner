import os

from graph_app.llm import (
    build_messages,
    choose_forced_tool,
    langsmith_tracing_enabled,
    parse_message_tool_calls,
    stream_chat_completion,
)


def test_choose_forced_tool_uses_text_stats_first():
    user_input = '请先统计文本 "LangGraph makes agent workflows explicit" 的字符数'
    result = choose_forced_tool(user_input, build_messages(user_input, []))

    assert result is not None
    assert result["route"] == "tool"
    assert result["tool_name"] == "text_stats"
    assert result["tool_args"]["text"] == "LangGraph makes agent workflows explicit"


def test_choose_forced_tool_skips_after_text_stats_was_requested():
    user_input = '请先统计文本 "abc" 的字符数'
    messages = build_messages(user_input, [])
    messages.append(
        {
            "role": "assistant",
            "tool_calls": [
                {"function": {"name": "text_stats", "arguments": '{"text": "abc"}'}}
            ],
        }
    )

    assert choose_forced_tool(user_input, messages) is None


def test_langsmith_tracing_enabled_reads_boolean_env(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    assert langsmith_tracing_enabled() is True

    monkeypatch.setenv("LANGSMITH_TRACING", "off")
    assert langsmith_tracing_enabled() is False


def test_parse_message_tool_calls_from_dicts():
    result = parse_message_tool_calls(
        [
            {
                "id": "call_1",
                "function": {
                    "name": "calculator",
                    "arguments": '{"expression": "2 + 3"}',
                },
            }
        ]
    )

    assert result == [
        {"id": "call_1", "name": "calculator", "args": {"expression": "2 + 3"}}
    ]


class Delta:
    def __init__(self, content=None, reasoning_content=None, tool_calls=None):
        self.content = content
        self.reasoning_content = reasoning_content
        self.tool_calls = tool_calls or []


class Choice:
    def __init__(self, delta):
        self.delta = delta


class Chunk:
    def __init__(self, delta):
        self.choices = [Choice(delta)]


class FunctionDelta:
    def __init__(self, name=None, arguments=None):
        self.name = name
        self.arguments = arguments


class ToolCallDelta:
    def __init__(self, index, id=None, function=None):
        self.index = index
        self.id = id
        self.function = function


class FakeCompletions:
    def __init__(self, chunks):
        self.chunks = chunks

    def create(self, **kwargs):
        return iter(self.chunks)


class FakeChat:
    def __init__(self, chunks):
        self.completions = FakeCompletions(chunks)


class FakeClient:
    def __init__(self, chunks):
        self.chat = FakeChat(chunks)


def test_stream_chat_completion_collects_content(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_MODEL", "fake-model")
    client = FakeClient(
        [
            Chunk(Delta(reasoning_content="thinking")),
            Chunk(Delta(content="hello ")),
            Chunk(Delta(content="world")),
        ]
    )

    message = stream_chat_completion(client, [])

    assert message["content"] == "hello world"
    assert message["reasoning_content"] == "thinking"
    assert message["_streamed_content"] is True


def test_stream_chat_completion_collects_tool_call_chunks(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_MODEL", "fake-model")
    client = FakeClient(
        [
            Chunk(
                Delta(
                    tool_calls=[
                        ToolCallDelta(
                            0,
                            id="call_1",
                            function=FunctionDelta(
                                name="calculator",
                                arguments='{"expression":',
                            ),
                        )
                    ]
                )
            ),
            Chunk(
                Delta(
                    tool_calls=[
                        ToolCallDelta(
                            0,
                            function=FunctionDelta(arguments='"2 + 3"}'),
                        )
                    ]
                )
            ),
        ]
    )

    message = stream_chat_completion(client, [])

    assert parse_message_tool_calls(message["tool_calls"]) == [
        {"id": "call_1", "name": "calculator", "args": {"expression": "2 + 3"}}
    ]
