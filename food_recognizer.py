"""
This module provides functions for food recognition using a pre-trained
YOLOv3 model.
"""
import os
import cv2
import numpy as np
import requests


def download_model_files():
    """
    Downloads the YOLOv3-tiny model files if they are not already present.

    This function checks for the model directory and the necessary model files.
    If they don't exist, it downloads them from the official sources.
    """
    model_dir = "models"
    files_to_download = {
        "yolov3-tiny.weights": "https://pjreddie.com/media/files/yolov3-tiny.weights",
        "yolov3-tiny.cfg": "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg",
        "coco.names": "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names",
    }

    # Create model directory if it doesn't exist
    if not os.path.exists(model_dir):
        print(f"Creating directory: {model_dir}")
        os.makedirs(model_dir)

    # Download files if they don't exist
    for filename, url in files_to_download.items():
        filepath = os.path.join(model_dir, filename)
        if not os.path.exists(filepath):
            print(f"Downloading {filename}...")
            try:
                response = requests.get(url, stream=True)
                # Raise an exception for bad status codes (4xx or 5xx)
                response.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Successfully downloaded {filename}.")
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {filename}: {e}")
                # Clean up partially downloaded file if it exists
                if os.path.exists(filepath):
                    os.remove(filepath)
                # Re-raise the exception to notify the caller
                raise


def recognize_food(image: np.ndarray, confidence_threshold: float = 0.5, nms_threshold: float = 0.4):
    """
    Recognizes food items in an image using the YOLOv3-tiny model.

    This function first ensures the model files are available, then loads the
    model and performs object detection on the input image. It filters the
    detections to return only items that are classified as food.

    Args:
        image: The input image as a NumPy array.
        confidence_threshold: The minimum probability to filter weak detections.
        nms_threshold: The threshold for non-maxima suppression.

    Returns:
        A list of dictionaries, where each dictionary represents a detected
        food item and contains its label, confidence score, and bounding box.
    """
    # Ensure model files are downloaded before proceeding
    download_model_files()

    # Define paths to model files
    weights_path = os.path.join("models", "yolov3-tiny.weights")
    config_path = os.path.join("models", "yolov3-tiny.cfg")
    names_path = os.path.join("models", "coco.names")

    # Load class names
    with open(names_path, "r") as f:
        classes = [line.strip() for line in f.readlines()]

    # A predefined list of food-related classes from the COCO dataset
    food_items = {
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
        'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
        'hot dog', 'pizza', 'donut', 'cake'
    }

    # Load the pre-trained YOLO model
    net = cv2.dnn.readNet(weights_path, config_path)

    # Get the names of the output layers
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers().flatten()]

    # Prepare the image for the network
    height, width, _ = image.shape
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)

    # Pass the blob through the network
    net.setInput(blob)
    layer_outputs = net.forward(output_layers)

    # Process the outputs
    boxes = []
    confidences = []
    class_ids = []

    for output in layer_outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > confidence_threshold:
                # Scale bounding box coordinates back to the original image size
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                # Top-left corner coordinates
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Apply non-maxima suppression to remove redundant bounding boxes
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)

    # Filter detections to return only food items
    results = []
    if len(indexes) > 0:
        for i in indexes.flatten():
            label = str(classes[class_ids[i]])
            if label in food_items:
                x, y, w, h = boxes[i]
                confidence = confidences[i]
                results.append({
                    "label": label,
                    "confidence": confidence,
                    "box": [x, y, w, h]
                })

    return results
