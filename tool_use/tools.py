"""Tools to be used by the LLM for various system control and information gathering operations."""

import sys
from pathlib import Path

import httpx
import yaml
from langchain_core.tools import tool
from loguru import logger
from models import Numbers

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from unified_logging.config_types import LoggingConfigs  # noqa: E402
from unified_logging.logging_client import setup_network_logger_client  # noqa: E402

LOGGING_CONFIG_PATH = Path("..", "unified_logging/logging_config.toml")
if LOGGING_CONFIG_PATH.exists():
    logging_configs = LoggingConfigs.load_from_path(str(LOGGING_CONFIG_PATH))
    setup_network_logger_client(logging_configs, logger)
    logger.info("Tools service started with unified logging")


config_path = Path("../config.yaml")
with config_path.open() as file:
    content = file.read()
    NETWORK_CONFIG = yaml.safe_load(content)

BROWSER_URL = (
    "http://" + NETWORK_CONFIG["browser_service"]["host"] + ":" + str(NETWORK_CONFIG["browser_service"]["port"])
)
HARDWARE_URL = (
    "http://" + NETWORK_CONFIG["hardware_service"]["host"] + ":" + str(NETWORK_CONFIG["hardware_service"]["port"])
)


@tool
def open_new_window() -> None:
    """Tool will open a new browser window in the system.

    This tool doesn't require any parameters. It creates a fresh browser window where
    subsequent browser operations like search can be performed. If no browser windows
    exist yet, this will open the first one.

    Example usage:
    open_new_window() - Opens a new browser tab or window

    Returns:
        Information about the operation status as a JSON object

    """
    logger.info("Executing open_new_window tool")
    response = httpx.get(url=BROWSER_URL + "/browser/open_new_window")
    result = response.json()
    logger.info(f"open_new_window response: {result}")
    return result


@tool
def search(query: str) -> dict:
    """Tool will Search the internet using a browser with the provided query.

    This tool performs a web search in a browser window.
    Use this tool when you don't know about the topic.
    The search results will include titles and URLs of top matches.

    Args:
    ----
        query: A JSON object containing a 'query' field with the search term
              Example: query = {"query": "weather forecast"}

    Examples:
    --------
    If you want to search for "...", you can use this tool like:
        search(query = "..."})

    Returns:
    -------
        JSON object with search results including titles and URLs

    """
    logger.info(f"Executing search tool with query: {query}")
    try:
        response = httpx.post(
            url=BROWSER_URL + "/browser/search",
            json={"query": query},
            timeout=10.0,  # Set explicit timeout
        )
        logger.info(f"search response: {response.json()}")
        return response.json()
    except httpx.ReadTimeout:
        logger.error("Browser service not responding. Is it running?")
        return {"error": "Browser service not responding. Is it running?"}
    except httpx.ConnectError:
        logger.error("Could not connect to browser service. Make sure it's running.")
        return {"error": "Could not connect to browser service. Make sure it's running."}


@tool
def close_browser() -> dict:
    """Tool Closes all browser windows and tabs.

    This tool doesn't require any parameters. It will close all currently open
    browser windows and tabs, but the browser service itself remains running
    so you can open new windows later.

    Example usage:
    close_browser() - Closes all browser windows

    Returns:
        Information about the operation status as a JSON object

    """
    logger.info("Executing close_browser tool")
    response = httpx.get(url=BROWSER_URL + "/browser/close_browser")
    result = response.json()
    logger.info(f"close_browser response: {result}")
    return result


@tool
def screenshot() -> dict:
    """Tool takes a screenshot of the current screen.

    This tool captures everything currently visible on the computer screen
    and returns image data that can be displayed or saved.
    No parameters are needed.

    Example usage:
    screenshot() - Takes a screenshot of the current screen

    Returns:
        JSON object with the screenshot details and image path/data

    """
    logger.info("Executing screenshot tool")
    try:
        response = httpx.get(HARDWARE_URL + "/screenshot", timeout=10.0)
        logger.info(f"screenshot response: {response.json()}")

        # Check if the response was successful
        correct_code = 200
        if response.status_code == correct_code:
            result = response.json()

            # Check if the response contains image information
            if "image_path" in result:
                # Extract just the filename without subdirectories
                filename = Path(result["image_path"]).name

                # Fix the URL construction
                return {
                    "success": True,
                    "message": "Screenshot captured successfully",
                    "image_path": result["image_path"],
                    "image_url": f"{HARDWARE_URL}/images/{filename}",
                }
            if "image_data" in result:
                # Make sure image_data is already base64-encoded from the server
                return {
                    "success": True,
                    "message": "Screenshot captured successfully",
                    "image_data": result["image_data"],  # Already base64 encoded
                    "content_type": result.get("content_type", "image/jpeg"),
                }
            else:  # noqa: RET505
                return {
                    "success": True,
                    "message": "Screenshot tool executed but no image data was returned",
                    "raw_response": result,
                }
        else:
            return {
                "success": False,
                "error": f"Server returned error: {response.status_code}",
                "details": response.text,
            }
    except Exception as e:  # noqa: BLE001
        logger.error(f"Unknown error in screenshot tool: {e!s}")
        return {"success": False, "error": f"Unknown error: {e!s}"}


