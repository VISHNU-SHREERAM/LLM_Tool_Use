import sys
from pathlib import Path

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from loguru import logger
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
    """Initialize and return the agent executor"""
    try:
        logger.info("Initializing ChatOllama model")
        model = ChatOllama(model="qwen2.5:3b", temperature=0)

        logger.info("Defining tool-calling prompt")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an AI assistant that can call functions\
                        . When screenshots or images are captured, \
                            you must include the image URL in your response.",
                ),
                ("human", "{prompt}"),
                (
                    "placeholder",
                    "{agent_scratchpad}",
                ),  # Necessary for tracking tool execution
            ],
        )

        logger.info("Creating tool-calling agent")
        agent = create_tool_calling_agent(llm=model, tools=TOOLS, prompt=prompt)

        logger.info("Wrapping agent inside an executor")
        executor = AgentExecutor(
            agent=agent, tools=TOOLS, verbose=True, handle_parsing_errors=True,
        )

        return executor
    except Exception as e:
        logger.error(f"Error initializing agent: {e!s}")
        return None


def main():
    """Main function to run the LLM agent in a loop"""
    # Initialize the agent
    executor = init_agent()
    if not executor:
        logger.error("Failed to initialize agent. Exiting.")
        return

    logger.info("Agent initialized successfully")

    # Run in a loop until the user types 'exit'
    while True:
        try:
            logger.info("Awaiting user input (type 'exit' to quit)")
            user_input = input("Enter: ")

            # Check if the user wants to exit
            if user_input.lower() == "exit":
                logger.info("User requested exit. Shutting down.")
                break

            logger.info(f"User input received: {user_input}")

            # Invoke the agent
            logger.info("Invoking the agent")
            response = executor.invoke({"prompt": user_input})

            logger.info(f"Agent response: {response['output']}")
            print("\nAgent response:")
            print(response["output"])
            print("\n" + "-" * 50 + "\n")  # Separator for readability

        except Exception as e:
            logger.error(f"Error during execution: {e!s}")
            print(f"An error occurred: {e!s}")


if __name__ == "__main__":
    main()
