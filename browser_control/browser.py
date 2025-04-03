from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from models import SearchQuery
import httpx
import toml
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
    logger.info("Browser service started with unified logging")


class BrowserWindowLimitReachedError(Exception):
    """Exception raised when the browser window limit is reached."""


APP = FastAPI()

APP.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PLAYWRIGHT: Playwright | None = None
BROWSER: Browser | None = None
CONTEXT: BrowserContext | None = None

SEARCH_URL = "https://www.bing.com/search?q="
MAX_WINDOWS = 5

# def #logger_info(message:str):
#     "Log message in a server."
#     url = toml.load("log_config.toml")["url"]+"/log"
#     httpx.request(method="POST", url=url, json={"message":message})


@APP.on_event("startup")
async def startup() -> None:
    """On application startup.

    1. Launch async Playwright.
    2. Launch a Firefox browser (change to chromium or webkit if desired).
    3. Create a new browser context.
    """
    global PLAYWRIGHT, BROWSER, CONTEXT
    logger.info("Starting up browser service...")
    PLAYWRIGHT = await async_playwright().start()
    # NOTE: set `headless=False` to see the browser window, or True to run in the background
    BROWSER = await PLAYWRIGHT.firefox.launch(headless=False)
    CONTEXT = await BROWSER.new_context()
    logger.info("Browser service started successfully.")


@APP.on_event("shutdown")
async def shutdown() -> None:
    """On application shutdown, close Playwright properly."""
    if PLAYWRIGHT:
        logger.info("Shutting down browser service...")
        await PLAYWRIGHT.stop()
        logger.info("Browser service shut down successfully.")


@APP.post("/browser/new_window_and_search")
async def new_window_and_search(query: SearchQuery) -> dict:
    """Open a new window and perform a search."""
    logger.info(f"Received request to open a new window and search for: {query.query}")
    await open_new_window()
    return await search(query)


@APP.get("/browser/open_new_window")
async def open_new_window() -> dict:
    """Open a new window in the existing browser context.

    Limited to 5 pages by default.
    """
    logger.info("Received request to open a new browser window.")
    if CONTEXT is None:
        logger.warning("Browser context is not initialized.")
        return {"response": "Browser context is not initialized."}

    try:
        if len(CONTEXT.pages) >= MAX_WINDOWS:

            def raise_window_limit_error() -> None:
                """Error to indicate that the maximum number of browser windows has been reached.

                Raises:
                    BrowserWindowLimitReachedError: Exception indicating the browser window limit has been reached.

                """
                raise BrowserWindowLimitReachedError(
                    "Maximum browser window limit reached."
                )

            logger.warning("Maximum browser window limit reached.")
            raise_window_limit_error()
        else:
            await CONTEXT.new_page()
            logger.info("New browser window opened successfully.")
            return {"response": "Opened a new window."}
    except BrowserWindowLimitReachedError as e:
        logger.error(f"Error: {str(e)}")
        return {"response": str(e)}


@APP.post("/browser/search")
async def search(query: SearchQuery) -> dict:
    """Perform a search on the most recently opened page.

    Args:
        query (SearchQuery): The search query to be performed.

    Returns:
        dict: A dictionary containing the response message, including search results and their URLs.
    """
    logger.info(f"Received search request for query: {query.query}")
    if CONTEXT is None:
        logger.warning("Browser context is not initialized.")
        return {"response": "Browser context is not initialized."}

    if len(CONTEXT.pages) == 0:
        logger.info("No open pages found. Opening a new window.")
        # If no pages exist, open a new window automatically
        await open_new_window()

    # Get the last page in the context
    page: Page = CONTEXT.pages[-1]
    await page.goto(SEARCH_URL + query.query)
    logger.info(f"Navigated to search URL: {SEARCH_URL + query.query}")

    # Get all result elements
    result_elements = await page.query_selector_all("h2 a")

    # Extract titles and links
    results = []
    for i, element in enumerate(result_elements[:3]):  # Limit to top 5 results
        title = await element.text_content()
        href = await element.get_attribute("href")
        results.append({"title": title, "url": href})
        logger.info(f"Result {i + 1}: Title: {title}, URL: {href}")

    logger.info(f"Search completed for query: {query.query}")
    return {"response": f"Searching for {query.query}", "results": results}


@APP.post("/browser/close_current_window")
async def close_current_window() -> dict:
    """Close the most recently opened window if any exist."""
    logger.info("Received request to close the current browser window.")
    if CONTEXT is None:
        logger.warning("Browser context is not initialized.")
        return {"response": "Browser context is not initialized."}

    if len(CONTEXT.pages) == 0:
        logger.warning("No open windows to close.")
        return {"response": "No open windows to close."}

    await CONTEXT.pages[-1].close()
    logger.info("Closed the current browser window.")
    return {"response": "Closed the current window."}


@APP.get("/browser/close_browser")
async def close_browser() -> dict:
    """Close all open pages in the current context.

    (Does NOT close the entire Playwright instance;
     shutting down the entire app will do that.).
    """
    logger.info("Received request to close all browser windows.")
    if CONTEXT is None:
        logger.warning("Browser context is not initialized.")
        return {"response": "Browser context is not initialized."}

    for page in CONTEXT.pages:
        await page.close()
    logger.info("All browser windows closed successfully.")
    return {"response": "Closed all browser windows."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(APP, host="0.0.0.0", port=8001)
