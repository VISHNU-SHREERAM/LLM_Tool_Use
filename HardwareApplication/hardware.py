import asyncio
import shutil
import uuid
from collections.abc import Awaitable, Callable
from threading import Lock

import cv2
import psutil
import pyautogui
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from starlette.responses import Response as StarletteResponse
import httpx
import toml
import sys
from pathlib import Path
from loguru import logger
from fastapi.staticfiles import StaticFiles


parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from unified_logging.config_types import LoggingConfigs  # noqa: E402
from unified_logging.logging_client import setup_network_logger_client  # noqa: E402

LOGGING_CONFIG_PATH = Path("..", "unified_logging/logging_config.toml")
if LOGGING_CONFIG_PATH.exists():
    logging_configs = LoggingConfigs.load_from_path(LOGGING_CONFIG_PATH)
    setup_network_logger_client(logging_configs, logger)
    logger.info("hardware service started with unified logging")


app = FastAPI()

camera: cv2.VideoCapture | None = None
camera_lock: Lock = Lock()

Path("camera_images").mkdir(exist_ok=True)

# Mount the directory for direct access to the images
app.mount("/images", StaticFiles(directory="camera_images"), name="images")

# def logger_info(message:str):
#     "Log message in a server."
#     url = toml.load("log_config.toml")["url"]+"/log"
#     httpx.request(method="POST", url=url, json={"message":message})


@app.middleware("http")
async def add_cors_header(
    request: Request,
    call_next: Callable[[Request], Awaitable[StarletteResponse]],
) -> StarletteResponse:
    """Middleware to add CORS header to each response."""
    logger.info(f"Processing request: {request.method} {request.url}")
    response: StarletteResponse = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    logger.info(f"Response status: {response.status_code}")
    return response


@app.on_event("startup")
async def startup_event() -> None:
    """On startup, open the camera and perform a warmup.
    If the camera cannot be opened or warmed up, raise an exception.
    """
    global camera
    logger.info("Starting up hardware service...")
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        logger.error("Could not open camera at startup.")
        raise Exception("Error: Could not open camera at startup.")
    logger.info("Camera initialized successfully.")
    for _ in range(10):
        ret, _ = camera.read()
        if not ret:
            logger.error("Could not warm up camera.")
            raise Exception("Error: Could not warm up camera.")
        await asyncio.sleep(0.1)
    logger.info("Camera warmed up successfully.")
    print("Camera initialized and warmed up.")


@app.on_event("shutdown")
def shutdown_event() -> None:
    """On shutdown, release the camera resource if it exists."""
    global camera
    logger.info("Shutting down hardware service...")
    if camera is not None:
        camera.release()
        logger.info("Camera resource released successfully.")


@app.get("/capture")
async def capture():
    """Take a photo with the camera and return it as base64."""
    logger.info("Received request to capture an image.")
    try:
        import base64
        import os
        import time
        from io import BytesIO

        import cv2

        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"error": "Could not open camera"}

        # Allow camera to initialize
        # Some cameras need warming up
        for _ in range(5):
            cap.read()

        # Capture frame
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return {"error": "Could not capture image"}

        # Create directory if it doesn't exist
        Path("camera_images").mkdir(exist_ok=True)

        # Save to file
        filename = f"camera_{int(time.time())}.jpg"
        filepath = Path("camera_images") / filename
        cv2.imwrite(filepath, frame)

        # Convert to base64 properly
        _, buffer = cv2.imencode(".jpg", frame)
        img_bytes = buffer.tobytes()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        logger.info(f"Image captured and saved as {filename}.")
        return {
            "message": "Camera image captured successfully",
            "image_path": filepath,
            "filename": filename,  # Add just the filename for easier access
        }

    except Exception as e:
        logger.error(f"Camera capture failed: {str(e)}")
        return {"error": f"Camera capture failed: {str(e)}"}


