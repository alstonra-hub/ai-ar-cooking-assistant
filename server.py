from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import cv2
from threading import Thread, Event
from FoodDetector import detect_food
from progress_tracker import FoodItemTracker

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!' # In a real app, this should be a real secret
socketio = SocketIO(app)

@app.route('/')
def index():
    return "API Server for AR Cooking Assistant is running."

# This will be replaced with real logic from progress_tracker.py later
mock_progress = {
    "current_state": "Chopping onions",
    "progress_percentage": 0
}

@app.route('/progress')
def progress():
    """Returns the current cooking progress."""
    # Simulate progress for now
    mock_progress["progress_percentage"] = (mock_progress["progress_percentage"] + 10) % 100
    return jsonify(mock_progress)

@socketio.on('connect')
def handle_connect():
    """Handles a new client connection."""
    print('Client connected')
    # Send a welcome message to the client that just connected
    emit('status_update', {'data': 'Welcome to the AR Cooking Assistant API!'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handles a client disconnection."""
    print('Client disconnected')

def push_progress_update(progress_data):
    """
    Pushes a progress update to all connected clients.
    This function will be called from the progress tracking logic.
    """
    socketio.emit('progress_update', progress_data, broadcast=True)

# Global state for tracking food items and thread control
food_trackers = {}
thread_stop_event = Event()

def video_processing_loop():
    """
    Main loop to process video, detect food, and track progress.
    This runs in a background thread.
    """
    print("Video processing loop started.")
    # In a real application, this would capture from a live camera
    # For this simulation, we load a static image to test the pipeline
    frame = cv2.imread("test_images/dog.jpg")
    if frame is None:
        print("Error: Could not load test image. Stopping processing loop.")
        return

    tracker_id_counter = 0

    while not thread_stop_event.is_set():
        # The core of the application logic is here.
        # This will fail on the detect_food call due to the known OpenCV issue.
        # The code is written to be logically correct, assuming a compatible environment.
        try:
            detected_items = detect_food(frame)

            if detected_items:
                # Simplified tracking: focus on the first detected item
                item = detected_items[0]
                item_box = item['box']

                if not food_trackers:
                    print("INFO: New food item detected, starting tracker.")
                    food_trackers[tracker_id_counter] = FoodItemTracker(tracker_id_counter, item_box, frame)
                    tracker_id_counter += 1

                tracker = food_trackers[0]
                tracker.update(item_box, frame)

                if tracker.state_changed_this_frame:
                    print(f"INFO: State change for item {tracker.id} detected. Sending WebSocket update.")
                    update_data = {
                        "itemId": tracker.id,
                        "newState": tracker.state,
                        "message": f"Item {tracker.id} is now {tracker.state}."
                    }
                    push_progress_update(update_data)

        except cv2.error as e:
            print(f"ERROR: Known OpenCV error in detection, cannot proceed. {e}")
            print("Stopping video processing loop.")
            break # Exit the loop on this fatal error
        except Exception as e:
            print(f"An unexpected error occurred in the processing loop: {e}")
            break

        socketio.sleep(2) # Process a frame every 2 seconds

if __name__ == '__main__':
    print("Starting background task for video processing...")
    socketio.start_background_task(target=video_processing_loop)
    print("Starting Flask-SocketIO server on http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000)
