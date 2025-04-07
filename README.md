# Installation Guide
## AutoMate: AI-Powered Computer Control¶
### Talk to your computer. Let AI do the rest.¶

This guide will walk you through the process of setting up AutoMate on your system.

## Prerequisites

## Step 1: Clone the Repository

```bash
git clone https://github.com/VISHNU-SHREERAM/LLM_Tool_Use.git
cd LLM_Tool_Use
```

## Step 2: Set Up the Environment

Make sure you have uv installed
Use the below link for reference:-
https://docs.astral.sh/uv/getting-started/installation/


```bash
just setup 
```

## Step 3: Install Required Models

### Install Ollama

If you haven't installed Ollama yet:

1. Visit [Ollama's website](https://ollama.ai/) and download the installer for your platform
2. Follow the installation instructions for your operating system
3. Pull the required Qwen2.5 model:

```bash
ollama pull qwen2.5:7b
```


## Step 4: Configure the System

Before running the system, you need to update the configuration file with your system's details:

1. Open `config.yaml` in your preferred text editor
2. Update the host IP addresses to match your setup:

```yaml
browser_service:
  host: 127.0.0.1  # Change to your IP if running on multiple machines
  port: 8001
hardware_service:
  host: 127.0.0.1  # Change to your IP if running on multiple machines
  port: 8003
logger_service:
  host: 127.0.0.1  # Change to your IP if running on multiple machines
  port: 8080
```

## Step 5: Run
```bash
just run 
```



# Configuration Guide

After installing AutoMate, you can customize its behavior through various configuration files. This guide explains all available configuration options.

## Main Configuration

The primary configuration file is `config.yaml` in the project root directory:

```yaml
browser_service:
  host: 10.32.7.130  # The IP address of the machine running the browser service
  port: 8001         # The port for browser service API

hardware_service:
  host: 10.32.7.130  # The IP address of the machine running the hardware service
  port: 8003         # The port for hardware service API

logger_service:
  host: 10.32.7.130  # The IP address of the machine running the logging service
  port: 8080         # The port for logging service API
```

### Network Configuration

If you're running all services on the same machine, you can use `127.0.0.1` or `localhost` as the host address. For distributed setups where services run on different machines, use the appropriate IP addresses.

!!! tip "Finding Your IP"
    You can find your machine's IP address with:
    
    - **Windows**: `ipconfig` in Command Prompt
    - **macOS/Linux**: `ifconfig` or `ip addr` in Terminal

## Logging Configuration

The logging system is configured through `unified_logging/logging_config.toml`:

```toml
min_log_level = "DEBUG"         # Minimum log level to capture (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_server_port = 9999          # ZMQ port for internal logging communication
client_log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {file}:{function}:{line} | {message}"
server_log_format = "[{level}] | {message}"
log_rotation = "00:00"          # When to rotate logs (daily at midnight)
log_file_name = "logs/log.txt"  # Where to store logs
log_compression = "zip"         # Compression format for rotated logs
```

### Log Levels

Available log levels in order of verbosity:

1. `DEBUG` - Debugging information, helpful for development
2. `INFO` - General information about system operation
3. `WARNING` - Warnings that don't prevent operation but indicate potential issues




