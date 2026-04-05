from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hermes_a2a.executor import HermesAgentExecutor
from hermes_a2a.hermes_client import HermesClient


def _make_context(task_id="task-1", context_id="ctx-1", message_text="Hello"):
    from a2a.types import Message, Part, TextPart, Role

    message = Message(
        role=Role.user,
        parts=[Part(root=TextPart(kind="text", text=message_text))],
        messageId="msg-1",
    )
    context = MagicMock()
    context.task_id = task_id
    context.context_id = context_id
    context.message = message
    return context


async def _noop_stream():
    """Empty async generator simulating no stream chunks."""
    return
    yield  # make it a generator


async def _hello_stream():
    for word in ["Hello", " world"]:
        yield word


@pytest.fixture
def mock_client():
    client = MagicMock(spec=HermesClient)
    return client


@pytest.fixture
def executor(mock_client):
    return HermesAgentExecutor(mock_client)


async def test_execute_streams_response(executor, mock_client):
    mock_client.stream = MagicMock(return_value=_hello_stream())

    event_queue = AsyncMock()
    context = _make_context()

    with patch("hermes_a2a.executor.TaskUpdater") as MockUpdater:
        updater_instance = AsyncMock()
        MockUpdater.return_value = updater_instance

        await executor.execute(context, event_queue)

        updater_instance.start_work.assert_called_once()
        assert updater_instance.add_artifact.call_count >= 3  # 2 chunks + final
        updater_instance.complete.assert_called_once()
        updater_instance.failed.assert_not_called()


async def test_execute_falls_back_to_complete_when_no_stream(executor, mock_client):
    mock_client.stream = MagicMock(return_value=_noop_stream())
    mock_client.complete = AsyncMock(return_value="Fallback response")

    event_queue = AsyncMock()
    context = _make_context()

    with patch("hermes_a2a.executor.TaskUpdater") as MockUpdater:
        updater_instance = AsyncMock()
        MockUpdater.return_value = updater_instance

        await executor.execute(context, event_queue)

        mock_client.complete.assert_called_once()
        updater_instance.add_artifact.assert_called_once()
        updater_instance.complete.assert_called_once()


async def test_execute_calls_failed_on_error(executor, mock_client):
    mock_client.stream = MagicMock(side_effect=Exception("network error"))

    event_queue = AsyncMock()
    context = _make_context()

    with patch("hermes_a2a.executor.TaskUpdater") as MockUpdater:
        updater_instance = AsyncMock()
        MockUpdater.return_value = updater_instance

        await executor.execute(context, event_queue)

        updater_instance.failed.assert_called_once()
        updater_instance.complete.assert_not_called()


async def test_execute_empty_message_completes_immediately(executor, mock_client):
    event_queue = AsyncMock()
    context = _make_context(message_text="   ")

    with patch("hermes_a2a.executor.TaskUpdater") as MockUpdater:
        updater_instance = AsyncMock()
        MockUpdater.return_value = updater_instance

        await executor.execute(context, event_queue)

        mock_client.stream.assert_not_called()
        updater_instance.complete.assert_called_once()


async def test_cancel_calls_updater_cancel(executor, mock_client):
    event_queue = AsyncMock()
    context = _make_context()

    with patch("hermes_a2a.executor.TaskUpdater") as MockUpdater:
        updater_instance = AsyncMock()
        MockUpdater.return_value = updater_instance

        await executor.cancel(context, event_queue)

        updater_instance.cancel.assert_called_once()