@app.get("/screenshot")
async def screenshot():
    """Take a screenshot of the current screen and return information about the saved image."""
    logger.info("Received request to take a screenshot.")

    # Import check as a separate step with detailed logging
    try:
        # First try to import PIL to check if Pillow is installed
        try:
            from PIL import Image

            logger.info("PIL/Pillow is available")
        except ImportError as e:
            logger.error(f"PIL import error: {str(e)}")
            return {
                "error": f"Screenshot failed: Pillow is not installed. Please run 'pip install pillow'."
            }

        # Then try to import pyautogui separately
        try:
            import pyautogui

            logger.info("PyAutoGUI is available")
        except ImportError as e:
            logger.error(f"PyAutoGUI import error: {str(e)}")
            return {
                "error": f"Screenshot failed: PyAutoGUI is not installed. Please run 'pip install pyautogui'."
            }

        # Create directory if it doesn't exist
        Path("camera_images").mkdir(exist_ok=True)

        # Generate a unique filename
        filename = f"screenshot_{uuid.uuid4().hex}.jpg"
        filepath = Path("camera_images") / filename

        # Capture the screenshot with more detailed error handling
        logger.info("Attempting to capture screenshot...")
        try:
            image = pyautogui.screenshot()
            logger.info("Screenshot captured, attempting to save...")
            image.save(str(filepath))
            logger.info(f"Screenshot saved as {filepath}.")

            # Return the same pattern of response as open_camera
            return {
                "message": "Screenshot captured successfully",
                "image_path": str(filepath),
                "filename": filename,
            }
        except Exception as screenshot_error:
            logger.error(
                f"Error during screenshot capture or save: {str(screenshot_error)}"
            )
            return {
                "error": f"Screenshot operation failed: {str(screenshot_error)}. This might be due to display server access restrictions."
            }

    except Exception as e:
        logger.error(f"Screenshot failed with unexpected error: {str(e)}")
        return {
            "error": f"Screenshot failed with unexpected error: {str(e)}. Please ensure both 'pyautogui' and 'pillow' are installed."
        }


@app.get("/cpu")
def cpu() -> JSONResponse:
    """Returns the current CPU usage percentage."""
    logger.info("Received request for CPU usage.")
    cpu_percent = psutil.cpu_percent(interval=0.5)
    logger.info(f"CPU usage: {cpu_percent}%")
    return JSONResponse(content={"cpu_percent": cpu_percent})


def get_disk_usage() -> tuple[int, int, int]:
    """Returns disk usage (total, used, free) in bytes for the root path."""
    total, used, free = shutil.disk_usage("/")
    # logger_info("disk info obtained")
    return total, used, free


def format_size(byte_size: float) -> str:
    """Formats a byte value into a human-readable string (e.g., B, KB, MB, GB, TB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if byte_size < 1024:
            return f"{byte_size:.2f}{unit}"
        byte_size /= 1024
    return f"{byte_size:.2f}PB"  # If it somehow exceeds TB


@app.get("/disk")
def disk() -> JSONResponse:
    """Returns disk usage information (total, used, free) in a formatted string."""
    logger.info("Received request for disk usage.")
    total, used, free = get_disk_usage()
    logger.info(
        f"Disk usage - Total: {format_size(total)}, Used: {format_size(used)}, Free: {format_size(free)}"
    )
    return JSONResponse(
        content={
            "total": format_size(total),
            "used": format_size(used),
            "free": format_size(free),
        },
    )


@app.get("/ram")
def ram() -> JSONResponse:
    """Returns total, used, and available RAM in a formatted string."""
    logger.info("Received request for RAM usage.")
    total = psutil.virtual_memory().total
    available = psutil.virtual_memory().available
    used = total - available
    logger.info(
        f"RAM usage - Total: {format_size(total)}, Used: {format_size(used)}, Available: {format_size(available)}"
    )
    return JSONResponse(
        content={
            "total": format_size(total),
            "used": format_size(used),
            "available": format_size(available),
        },
    )


# get for no of cores, cpu arc, name
@app.get("/cpuinfo")
def cpuinfo() -> JSONResponse:
    """Returns the number of cores, CPU architecture, and name."""
    logger.info("Received request for CPU information.")
    try:
        cpu_info = psutil.cpu_stats()
        logger.info(
            f"CPU info - Cores: {cpu_info.cores}, Arch: {cpu_info.arch}, Name: {cpu_info.name}"
        )
        return JSONResponse(
            content={
                "cores": cpu_info.cores,
                "arch": cpu_info.arch,
                "name": cpu_info.name,
            },
        )
    except Exception as e:
        logger.error(f"Failed to retrieve CPU info: {str(e)}")
        return JSONResponse(content={"error": f"Failed to retrieve CPU info: {str(e)}"})


###############################################################################
# 6. Run the Application
###############################################################################
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
