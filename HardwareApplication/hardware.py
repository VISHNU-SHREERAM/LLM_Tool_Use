"""Hardware."""

import asyncio
import platform
import shutil
import sys
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from threading import Lock

import cpuinfo
import cv2
import psutil
import pyautogui
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.responses import Response as StarletteResponse

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from unified_logging.config_types import LoggingConfigs  # noqa: E402
from unified_logging.logging_client import setup_network_logger_client  # noqa: E402

LOGGING_CONFIG_PATH = Path("..", "unified_logging/logging_config.toml")
if LOGGING_CONFIG_PATH.exists():
    logging_configs = LoggingConfigs.load_from_path(str(LOGGING_CONFIG_PATH))
    setup_network_logger_client(logging_configs, logger)
    logger.info("hardware service started with unified logging")


app = FastAPI()

camera: cv2.VideoCapture | None = None
camera_lock: Lock = Lock()

Path("camera_images").mkdir(exist_ok=True)

# Mount the directory for direct access to the images
app.mount("/images", StaticFiles(directory="camera_images"), name="images")


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


class CustomError(Exception):
    """Custom error class for handling exceptions."""


@app.on_event("startup")
async def startup_event() -> None:
    """On startup, open the camera and perform a warmup.

    If the camera cannot be opened or warmed up, raise an exception.
    """
    logger.info("Starting up hardware service...")
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        logger.error("Could not open camera at startup.")
        msg = "Error: Could not open camera at startup."
        raise CustomError(msg)
    logger.info("Camera opened successfully.")

    logger.info("Camera initialized successfully.")
    for _ in range(10):
        ret, _ = camera.read()
        if not ret:
            logger.error("Could not warm up camera.")
            msg = "Error: Could not warm up camera."
            raise CustomError(msg)
        logger.info("Camera warmed up successfully.")
        # Allow camera to warm up
        await asyncio.sleep(0.1)
    logger.info("Camera warmed up successfully.")


@app.on_event("shutdown")
def shutdown_event() -> None:
    """On shutdown, release the camera resource if it exists."""
    logger.info("Shutting down hardware service...")
    if camera is not None:
        camera.release()
        logger.info("Camera resource released successfully.")


@app.get("/capture")
async def capture() -> dict[str, str]:
    """Take a photo with the camera and return it as base64."""
    logger.info("Received request to capture an image.")
    try:
        import time

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
        cv2.imwrite(str(filepath), frame)
        # Convert to base64 properly
        _, buffer = cv2.imencode(".jpg", frame)

        logger.info(f"Image captured and saved as {filename}.")
        return {
            "message": "Camera image captured successfully",
            "image_path": str(filepath),
            "filename": filename,  # Add just the filename for easier access
        }

    except (Exception, BaseException) as e:
        logger.error(f"Camera capture failed: {e!s}")
        return {"error": f"Camera capture failed: {e!s}"}


@app.get("/screenshot")
async def screenshot() -> dict[str, str]:
    """Take a screenshot of the current screen.

    Returns information about the saved image.
    """
    logger.info("Received request to take a screenshot.")

    # Import check as a separate step with detailed logging
    try:
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
        except (Exception, BaseException) as screenshot_error:
            logger.error(f"Error during screenshot capture or save: {screenshot_error!s}")
            return {"error": f"Screenshot operation failed: {screenshot_error!s}."}

    except (Exception, BaseException) as e:
        logger.error(f"Screenshot failed with unexpected error: {e!s}")
        return {"error": f"Screenshot failed with unexpected error: {e!s}."}


@app.get("/cpu")
def cpu() -> JSONResponse:
    """Return the current CPU usage percentage."""
    logger.info("Received request for CPU usage.")
    cpu_percent = psutil.cpu_percent(interval=0.5)
    logger.info(f"CPU usage: {cpu_percent}%")
    return JSONResponse(content={"cpu_percent": cpu_percent})


def get_disk_usage() -> tuple[int, int, int]:
    """Return disk usage (total, used, free) in bytes for the root path."""
    total, used, free = shutil.disk_usage("/")
    return total, used, free


def format_size(byte_size: float) -> str:
    """Format the byte value into a human-readable string.

    Converts bytes to appropriate units (B, KB, MB, GB, TB) based on size.
    """
    value = 1024
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if byte_size < value:
            return f"{byte_size:.2f}{unit}"
        byte_size /= 1024
    return f"{byte_size:.2f}PB"  # If it somehow exceeds TB


