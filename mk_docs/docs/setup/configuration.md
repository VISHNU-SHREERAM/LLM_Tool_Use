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