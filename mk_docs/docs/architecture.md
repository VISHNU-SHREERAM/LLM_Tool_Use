# System Architecture

AutoMate follows a modular, microservices-based architecture that separates different concerns into independent services. This design allows for flexibility, scalability, and ease of maintenance.

## Architecture Overview

AutoMate consists of several key components that work together to enable natural language control of computer systems:

1. **LLM Agent** - The brain of the system that interprets commands
2. **Browser Service** - Handles web browser control operations
3. **Hardware Service** - Manages hardware interactions and system metrics
4. **Unified Logging** - Centralized logging system across all components

These components communicate with each other through HTTP APIs, creating a flexible and distributed system.

## Component Breakdown

### User Interface Layer

- **Text Interface**: Command-line interface for entering text commands
- **Voice Interface**: (Planned) Browser-based interface for voice commands

### Core Processing

- **LLM Agent**: The central controller that interprets natural language and decides which tools to invoke
  - Powered by Qwen2.5 model via Ollama
  - Uses LangChain framework for tool-calling functionality

- **Tool Manager**: Routes requests to appropriate service based on LLM agent's decisions

### Service Layer

- **Browser Service**
  - Manages Firefox browser instances using Playwright
  - Handles opening new windows, searching, and closing browsers
  - Implements safeguards like maximum window limits

- **Hardware Service**
  - Provides access to hardware components via FastAPI endpoints
  - Handles camera access, screenshots, and system information retrieval
  - Manages image storage and access via static file serving

- **Math Tools**
  - Performs mathematical operations like addition and multiplication
  - Implemented as direct function calls within the LLM agent

### Infrastructure Layer

- **Unified Logging System**
  - Centralized logging service using ZMQ for inter-process communication
  - Collects logs from all services into a single file
  - Provides standardized logging format and rotation

## Data Flow

1. **Input Processing**:
   - User provides input via text or voice
   - Text is sent to the LLM agent for processing

2. **Command Interpretation**:
   - LLM agent analyzes the text to determine user intent
   - Selects appropriate tool based on context
   - Extracts any necessary parameters

3. **Tool Execution**:
   - Selected tool receives command and parameters
   - Tool executes the requested action
   - Results are captured and formatted

4. **Response Delivery**:
   - Results are returned to LLM agent
   - LLM agent generates natural language response
   - Response is presented to user

5. **Logging**:
   - Each step in the process generates logs
   - Logs are consolidated by the unified logging system
   - System health and activity can be monitored

## Network Communication

Services communicate over HTTP/REST APIs, with the following default ports:

- **Browser Service**: Port 8001
- **Hardware Service**: Port 8003
- **Logging Service**: Port 8080

Configuration is centralized in `config.yaml` for easy deployment in different environments.

## Design Principles

1. **Modularity**: Each component has a single responsibility and can be developed/replaced independently
2. **Statelessness**: Services maintain minimal state for reliability
3. **Configurability**: System behavior can be adjusted through configuration files
4. **Observability**: Comprehensive logging enables debugging and monitoring
