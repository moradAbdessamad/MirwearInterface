import time
import cv2
from gradio_client import Client, handle_file
from PIL import Image
import shutil
import os

# Initialize the camera
camera = cv2.VideoCapture(1)  # Use 0 for default camera, adjust if needed

# Function to capture image from camera
def capture_image():
    print("Get ready! Capturing image in 5 seconds...")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    ret, frame = camera.read()
    if ret:
        capture_path = 'captured_image.jpg'
        cv2.imwrite(capture_path, frame)
        print(f"Image captured and saved as {capture_path}")
        return capture_path
    else:
        print("Failed to capture image")
        return None

# Capture image for vton_img
vton_img_path = capture_image()

if vton_img_path:
    client = Client("Nouhaila-B1/MirrWearOOTD", hf_token="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")
    
    # Start time before the prediction
    start_time = time.time()

    # Run the prediction with new parameters
    result = client.predict(
        vton_img=handle_file(vton_img_path),
        garm_img=handle_file(r'D:\OSC\APIOOTD\00069_00.jpg'),    
        category="Upper-body", # category Literal['Upper-body', 'Lower-body', 'Dress'] Default: "Upper-body"   
        n_samples=1,
        n_steps=20,
        image_scale=2,
        seed=-1,
        api_name="/process_dc"
    )

    # End time after the prediction
    end_time = time.time()

    # Calculate the time taken
    time_taken = end_time - start_time
    print(f"Time taken for the request: {time_taken:.2f} seconds")

    # Check if the result is a list and contains a dictionary with the image path
    if isinstance(result, list) and len(result) > 0 and 'image' in result[0]:
        image_path = result[0]['image']  # Access the image path
        root_folder_path = r'D:\OSC\APIOOTD\content'  # Your root folder where app.py is located
        output_file_path = os.path.join(root_folder_path, 'generated_image.webp')  # Define the path to save the image

        # Check if the source image file exists
        if os.path.exists(image_path):
            # Copy the image to the root folder
            shutil.copy(image_path, output_file_path)
            print(f"Image successfully saved at: {output_file_path}")

            # Open and display the image using PIL
            image = Image.open(output_file_path)
            image.show()
        else:
            print(f"File not found: {image_path}")
    else:
        print(f"Unexpected result format: {result}")

    # Release the camera
    camera.release()
else:
    print("Failed to capture image. Exiting.")
