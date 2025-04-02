from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_ollama.chat_models import ChatOllama
from langchain.agents import create_tool_calling_agent, AgentExecutor
from pydantic import BaseModel, Field
from tools import TOOLS

# Initialize model
model = ChatOllama(model="qwen2.5:3b", temperature=0)

# Define a proper tool-calling prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an AI assistant that can call functions."),
        ("human", "{prompt}"),
        ("placeholder", "{agent_scratchpad}")  # Necessary for tracking tool execution
    ]
)

# Create the agent
agent = create_tool_calling_agent(llm=model, tools=TOOLS, prompt=prompt)

# Wrap the agent inside an executor
executor = AgentExecutor(agent=agent, tools=TOOLS, verbose=True, handle_parsing_errors=True)

# Invoke the agent
response = executor.invoke({"prompt": "close all windows"})

print(response["output"])
