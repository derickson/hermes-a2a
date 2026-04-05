import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart
from a2a.utils.message import get_message_text

from hermes_a2a.file_utils import build_file_part, detect_file_paths
from hermes_a2a.hermes_client import HermesClient

logger = logging.getLogger(__name__)


class HermesAgentExecutor(AgentExecutor):
    def __init__(self, client: HermesClient, public_url: str = "") -> None:
        self._client = client
        self._public_url = public_url

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=context.task_id,
            context_id=context.context_id,
        )

        try:
            user_text = get_message_text(context.message) if context.message else ""
            if not user_text.strip():
                await updater.complete()
                return

            messages = [{"role": "user", "content": user_text}]
            session_id = context.context_id

            await updater.start_work()

            chunks: list[str] = []
            artifact_id = f"response-{context.task_id}"
            first_chunk = True

            async for chunk in self._client.stream(messages, session_id=session_id):
                chunks.append(chunk)
                parts = [Part(root=TextPart(kind="text", text=chunk))]
                if first_chunk:
                    await updater.add_artifact(
                        parts=parts,
                        artifact_id=artifact_id,
                        name="response",
                        append=False,
                        last_chunk=False,
                    )
                    first_chunk = False
                else:
                    await updater.add_artifact(
                        parts=parts,
                        artifact_id=artifact_id,
                        append=True,
                        last_chunk=False,
                    )

            if chunks:
                full_text = "".join(chunks)
                file_parts = [
                    build_file_part(p, self._public_url)
                    for p in detect_file_paths(full_text)
                ]
                final_parts = file_parts if file_parts else [Part(root=TextPart(kind="text", text=""))]
                await updater.add_artifact(
                    parts=final_parts,
                    artifact_id=artifact_id,
                    append=True,
                    last_chunk=True,
                )
            else:
                # Hermes returned nothing — fall back to non-streaming
                response_text = await self._client.complete(messages, session_id=session_id)
                await updater.add_artifact(
                    parts=[Part(root=TextPart(kind="text", text=response_text))],
                    name="response",
                    last_chunk=True,
                )

            await updater.complete()

        except Exception:
            logger.exception("Error executing Hermes request for task %s", context.task_id)
            await updater.failed()

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=context.task_id,
            context_id=context.context_id,
        )
        await updater.cancel()
