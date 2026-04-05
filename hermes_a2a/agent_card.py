from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(host: str, port: int) -> AgentCard:
    url = f"http://{host}:{port}/"

    skills = [
        AgentSkill(
            id="hermes_chat",
            name="General AI Assistant",
            description=(
                "Conversational AI with access to tools: terminal, file system, "
                "web search, memory, and more."
            ),
            tags=["chat", "assistant", "general"],
            examples=[
                "What files are in my project?",
                "Search the web for the latest Python news",
                "Help me write a bash script",
            ],
        ),
        AgentSkill(
            id="hermes_tools",
            name="Tool Use",
            description=(
                "Execute terminal commands, read/write files, browse the web, "
                "manage scheduled jobs, and interact with the local system."
            ),
            tags=["tools", "terminal", "files", "web", "system"],
            examples=[
                "Run pytest and show me the results",
                "Read the contents of README.md",
                "Schedule a daily standup reminder at 9am",
            ],
        ),
    ]

    return AgentCard(
        name="Hermes Agent",
        description=(
            "A powerful local AI agent with full tool access including terminal, "
            "file system, web search, memory, and scheduled jobs."
        ),
        url=url,
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=True,
        ),
        skills=skills,
    )
