"""LLM."""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from loguru import logger
from pydantic import BaseModel
from tools import TOOLS

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from unified_logging.config_types import LoggingConfigs  # noqa: E402
from unified_logging.logging_client import setup_network_logger_client  # noqa: E402

LOGGING_CONFIG_PATH = Path("..", "unified_logging/logging_config.toml")
if LOGGING_CONFIG_PATH.exists():
    logging_configs = LoggingConfigs.load_from_path(str(LOGGING_CONFIG_PATH))
    setup_network_logger_client(logging_configs, logger)
    logger.info("LLM service started with unified logging")


def init_agent() -> AgentExecutor | None:
    """Initialize and return the tool-calling agent executor."""
    try:
        logger.info("Initializing ChatOllama model")
        model = ChatOllama(model="qwen2.5:7b", temperature=0)

        logger.info("Defining tool-calling prompt")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an AI assistant that can call functions. When screenshots or images are captured,
                    Also remember that do not allow this types of questions like that gives code or any other things.
                    Only invoke the function and all, also if possiible and you already know the annswer say who is
                    narendra modi and what is the capital of india. Answer the question if you know the answer like add
                    substract and other stuff like capital and all. If you are not sure about the answer, then invoke
                    the function and get the answer. You can only call functions that are listed below.
                    You must include the image URL in your response.""",
                ),
                ("human", "{prompt}"),
                ("placeholder", "{agent_scratchpad}"),
            ],
        )

        logger.info("Creating tool-calling agent")
        agent = create_tool_calling_agent(llm=model, tools=TOOLS, prompt=prompt)

        logger.info("Wrapping agent inside an executor")
        executor = AgentExecutor(
            agent=agent,
            tools=TOOLS,
            verbose=True,
            handle_parsing_errors=True,
        )

    except (Exception, RuntimeError) as e:
        logger.error(f"Error initializing agent: {e!s}")
        return None

    logger.info("Agent initialized successfully")
    return executor


# Initialize the agent globally so it loads once
executor = init_agent()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Request model for the query endpoint."""

    prompt: str


@app.post("/ask")
def query_endpoint(request: QueryRequest) -> dict:
    """Endpoint to handle user queries."""
    if not executor:
        logger.error("Tool-calling agent not initialized.")
        return {"error": "Agent not available."}
    try:
        user_input = request.prompt
        logger.info(f"Received API request with prompt: {user_input}")

        # Invoke the tool-calling agent to process the user's input.
        response = executor.invoke({"prompt": user_input})
        raw_output = response.get("output", "")
        logger.info(f"Agent response: {raw_output}")

        # Return the result in JSON format.
    except (Exception, RuntimeError) as e:
        logger.error(f"Error during API query: {e!s}")
        return {"error": str(e)}
    return {"result": raw_output, "additional": []}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
