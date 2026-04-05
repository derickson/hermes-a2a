import pytest
import respx
import httpx

from hermes_a2a.hermes_client import HermesClient


BASE_URL = "http://127.0.0.1:8642"
API_KEY = "test-key"


@pytest.fixture
def client():
    return HermesClient(base_url=BASE_URL, api_key=API_KEY, model="hermes-agent", timeout=10.0)


@respx.mock
async def test_complete_returns_content(client):
    respx.post(f"{BASE_URL}/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": "Hello!"}}]
            },
        )
    )
    result = await client.complete([{"role": "user", "content": "Hi"}])
    assert result == "Hello!"


@respx.mock
async def test_complete_sends_session_id(client):
    route = respx.post(f"{BASE_URL}/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "Hi"}}]},
        )
    )
    await client.complete([{"role": "user", "content": "Hi"}], session_id="sess-123")
    assert route.calls[0].request.headers["X-Hermes-Session-Id"] == "sess-123"


@respx.mock
async def test_complete_raises_on_http_error(client):
    respx.post(f"{BASE_URL}/v1/chat/completions").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )
    with pytest.raises(httpx.HTTPStatusError):
        await client.complete([{"role": "user", "content": "Hi"}])


@respx.mock
async def test_stream_yields_deltas(client):
    sse_body = (
        'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n'
        'data: {"choices": [{"delta": {"content": " world"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    respx.post(f"{BASE_URL}/v1/chat/completions").mock(
        return_value=httpx.Response(200, text=sse_body)
    )
    chunks = []
    async for chunk in client.stream([{"role": "user", "content": "Hi"}]):
        chunks.append(chunk)
    assert chunks == ["Hello", " world"]


@respx.mock
async def test_stream_skips_empty_deltas(client):
    sse_body = (
        'data: {"choices": [{"delta": {}}]}\n\n'
        'data: {"choices": [{"delta": {"content": "text"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    respx.post(f"{BASE_URL}/v1/chat/completions").mock(
        return_value=httpx.Response(200, text=sse_body)
    )
    chunks = []
    async for chunk in client.stream([{"role": "user", "content": "Hi"}]):
        chunks.append(chunk)
    assert chunks == ["text"]
