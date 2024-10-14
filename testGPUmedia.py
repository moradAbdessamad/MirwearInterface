import mediapipe as mp
import cv2
import torch
import tkinter as tk 
from PIL import Image, ImageTk
import os 

root = tk.Tk()
root.title("The image and clothings test")

canvas = tk.Canvas(root, width=640, height=480)
canvas.pack()

# Check if CUDA is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Initialize the camera
cap = cv2.VideoCapture(0)

# Example PyTorch model (replace with your actual model)
model = torch.nn.Linear(2, 1).to(device)

def save_image():
    success, image = cap.read()
    if success:
        save_path = "./static/output"
        os.makedirs(save_path, exist_ok=True)
        file_name = f"captured_image_{len(os.listdir(save_path))}.jpg"
        cv2.imwrite(os.path.join(save_path, file_name), image)
        print(f"Image saved as {file_name}")

save_button = tk.Button(root, text="Save Image", command=save_image)
save_button.pack()

def update_frame():
    success, image = cap.read()
    if success:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
        # Flip the image horizontally for a mirrored view
        image = cv2.flip(image, 1)

        # Process the flipped image and find hands
        results = hands.process(image)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get the position of the index finger tip
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                
                # Convert the normalized coordinates to pixel coordinates
                h, w, c = image.shape
                cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                
                # Example: Use PyTorch model with GPU
                input_tensor = torch.tensor([cx, cy], dtype=torch.float32).to(device)
                output = model(input_tensor)
                
                # Draw a circle at the index finger tip
                cv2.circle(image, (cx, cy), 20, (255, 255, 255), 2)            
                
                # Display the PyTorch model output
                cv2.putText(image, f"Model output: {output.item():.2f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Convert the image to PhotoImage format for Tkinter
        image_tk = ImageTk.PhotoImage(Image.fromarray(image))
        
        # Update the canvas with the new image
        canvas.create_image(0, 0, anchor=tk.NW, image=image_tk)
        canvas.image = image_tk  # Keep a reference to prevent garbage collection

    # Schedule the next frame update
    root.after(10, update_frame)  # Update every 10ms for smoother display

# Start the frame update loop
update_frame()

# Run the Tkinter event loop
root.mainloop()

# Release resources
cap.release()
cv2.destroyAllWindows()