import cv2
from FoodDetector import detect_food

def main():
    """
    Main function to test the FoodDetector module.
    """
    image_path = "test_images/dog.jpg"

    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return

    print(f"Running food detection on '{image_path}'...")

    detected_items = detect_food(image)

    if detected_items:
        print("\nDetected food items:")
        for item in detected_items:
            print(f"  - Label: {item['label']}, "
                  f"Confidence: {item['confidence']:.2f}, "
                  f"BBox: {item['box']}")
    else:
        print("\nNo food items were detected in the image.")

if __name__ == "__main__":
    main()
