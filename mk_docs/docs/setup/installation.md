# Installation Guide

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
just build 
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




