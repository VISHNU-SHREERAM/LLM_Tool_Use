"""tools to be used by the llm"""
from langchain_core.tools import tool
from models import Query, Numbers
import httpx
import yaml

with open("../config.yaml", "r") as file:
    content = file.read()
    NETWORK_CONFIG = yaml.safe_load(content)

BROWSER_URL = "http://" + NETWORK_CONFIG["browser_service"]["host"] + ":" + str(NETWORK_CONFIG["browser_service"]["port"])
HARDWARE_URL = "http://" + NETWORK_CONFIG["hardware_service"]["host"] + ":" + str(NETWORK_CONFIG["hardware_service"]["port"])

@tool
def open_new_window() -> None:
    """Open a new browser window and does nothing."""
    response = httpx.get(url=BROWSER_URL+"/browser/open_new_window")
    result = response.json()
    return result
@tool
def search(query: Query):
    """Searches for query in the internet using browser. 
    If no window is open then it will automatically create a new window and search."""
    response = httpx.post(url=BROWSER_URL+"/browser/search", json=query.model_dump())
    result = response.json()
    return result

@tool
def close_browser():
    """Closes browser and all its windows"""
    response = httpx.get(url=BROWSER_URL+"/browser/close_browser")
    result = response.json()
    return result

@tool
def screenshot():
    """Takes a screenshot"""
    response = httpx.get(HARDWARE_URL+"/screenshot")
    result = response.json()
    return result

@tool
def open_camera():
    """Opens camera"""
    response = httpx.get(HARDWARE_URL+"/capture")
    result = response.json()
    return result

@tool
def show_ram():
    """Shows current ram info like total available, usage...etc"""
    response = httpx.get(HARDWARE_URL+"/ram")
    result = response.json()
    return result

@tool
def show_disk():
    """Shows disk information like total available, usage...etc"""
    response = httpx.get(HARDWARE_URL+"/disk")
    result = response.json()
    return result

@tool
def show_cpu():
    """Shows all the current CPU info like usage, overall clock speed, number of cores...etc"""
    response1 = httpx.get(HARDWARE_URL+"/cpuinfo")
    response2 = httpx.get(HARDWARE_URL+"/cpu")
    result1 = response1.json()
    result2 = response2.json()
    return {"hardware description":result1, "usage info": result2}

@tool
def show_hardware_info():
    """Aggregates info of different hardware components like CPU, RAM and Disk"""
    response = httpx.get(HARDWARE_URL+"/screenshot")
    result = response.json()
    return result

@tool
def add(numbers: Numbers):
    """Adds two integers."""
    print("adding...")
    return numbers.a + numbers.b

@tool
def multiply(numbers: Numbers):
    """Multiply two integers."""
    print("multiplying")
    return numbers.a * numbers.b

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
    multiply
]