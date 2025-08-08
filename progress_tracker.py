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
