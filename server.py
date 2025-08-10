from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import cv2
from threading import Thread, Event
from FoodDetector import detect_food
from progress_tracker import FoodItemTracker

class RecipeStateManager:
    """Manages the state of the current recipe, including steps and timers."""
    def __init__(self):
        # Mock recipe data - this will be replaced by API calls in a later step
        self._recipe = {
            "name": "Simple Pasta",
            "steps": [
                {"description": "Boil water", "duration": 300}, # 5 minutes
                {"description": "Add pasta and cook", "duration": 480}, # 8 minutes
                {"description": "Drain pasta and serve", "duration": 60} # 1 minute
            ]
        }
        self.current_step_index = 0
        self.timer_remaining = self._recipe["steps"][0]["duration"]
        self.timer_is_running = False # Start in a paused state

    def get_current_status(self):
        """Returns the current state of the recipe."""
        current_step = self._recipe["steps"][self.current_step_index]
        return {
            "recipe_name": self._recipe["name"],
            "current_step": current_step["description"],
            "current_step_index": self.current_step_index,
            "total_steps": len(self._recipe["steps"]),
            "timer_remaining": self.timer_remaining,
            "timer_is_running": self.timer_is_running
        }

    def pause_timer(self):
        """Pauses the timer and notifies clients."""
        self.timer_is_running = False
        print("INFO: Timer paused.")
        push_progress_update(self.get_current_status())

    def resume_timer(self):
        """Resumes the timer and notifies clients."""
        self.timer_is_running = True
        print("INFO: Timer resumed.")
        push_progress_update(self.get_current_status())

    def next_step(self):
        """Advances to the next step and notifies clients."""
        if self.current_step_index < len(self._recipe["steps"]) - 1:
            self.current_step_index += 1
            new_step = self._recipe["steps"][self.current_step_index]
            self.timer_remaining = new_step["duration"]
            self.timer_is_running = False  # Always start new steps paused
            print(f"INFO: Advanced to step {self.current_step_index + 1}: {new_step['description']}")
            push_progress_update(self.get_current_status())
            return True
        else:
            print("INFO: Already on the final step.")
            return False

    def _decrement_timer(self):
        """Decrements the timer by one second if it is running."""
        if self.timer_is_running and self.timer_remaining > 0:
            self.timer_remaining -= 1
            # Push updates every second while timer is running
            push_progress_update(self.get_current_status())

# Create a single instance of the state manager to be used by the app
recipe_manager = RecipeStateManager()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!' # In a real app, this should be a real secret
socketio = SocketIO(app)

@app.route('/')
def index():
    return "API Server for AR Cooking Assistant is running."

@app.route('/progress')
def progress():
    """Returns the current cooking progress status."""
    return jsonify(recipe_manager.get_current_status())

# --- Command Endpoints ---

@app.route('/command/next_step', methods=['POST'])
def command_next_step():
    recipe_manager.next_step()
    return jsonify({"status": "ok", "message": "Advanced to next step."})

@app.route('/command/repeat_step', methods=['POST'])
def command_repeat_step():
    push_progress_update(recipe_manager.get_current_status())
    return jsonify({"status": "ok", "message": "Current step data re-sent."})

@app.route('/command/pause_timer', methods=['POST'])
def command_pause_timer():
    recipe_manager.pause_timer()
    return jsonify({"status": "ok", "message": "Timer paused."})

@app.route('/command/resume_timer', methods=['POST'])
def command_resume_timer():
    recipe_manager.resume_timer()
    return jsonify({"status": "ok", "message": "Timer resumed."})

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

def send_food_detected_event(item_data):
    """Sends a food detection event to all connected clients."""
    event_data = {
        "event": "food_detected",
        "item": item_data["label"],
        "confidence": item_data["confidence"]
    }
    socketio.emit('detection_event', event_data, broadcast=True)

# Global state for thread control
thread_stop_event = Event()

def timer_thread_loop():
    """A background thread that manages the recipe timer."""
    while not thread_stop_event.is_set():
        recipe_manager._decrement_timer()
        socketio.sleep(1)

def video_processing_loop():
    """
    Main loop to process video, detect food, and send WebSocket events.
    """
    print("Video processing loop started.")
    frame = cv2.imread("test_images/dog.jpg")
    if frame is None:
        print("Error: Could not load test image. Stopping processing loop.")
        return

    while not thread_stop_event.is_set():
        try:
            detected_items = detect_food(frame)

            if detected_items:
                print(f"INFO: Detected {len(detected_items)} food item(s). Sending events.")
                for item in detected_items:
                    send_food_detected_event(item)

        except cv2.error as e:
            print(f"ERROR: Known OpenCV error in detection, cannot proceed. {e}")
            print("Stopping video processing loop.")
            break
        except Exception as e:
            print(f"An unexpected error occurred in the processing loop: {e}")
            break

        socketio.sleep(2) # Detection runs every 2 seconds

if __name__ == '__main__':
    print("Starting background tasks...")
    socketio.start_background_task(target=timer_thread_loop)
    socketio.start_background_task(target=video_processing_loop)
    print("Starting Flask-SocketIO server on http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000)
