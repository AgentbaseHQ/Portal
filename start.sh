#!/bin/bash
set -e

# Print a message
echo "Starting virtual display and VNC server..."

# Start Xvfb
Xvfb $DISPLAY -screen 0 $RESOLUTION &
echo "Xvfb started on display $DISPLAY"

# Give Xvfb a moment to start
sleep 2

# Start x11vnc
x11vnc -display $DISPLAY -forever -shared -nopw &
echo "x11vnc server started on port 5900"

# Start noVNC (HTML5 VNC client)
/usr/bin/websockify --web=/usr/share/novnc/ 6080 localhost:5900 &
echo "noVNC HTML5 client started on port 6080"

# Switch to the pointer user
su - pointer -c "DISPLAY=$DISPLAY chromium --no-sandbox --disable-gpu --disable-dev-shm-usage --disable-software-rasterizer --disable-setuid-sandbox --no-first-run --window-size=1920,1080 --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0" &

echo "Chromium browser started"

# Start the browser server
cd /browser
echo "Starting the browser server..."
python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 &
echo "Browser server started on port 8000"

# Change back to /home/pointer as the working directory
cd /home/pointer
echo "Changed working directory to /home/pointer"

echo "Connect to VNC on port 5900 or use noVNC by pointing your browser to http://localhost:6080/vnc.html"
echo "Browser server API available at http://localhost:8000"

# Keep the container running
echo "Container is running. Press Ctrl+C to stop."
tail -f /dev/null 