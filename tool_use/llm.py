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
    logging_configs = LoggingConfigs.load_from_path(LOGGING_CONFIG_PATH)
    setup_network_logger_client(logging_configs, logger)
    logger.info("LLM service started with unified logging")


def init_agent():
    """Initialize and return the tool-calling agent executor."""
    try:
        logger.info("Initializing ChatOllama model")
        model = ChatOllama(model="qwen2.5:7b", temperature=0)

        logger.info("Defining tool-calling prompt")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an AI assistant that can call functions. When screenshots or images are captured, "
                    "you must include the image URL in your response.",
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

        return executor
    except Exception as e:
        logger.error(f"Error initializing agent: {e!s}")
        return None


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
    prompt: str


@app.post("/ask")
def query_endpoint(request: QueryRequest):
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
        return {"result": raw_output, "additional": []}
    except Exception as e:
        logger.error(f"Error during API query: {e!s}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