@tool
def open_camera() -> dict:
    """Tool opens the camera and takes a photo.

    This tool activates the computer's camera, captures a single photo,
    and returns the image data. No parameters are needed.

    Example usage:
    open_camera() - Takes a photo with the camera

    Returns:
        JSON object with camera photo details and image path/data

    """
    logger.info("Executing open_camera tool")
    ok = 200
    try:
        response = httpx.get(HARDWARE_URL + "/capture", timeout=15.0)
        logger.info(f"open_camera response: {response.json()}")

        # Check if the response was successful
        if response.status_code == ok:
            result = response.json()

            # Check if the response contains image information
            if "image_path" in result:
                # Extract just the filename without subdirectories
                filename = Path(result["image_path"]).name

                # Fix the URL construction
                return {
                    "success": True,
                    "message": "Camera photo captured successfully",
                    "image_path": result["image_path"],
                    "image_url": f"{HARDWARE_URL}/images/{filename}",
                }
            if "image_data" in result:
                # Make sure image_data is already base64-encoded from the server
                return {
                    "success": True,
                    "message": "Camera photo captured successfully",
                    "image_data": result["image_data"],  # Already base64 encoded
                    "content_type": result.get("content_type", "image/jpeg"),
                }
            return {
                "success": True,
                "message": "Camera opened but no image data was returned",
                "raw_response": result,
            }

    except (httpx.ReadTimeout, httpx.ConnectError) as e:
        logger.error(f"Unknown error in open_camera: {e!s}")
        return {"success": False, "error": f"Unknown error: {e!s}"}

    return {
        "success": False,
        "error": f"Server returned error: {response.status_code}",
        "details": response.text,
    }


@tool
def show_ram() -> dict:
    """Tool shows current RAM (memory) information.

    This tool retrieves detailed information about the system's RAM usage,
    including total available memory, used memory, and free memory.
    No parameters are needed.

    Example usage:
    show_ram() - Shows RAM information

    Returns:
        JSON object with RAM details including total, used, and available memory

    """
    logger.info("Executing show_ram tool")
    response = httpx.get(HARDWARE_URL + "/ram")
    result = response.json()
    logger.info(f"show_ram response: {result}")
    return result


@tool
def show_disk() -> dict:
    """Tool shows disk storage information.

    This tool provides details about the computer's disk usage,
    including total disk space, used space, and available space.
    No parameters are needed.

    Example usage:
    show_disk() - Shows disk information

    Returns:
        JSON object with disk details including total, used, and free space

    """
    logger.info("Executing show_disk tool")
    response = httpx.get(HARDWARE_URL + "/disk")
    result = response.json()
    logger.info(f"show_disk response: {result}")
    return result


@tool
def show_cpu() -> dict:
    """Tool shows detailed CPU information and usage.

    This tool retrieves comprehensive information about the computer's CPU,
    including usage percentage, clock speed, number of cores, and other
    technical specifications. No parameters are needed.

    Example usage:
    show_cpu() - Shows CPU information and usage

    Returns:
        JSON object with CPU specifications and current usage percentage

    """
    logger.info("Executing show_cpu tool")
    response1 = httpx.get(HARDWARE_URL + "/cpuinfo")
    result1 = response1.json()
    logger.info(f"show_cpu response: {result1}")
    return {"hardware description": result1}


@tool
def show_hardware_info() -> dict:
    """Tool shows comprehensive system hardware information.

    This tool aggregates data about all major hardware components including
    CPU, RAM, and disk storage, providing a complete overview of the system.
    No parameters are needed.

    Example usage:
    show_hardware_info() - Shows comprehensive hardware information

    Returns:
        JSON object with combined information about all hardware components

    """
    logger.info("Executing show_hardware_info tool")

    # Get CPU information
    response_cpu = httpx.get(HARDWARE_URL + "/cpuinfo")
    cpu_info = response_cpu.json()
    logger.info(f"CPU info: {cpu_info}")

    # Get RAM information
    response_ram = httpx.get(HARDWARE_URL + "/ram")
    ram_info = response_ram.json()
    logger.info(f"RAM info: {ram_info}")

    # Get Disk information
    response_disk = httpx.get(HARDWARE_URL + "/disk")
    disk_info = response_disk.json()
    logger.info(f"Disk info: {disk_info}")

    # Combine all hardware information into one dictionary
    combined_info = {
        "cpu": cpu_info,
        "ram": ram_info,
        "disk": disk_info,
    }
    logger.info(f"show_hardware_info result: {combined_info}")

    return combined_info


@tool
def add(numbers: Numbers) -> float:
    """Tool adds two numbers together.

    This tool performs addition of two numbers and returns their sum.

    Args:
        numbers: A Numbers object with two fields: 'a' and 'b'
                Both should be numbers (integers or floats)

    Examples:
        add({"a": 5, "b": 3}) - Returns 8
        add({"a": 2.5, "b": 7.5}) - Returns 10.0

    Returns:
        The sum of the two numbers (a + b)

    """
    logger.info(f"Executing add tool with numbers: {numbers}")
    result = numbers.a + numbers.b
    logger.info(f"add result: {result}")
    return result


@tool
def multiply(numbers: Numbers) -> float:
    """Multiplies two numbers together.

    This tool performs multiplication of two numbers and returns their product.

    Args:
        numbers: A Numbers object with two fields: 'a' and 'b'
                Both should be numbers (integers or floats)

    Examples:
        multiply({"a": 5, "b": 3}) - Returns 15
        multiply({"a": 2.5, "b": 4}) - Returns 10.0

    Returns:
        The product of the two numbers (a * b)

    """
    logger.info(f"Executing multiply tool with numbers: {numbers}")
    result = numbers.a * numbers.b
    logger.info(f"multiply result: {result}")
    return result


TOOLS = [
    open_new_window,
    search,
    close_browser,
    screenshot,
    open_camera,
    show_ram,
    show_disk,
    show_cpu,
    # show_hardware_info,
]
