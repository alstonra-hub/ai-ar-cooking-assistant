"""
This module provides functions to track the progress of cooking tasks
using computer vision.
"""
import cv2
import numpy as np


def is_pasta_boiling(frame: np.ndarray, threshold: int = 500) -> bool:
    """
    Detects if pasta is boiling by analyzing a single frame from a camera feed.

    This function determines if pasta is boiling by detecting the level of
    turbulence and bubbles in the water. It does this by converting the frame to
    grayscale, applying a blur to reduce noise, and then using Canny edge
    detection to find edges. The number of contours found in the frame is
    compared against a threshold to decide if the water is boiling.

    Args:
        frame: A single frame from a video feed, represented as a NumPy array.
        threshold: The minimum number of contours to detect before considering
                   the pasta to be boiling. This value may need to be tuned
                   based on the specific camera setup and conditions.

    Returns:
        True if the number of contours exceeds the threshold (indicating boiling),
        False otherwise.
    """
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply a Gaussian blur to reduce noise and improve edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Use Canny edge detection to find edges in the frame
    edges = cv2.Canny(blurred, 50, 150)

    # Find contours in the edge-detected image
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # If the number of contours is above the threshold, we assume boiling
    return len(contours) > threshold


def get_average_color(image, box):
    """
    Calculates the average BGR color within a given bounding box.

    Args:
        image: The source image.
        box: A tuple (x, y, w, h) representing the bounding box.

    Returns:
        A numpy array representing the average BGR color.
    """
    x, y, w, h = [int(v) for v in box]
    roi = image[y:y+h, x:x+w]
    if roi.size == 0:
        return np.array([0, 0, 0])
    average_color = np.mean(roi, axis=(0, 1))
    return average_color


class FoodItemTracker:
    """
    Tracks the cooking state of a single food item based on color changes over time.
    """

    # This threshold determines how much the color must change to be considered "cooked".
    # It is an empirical value and may require tuning for specific lighting and food.
    COLOR_CHANGE_THRESHOLD = 50.0

    def __init__(self, item_id, initial_box, initial_frame):
        self.id = item_id
        self.box = initial_box
        self.initial_color = get_average_color(initial_frame, initial_box)
        self.current_color = self.initial_color
        self.state = "raw"  # Initial cooking state
        self.state_changed_this_frame = False

    def update(self, new_box, current_frame):
        """
        Updates the tracker with a new frame and bounding box, and checks for a state change.

        Args:
            new_box: The new bounding box of the item.
            current_frame: The current video frame.
        """
        self.box = new_box
        self.current_color = get_average_color(current_frame, new_box)
        self.state_changed_this_frame = False

        # We only transition from "raw" to "cooked". No further changes.
        if self.state == "raw":
            # Calculate the Euclidean distance in the BGR color space
            color_distance = np.linalg.norm(self.current_color - self.initial_color)

            if color_distance > self.COLOR_CHANGE_THRESHOLD:
                self.state = "cooked"
                self.state_changed_this_frame = True
                print(f"INFO: Food item {self.id} has changed state to 'cooked'.")
