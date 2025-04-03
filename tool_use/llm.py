from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_ollama.chat_models import ChatOllama
from langchain.agents import create_tool_calling_agent, AgentExecutor
from pydantic import BaseModel, Field
from tools import TOOLS
import sys
from pathlib import Path
from loguru import logger


parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from unified_logging.config_types import LoggingConfigs  # noqa: E402
from unified_logging.logging_client import setup_network_logger_client  # noqa: E402

LOGGING_CONFIG_PATH = Path("..", "unified_logging/logging_config.toml")
if LOGGING_CONFIG_PATH.exists():
    logging_configs = LoggingConfigs.load_from_path(LOGGING_CONFIG_PATH)
    setup_network_logger_client(logging_configs, logger)
    logger.info("LLM service started with unified logging")


logger.info("Initializing ChatOllama model")
model = ChatOllama(model="qwen2.5:3b", temperature=0)

logger.info("Defining tool-calling prompt")
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an AI assistant that can call functions."),
        ("human", "{prompt}"),
        ("placeholder", "{agent_scratchpad}"),  # Necessary for tracking tool execution
    ]
)

logger.info("Creating tool-calling agent")
agent = create_tool_calling_agent(llm=model, tools=TOOLS, prompt=prompt)

logger.info("Wrapping agent inside an executor")
executor = AgentExecutor(
    agent=agent, tools=TOOLS, verbose=True, handle_parsing_errors=True
)

logger.info("Awaiting user input")
user_input = input("Enter :")
logger.info(f"User input received: {user_input}")

logger.info("Invoking the agent")
response = executor.invoke({"prompt": user_input})

logger.info(f"Agent response: {response['output']}")
print(response["output"])