@app.get("/disk")
def disk() -> JSONResponse:
    """Disk usage information (total, used, free) in a formatted string."""
    logger.info("Received request for disk usage.")
    total, used, free = get_disk_usage()
    logger.info(
        f"Disk usage - Total: {format_size(total)}, Used: {format_size(used)}, Free: {format_size(free)}",
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
    """Total, used, and available RAM in a formatted string."""
    logger.info("Received request for RAM usage.")
    total = psutil.virtual_memory().total
    available = psutil.virtual_memory().available
    used = total - available
    logger.info(
        f"RAM usage - Total: {format_size(total)}, Used: {format_size(used)}, Available: {format_size(available)}",
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
async def get_cpuinfo() -> JSONResponse:
    """Detailed CPU information."""
    cpu_data = {}

    try:
        # --- Using cpuinfo for reliable name ---
        info = cpuinfo.get_cpu_info()
        cpu_data["cpu_name"] = info.get("brand_raw", "N/A")
        cpu_data["architecture"] = info.get("arch_string_raw", platform.machine())
        cpu_data["bits"] = info.get("bits", "N/A")
        cpu_data["vendor_id"] = info.get("vendor_id_raw", "N/A")

        # --- Using psutil for counts, frequencies, and usage ---
        cpu_data["physical_cores"] = psutil.cpu_count(logical=False)
        cpu_data["logical_cores"] = psutil.cpu_count(logical=True)

        # CPU Frequency
        try:
            cpufreq = psutil.cpu_freq()
            if cpufreq:
                cpu_data["max_frequency_mhz"] = cpufreq.max
                cpu_data["min_frequency_mhz"] = cpufreq.min
                cpu_data["current_frequency_mhz"] = cpufreq.current
            else:
                cpu_data["max_frequency_mhz"] = "N/A (Not Supported)"
                cpu_data["min_frequency_mhz"] = "N/A (Not Supported)"
                cpu_data["current_frequency_mhz"] = "N/A (Not Supported)"
        except NotImplementedError:
            cpu_data["max_frequency_mhz"] = "N/A (Not Supported)"
            cpu_data["min_frequency_mhz"] = "N/A (Not Supported)"
            cpu_data["current_frequency_mhz"] = "N/A (Not Supported)"
        except (AttributeError, ValueError, TypeError) as e:
            # Catch specific potential errors during frequency fetching
            logger.error(f"Error fetching CPU frequency: {e!s}")
            cpu_data["max_frequency_mhz"] = f"Error ({type(e).__name__})"
            cpu_data["min_frequency_mhz"] = f"Error ({type(e).__name__})"
            cpu_data["current_frequency_mhz"] = f"Error ({type(e).__name__})"

        # CPU Usage (snapshot over a short interval)
        # Using a small interval gives a more "current" snapshot but blocks for that duration.
        # interval=None is non-blocking but compares CPU times since the last call *by this process*,
        # which might not be what you want for a single API request. 0.1 to 0.5 is often reasonable.
        interval = 0.2
        cpu_data["total_cpu_usage_percent"] = psutil.cpu_percent(interval=interval)
        cpu_data["per_cpu_usage_percent"] = psutil.cpu_percent(interval=interval, percpu=True)

        # Detailed CPU times percentage
        cpu_times = psutil.cpu_times_percent(interval=interval)
        cpu_data["cpu_usage_breakdown_percent"] = {
            "user": getattr(cpu_times, "user", "N/A"),
            "system": getattr(cpu_times, "system", "N/A"),
            "idle": getattr(cpu_times, "idle", "N/A"),
            "interrupt": getattr(cpu_times, "interrupt", "N/A"),  # May not be available on all OS
            "dpc": getattr(cpu_times, "dpc", "N/A"),  # May not be available on all OS (Windows)
        }

        # --- Basic Platform Info ---
        cpu_data["os_platform"] = platform.system()
        cpu_data["os_release"] = platform.release()
        cpu_data["os_version"] = platform.version()

    except AttributeError as e:
        # General error handling
        return JSONResponse(status_code=500, content={"error": f"Failed to retrieve CPU info: {e!s}"})

    return JSONResponse(content=cpu_data)


###############################################################################
# 6. Run the Application
###############################################################################
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8003)
