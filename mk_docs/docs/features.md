# Features & Tools

AutoMate provides a comprehensive set of tools that allow you to control various aspects of your computer through natural language. This page details all the available tools and how to use them.

## Browser Control Tools

These tools allow you to control web browser operations through commands.

### Open New Window

Opens a new browser window for web navigation.

**Usage Examples:**
```
"Open a new browser window"
"Start browser"
"Open browser"
```

**Tool Details:**
- No parameters required
- Creates a fresh browser window for subsequent operations
- Maximum of 5 windows can be opened simultaneously

### Search

Performs a web search using the provided query.

**Usage Examples:**
```
"Search for weather in New York"
"Look up recipe for chocolate cake"
"Find information about quantum computing"
```

**Tool Details:**
- Requires a query parameter
- Automatically opens a new window if none exists
- Returns titles and URLs of top search results

### Close Browser

Closes all open browser windows.

**Usage Examples:**
```
"Close the browser"
"Terminate browser"
"Shut down browser"
```

**Tool Details:**
- No parameters required
- Closes all windows but keeps the browser service running

## Hardware Control Tools

These tools interact with your computer's hardware components.

### Take Screenshot

Captures a screenshot of your current screen.

**Usage Examples:**
```
"Take a screenshot"
"Capture my screen"
"Screenshot this"
```

**Tool Details:**
- No parameters required
- Returns a link to view the captured image
- Images are saved in the camera_images directory

### Open Camera

Activates your computer's camera and takes a photo.

**Usage Examples:**
```
"Open camera"
"Take a photo"
"Capture an image with camera"
```

**Tool Details:**
- No parameters required
- Returns a link to view the captured photo
- Images are saved in the camera_images directory

## System Information Tools

These tools provide information about your system's hardware and performance.

### Show RAM

Displays information about memory usage.

**Usage Examples:**
```
"Show RAM information"
"Check memory usage"
"How much RAM is available?"
```

**Tool Details:**
- No parameters required
- Returns total, used, and available memory
- Values are formatted in human-readable units (KB, MB, GB)

### Show Disk

Provides information about disk storage.

**Usage Examples:**
```
"Show disk usage"
"Check available storage"
"How much disk space is left?"
```

**Tool Details:**
- No parameters required
- Returns total, used, and free disk space
- Values are formatted in human-readable units

### Show CPU

Displays CPU information and usage.

**Usage Examples:**
```
"Show CPU usage"
"Check processor information"
"What's my CPU doing?"
```

**Tool Details:**
- No parameters required
- Returns CPU specifications and current usage percentage
- Combines hardware description and real-time usage data

### Show Hardware Info

Provides comprehensive information about all system hardware.

**Usage Examples:**
```
"Show system information"
"Display hardware details"
"Give me all hardware stats"
```

**Tool Details:**
- No parameters required
- Returns combined information about all hardware components


## Command Reference Table

| Category | Command | Parameters | Description |
|----------|---------|------------|-------------|
| Browser | open_new_window | None | Opens a new browser window |
| Browser | search | query: string | Searches the web with the given query |
| Browser | close_browser | None | Closes all browser windows |
| Hardware | screenshot | None | Takes a screenshot of the current screen |
| Hardware | open_camera | None | Takes a photo using the camera |
| System | show_ram | None | Shows RAM usage information |
| System | show_disk | None | Shows disk usage information |
| System | show_cpu | None | Shows CPU information and usage |
| System | show_hardware_info | None | Shows comprehensive hardware information |
