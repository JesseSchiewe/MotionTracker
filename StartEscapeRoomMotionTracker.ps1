## This script sets the PYTHONPATH and starts the Motion Tracker in live mode with an event webhook URL.
## This sends output events to the EscapeRoom application via the specified webhook URL.


# First start the Kinect Bridge to allow motion control input to be available for the Motion Tracker.
# This ensures that the Motion Tracker can receive motion events from the Kinect device.
& .\src\bridge\KinectBridge\bin\Release\net472\KinectBridge.exe

# Now that the Kinect Bridge is running, set the PYTHONPATH and start the Motion Tracker so it can begin processing motion events.
# Activate the virtual environment so that the Motion Tracker can run with the correct dependencies.
.\.venv\Scripts\Activate.ps1

$env:PYTHONPATH = "src/python"
python -m motion_tracker.main --live --event-webhook-url http://127.0.0.1:5000/motion-events

