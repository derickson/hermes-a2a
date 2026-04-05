import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette

from hermes_a2a.agent_card import build_agent_card
from hermes_a2a.config import settings
from hermes_a2a.executor import HermesAgentExecutor
from hermes_a2a.hermes_client import HermesClient

logging.basicConfig(
    level=getattr(logging, settings.a2a_log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> Starlette:
    client = HermesClient(
        base_url=settings.hermes_url,
        api_key=settings.hermes_api_key,
        model=settings.hermes_model,
        timeout=settings.hermes_timeout,
    )
    executor = HermesAgentExecutor(client)
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
