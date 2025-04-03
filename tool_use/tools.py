"""tools to be used by the llm"""

from langchain_core.tools import tool
from models import Query, Numbers
import httpx
import yaml
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
    logger.info("Tools service started with unified logging")


with open("../config.yaml", "r") as file:
    content = file.read()
    NETWORK_CONFIG = yaml.safe_load(content)

BROWSER_URL = (
    "http://"
    + NETWORK_CONFIG["browser_service"]["host"]
    + ":"
    + str(NETWORK_CONFIG["browser_service"]["port"])
)
HARDWARE_URL = (
    "http://"
    + NETWORK_CONFIG["hardware_service"]["host"]
    + ":"
    + str(NETWORK_CONFIG["hardware_service"]["port"])
)


@tool
def open_new_window() -> None:
    """Open a new browser window and does nothing."""
    logger.info("Executing open_new_window tool")
    response = httpx.get(url=BROWSER_URL + "/browser/open_new_window")
    result = response.json()
    logger.info(f"open_new_window response: {result}")
    return result


@tool
def search(query: Query):
    """Searches for query in the internet using browser.
    If no window is open then it will automatically create a new window and search."""
    logger.info(f"Executing search tool with query: {query}")
    try:
        response = httpx.post(
            url=BROWSER_URL + "/browser/search",
            json=query.model_dump(),
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
def close_browser():
    """Closes browser and all its windows"""
    response = httpx.get(url=BROWSER_URL + "/browser/close_browser")
    result = response.json()
    return result


@tool
def screenshot():
    """Takes a screenshot"""
    response = httpx.get(HARDWARE_URL + "/screenshot")
    result = response.json()
    return result


@tool
def open_camera():
    """Opens camera and takes a photo. Returns image data that can be displayed in the frontend."""
    logger.info("Executing open_camera tool")
    try:
        response = httpx.get(HARDWARE_URL + "/capture", timeout=10.0)
        logger.info(f"open_camera response: {response.json()}")

        # Check if the response was successful
        if response.status_code == 200:
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
            elif "image_data" in result:
                # Make sure image_data is already base64-encoded from the server
                return {
                    "success": True,
                    "message": "Camera photo captured successfully",
                    "image_data": result["image_data"],  # Already base64 encoded
                    "content_type": result.get("content_type", "image/jpeg"),
                }
            else:
                return {
                    "success": True,
                    "message": "Camera opened but no image data was returned",
                    "raw_response": result,
                }
        else:
            return {
                "success": False,
                "error": f"Server returned error: {response.status_code}",
                "details": response.text,
            }

    except httpx.ReadTimeout:
        logger.error("Hardware service not responding. Is it running?")
        return {
            "success": False,
            "error": "Hardware service not responding. Is it running?",
        }
    except httpx.ConnectError:
        logger.error("Could not connect to hardware service. Make sure it's running.")
        return {
            "success": False,
            "error": "Could not connect to hardware service. Make sure it's running.",
        }
    except Exception as e:
        logger.error(f"Unknown error in open_camera: {str(e)}")
        return {"success": False, "error": f"Unknown error: {str(e)}"}


@tool
def show_ram():
    """Shows current ram info like total available, usage...etc"""
    response = httpx.get(HARDWARE_URL + "/ram")
    result = response.json()
    return result


@tool
def show_disk():
    """Shows disk information like total available, usage...etc"""
    response = httpx.get(HARDWARE_URL + "/disk")
    result = response.json()
    return result


@tool
def show_cpu():
    """Shows all the current CPU info like usage, overall clock speed, number of cores...etc"""
    response1 = httpx.get(HARDWARE_URL + "/cpuinfo")
    response2 = httpx.get(HARDWARE_URL + "/cpu")
    result1 = response1.json()
    result2 = response2.json()
    return {"hardware description": result1, "usage info": result2}


@tool
def show_hardware_info():
    """Aggregates info of different hardware components like CPU, RAM and Disk"""
    response = httpx.get(HARDWARE_URL + "/screenshot")
    result = response.json()
    return result


@tool
def add(numbers: Numbers):
    """Adds two integers."""
    logger.info(f"Executing add tool with numbers: {numbers}")
    result = numbers.a + numbers.b
    logger.info(f"add result: {result}")
    return result


@tool
def multiply(numbers: Numbers):
    """Multiply two integers."""
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
    show_hardware_info,
    add,
    multiply,
]
