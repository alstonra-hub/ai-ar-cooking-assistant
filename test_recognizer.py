import cv2
from food_recognizer import recognize_food

def main():
    """
    Main function to test the food recognizer.

    This script loads a sample image, runs the food recognition function on it,
    and prints the results to the console.
    """
    image_path = "test_images/dog.jpg"

    # Load the image from the specified path
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Could not load image from path: {image_path}")
        return

    print(f"Running food recognition on '{image_path}'...")

    # Call the main recognition function
    food_items = recognize_food(image)

    # Print the detected items
    if food_items:
        print("\nDetected food items:")
        for item in food_items:
            print(f"  - Label: {item['label']}, "
                  f"Confidence: {item['confidence']:.2f}, "
                  f"BBox: {item['box']}")
    else:
        print("\nNo food items were detected in the image.")

if __name__ == "__main__":
    main()
