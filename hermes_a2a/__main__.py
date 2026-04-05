import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, Response

from hermes_a2a.agent_card import build_agent_card
from hermes_a2a.config import settings
from hermes_a2a.executor import HermesAgentExecutor
from hermes_a2a.hermes_client import HermesClient

logging.basicConfig(
    level=getattr(logging, settings.a2a_log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def _resolve_public_url() -> str:
    if settings.a2a_public_url:
        return settings.a2a_public_url.rstrip("/")
    host = settings.a2a_host if settings.a2a_host != "0.0.0.0" else "127.0.0.1"
    return f"http://{host}:{settings.a2a_port}"


async def _serve_file(request: Request) -> Response:
    path = "/" + request.path_params["path"]
    allowed = settings.a2a_file_serve_paths
    if not any(path.startswith(p.rstrip("/") + "/") or path == p for p in allowed):
        return Response("Forbidden", status_code=403)
    real = os.path.realpath(path)
    if not any(real.startswith(os.path.realpath(p)) for p in allowed):
        return Response("Forbidden", status_code=403)
    if not os.path.isfile(real):
        return Response("Not Found", status_code=404)
    return FileResponse(real)


def create_app() -> Starlette:
    public_url = _resolve_public_url()
    client = HermesClient(
        base_url=settings.hermes_url,
        api_key=settings.hermes_api_key,
        model=settings.hermes_model,
        timeout=settings.hermes_timeout,
    )
    executor = HermesAgentExecutor(client, public_url=public_url)
    task_store = InMemoryTaskStore()
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
    )
    agent_card = build_agent_card(settings.a2a_host, settings.a2a_port)

    @asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        logger.info(
            "hermes-a2a starting — bridging to %s, listening on %s:%d",
            settings.hermes_url,
            settings.a2a_host,
            settings.a2a_port,
        )
        try:
            yield
        finally:
            await client.close()
            logger.info("hermes-a2a stopped")

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    app = server.build()
    app.router.lifespan_context = lifespan
    app.add_route("/files/{path:path}", _serve_file, methods=["GET"])
    return app


def main() -> None:
    uvicorn.run(
        create_app(),
        host=settings.a2a_host,
        port=settings.a2a_port,
        log_level=settings.a2a_log_level.lower(),
    )


if __name__ == "__main__":
    main()
