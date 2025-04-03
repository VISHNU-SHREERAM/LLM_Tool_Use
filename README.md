# LLM_Tool_Use

Before running make sure you have Ollama installed
and also pull the ollama qwen2.5:3b model

to run
-   cd unified_logging && uv run .\start_logging_server.py
-   cd browser_control && uv run .\browser.py
-   cd HardwareApplication && uv run .\hardware.py
-   cd tool_use && uv run .\llm.py
