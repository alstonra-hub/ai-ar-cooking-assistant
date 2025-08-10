import os
import cv2
import numpy as np
import requests

def download_model_files():
    """
    Downloads the YOLOv3-tiny model files if they are not already present.
    """
    model_dir = "models"
    files_to_download = {
        "yolov3-tiny.weights": "https://pjreddie.com/media/files/yolov3-tiny.weights",
        "yolov3-tiny.cfg": "https://github.com/pjreddie/darknet/blob/master/cfg/yolov3-tiny.cfg?raw=true",
        "coco.names": "https://github.com/pjreddie/darknet/blob/master/data/coco.names?raw=true",
    }

    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    for filename, url in files_to_download.items():
        filepath = os.path.join(model_dir, filename)
        if not os.path.exists(filepath):
            print(f"Downloading {filename}...")
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Successfully downloaded {filename}.")
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {filename}: {e}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise

def preprocess_image(image, alpha=1.2, beta=10):
    """
    Applies brightness and contrast adjustment.
    alpha: contrast control (1.0-3.0)
    beta: brightness control (0-100)
    """
    adjusted_image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return adjusted_image

def detect_food(image: np.ndarray, confidence_threshold: float = 0.3, nms_threshold: float = 0.4):
    """
    Detects food items in an image using the YOLOv3-tiny model.

    Args:
        image: The input image as a NumPy array.
        confidence_threshold: The minimum probability to filter weak detections.
        nms_threshold: The threshold for non-maxima suppression.

    Returns:
        A list of dictionaries, where each dictionary represents a detected
        food item and contains its label, confidence score, and bounding box.
    """
    download_model_files()

    # Apply preprocessing to the input image
    image = preprocess_image(image)

    weights_path = os.path.join("models", "yolov3-tiny.weights")
    config_path = os.path.join("models", "yolov3-tiny.cfg")
    names_path = os.path.join("models", "coco.names")

    with open(names_path, "r") as f:
        classes = [line.strip() for line in f.readlines()]

    food_items = {
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
        'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
        'hot dog', 'pizza', 'donut', 'cake'
    }

    net = cv2.dnn.readNet(weights_path, config_path)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers().flatten()]

    height, width, _ = image.shape
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)

    net.setInput(blob)
    layer_outputs = net.forward(output_layers)

    boxes = []
    confidences = []
    class_ids = []

    for output in layer_outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > confidence_threshold:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)

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


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Detect food items in an image using YOLOv3-tiny.'
    )
    parser.add_argument(
        '--test-image',
        type=str,
        required=True,
        help='Path to an image file for detection testing.'
    )

    args = parser.parse_args()

    if args.test_image:
        print(f"--- Running FoodDetector in Test Mode ---")
        print(f"Loading image from: {args.test_image}")

        try:
            image = cv2.imread(args.test_image)
            if image is None:
                print(f"\nError: Could not read the image file. Please check the path.")
            else:
                # Call the main detection function
                detected_food = detect_food(image)

                print(f"\n--- Detection Results ---")
                if detected_food:
                    for item in detected_food:
                        print(f"  - Found '{item['label']}' with {item['confidence']:.2f} confidence.")
                else:
                    print("  No food items were detected.")

        except cv2.error as e:
            print(f"\nERROR: A known OpenCV compatibility issue occurred.")
            print(f"       The YOLOv3 model weights are likely incompatible with this version of OpenCV.")
            print(f"       OpenCV Error Details: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
