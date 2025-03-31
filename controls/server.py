from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import subprocess
import json
import os
import time
from pathlib import Path

app = FastAPI()

# Create screenshots directory in the same directory as the script
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

def execute_xdotool(command: str):
    """Helper function to execute xdotool commands"""
    try:
        full_command = f"DISPLAY=:99 xdotool {command}"
        subprocess.run(full_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing xdotool command: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

async def capture_screenshot():
    """Helper function to capture screenshot"""
    timestamp = str(int(time.time() * 1000))
    filename = f"screenshot-{timestamp}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    
    try:
        # Capture screenshot using imagemagick's import command
        process = subprocess.run(
            f'DISPLAY=:99 import -window root "{filepath}"',
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check if file exists and has size
        if not os.path.exists(filepath):
            raise Exception("Screenshot file was not created")
        
        if os.path.getsize(filepath) == 0:
            os.remove(filepath)
            raise Exception("Screenshot file is empty")
            
        return filepath
        
    except subprocess.CalledProcessError as e:
        print(f"Error capturing screenshot: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        raise Exception(f"Failed to capture screenshot: {e}")
    except Exception as e:
        print(f"Unexpected error during screenshot: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        raise

@app.get("/screenshot")
async def get_screenshot():
    screenshot_path = None
    try:
        screenshot_path = await capture_screenshot()
        
        # Return the file and ensure cleanup after sending
        return FileResponse(
            path=screenshot_path,
            media_type="image/png",
            filename="screenshot.png",
            background=None  # Run in the main thread to ensure proper cleanup
        )
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        # Cleanup old screenshots
        for file in os.listdir(SCREENSHOTS_DIR):
            if file.startswith("screenshot-") and file.endswith(".png"):
                file_path = os.path.join(SCREENSHOTS_DIR, file)
                try:
                    # Don't delete the file we're currently sending
                    if file_path != screenshot_path:
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error cleaning up old screenshot {file}: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "mouse":
                x = message.get("x")
                y = message.get("y")
                click = message.get("click")
                button = message.get("button", 1)
                
                if x is not None and y is not None:
                    execute_xdotool(f"mousemove {x} {y}")
                if click:
                    execute_xdotool(f"click {button}")
                    
            elif message.get("type") == "scroll":
                delta_y = message.get("deltaY", 0)
                delta_x = message.get("deltaX", 0)
                
                if delta_y != 0:
                    button = 4 if delta_y < 0 else 5  # 4 is scroll up, 5 is scroll down
                    scroll_count = abs(int(delta_y / 100))
                    for _ in range(scroll_count):
                        execute_xdotool(f"click {button}")
                        
                if delta_x != 0:
                    button = 6 if delta_x < 0 else 7  # 6 is scroll left, 7 is scroll right
                    scroll_count = abs(int(delta_x / 100))
                    for _ in range(scroll_count):
                        execute_xdotool(f"click {button}")
                        
            elif message.get("type") == "keyboard":
                input_type = message.get("inputType")
                key = message.get("key")
                
                if input_type == "type":
                    execute_xdotool(f'type "{key}"')
                elif input_type == "key":
                    execute_xdotool(f"key {key}")
                    
    except Exception as e:
        print(f"Error in websocket connection: {e}")
    finally:
        print("Client disconnected")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
