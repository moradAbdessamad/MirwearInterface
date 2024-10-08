from flask import Flask, Response, render_template, url_for, redirect, session, jsonify, send_file
import threading
from flask_socketio import SocketIO, emit
import cv2
import mediapipe as mp
import time
import os
from groq import Groq
import json
import datetime
import re
import qrcode
import io
from gradio_client import Client, handle_file
from PIL import Image
import shutil
import os
import asyncio
from gradio_client import Client, handle_file
import base64
from dotenv import load_dotenv
import torch
from ultralytics import YOLO


app = Flask(__name__)
socketio = SocketIO(app)
size_capture_done = False

load_dotenv()

hf_token = os.getenv("HF_TOKEN")

# Initialize the Groq client with your API key
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# Add camera_index variable
camera_index = 0  # Default to first camera, change as needed

selected_items = {'option1_1': None, 'option1_2': None, 'option1_3': None}

hover_start_time = {}
hover_duration = 1  # Duration to hover in seconds

current_category = None
current_items = None
request_in_progress = None

output_folder = r'D:\OSC\MirwearInterface\static\output'
folder_path = r"D:\OSC\MirwearInterface\static\output"


def check_user_in_outline_v1():
    cap = cv2.VideoCapture(camera_index)
    start_time = None
    capturing = False
    outline_image = cv2.imread('static/Cloths/image.png', -1)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame_h, frame_w, _ = frame.shape
        outline_resized = cv2.resize(outline_image, (frame_w, frame_h))

        alpha_outline = outline_resized[:, :, 3] / 255.0
        for c in range(0, 3):
            frame[:, :, c] = outline_resized[:, :, c] * alpha_outline + frame[:, :, c] * (1 - alpha_outline)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            nose = results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
            print("the landamrsk");
            print("The landmarks of the nose ")
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]

            if (0.4 < nose.x < 0.6) and (0.4 < nose.y < 0.6) and (0.3 < left_shoulder.x < 0.5) and (0.3 < right_shoulder < 0.7):
                if start_time is None:
                    start_time = time.time()
                else:
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= 5:
                        capturing = True
                        break

            else:
                start_time = None

        rett, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
    if capturing:
        global size_capture_done
        size_capture_done = True
        socketio.emit('size_capture_done', {'status': 'completed'})


@socketio.on('button_hover_with_window_size')
def handle_button_hover_with_window_size(data):
    button = data['button']
    window_size = data['windowSize']
    print(f"Button hover: {button}")
    print(f"Window size: Width: {window_size['width']}, Height: {window_size['height']}")
    global frame_width, frame_height
    frame_width, frame_height = window_size['width'], window_size['height']

@socketio.on('button_positions')
def handle_button_positions(data):
    global buttons
    buttons = {}
    for button_id, coords in data.items():
        buttons[button_id] = {
            'top_left': (int(coords['top_left']['x']), int(coords['top_left']['y'])),
            'bottom_right': (int(coords['bottom_right']['x']), int(coords['bottom_right']['y']))
        }
    # print("Updated button positions:", buttons)

    
buttons = {
    'Top': {'top_left': (9, 208), 'bottom_right': (112, 312)},
    'Bottom': {'top_left': (9, 318), 'bottom_right': (112, 422)},
    'Foot': {'top_left': (9, 428), 'bottom_right': (112, 532)},
    'option1_1': {'top_left': (1329, 156), 'bottom_right': (1482, 309)},
    'option1_2': {'top_left': (1329, 316), 'bottom_right': (1482, 469)},
    'option1_3': {'top_left': (1329, 476), 'bottom_right': (1482, 629)},
    'Changedown': {'top_left': (1386, 111), 'bottom_right': (1421, 146)},
    'Recommend': {'top_left': (701, 593), 'bottom_right': (834, 637)}
}


request_in_progress_flag = None
capture_requested_send = False
CAPTURED_IMAGE_PATH = r'D:\OSC\MirwearInterface\static\imagesformcam\latest_capture.jpg'
CROPPED_IMAGE_PATH = r'D:\OSC\MirwearInterface\static\models\cropped_person_image.jpg'

def check_button_hover(finger_tip_coords):
    global hover_start_time
    global current_category
    global current_items
    global request_in_progress_flag

    if finger_tip_coords:
        for button, coords in buttons.items():
            if (coords['top_left'][0] <= finger_tip_coords['x'] <= coords['bottom_right'][0] and
                coords['top_left'][1] <= finger_tip_coords['y'] <= coords['bottom_right'][1]):
                
                if button not in hover_start_time:
                    hover_start_time[button] = time.time()
                elif time.time() - hover_start_time[button] >= hover_duration:
                    if button in ['option1_1', 'option1_2', 'option1_3']:
                        print(f"{button} is hovered")
                        print(f"current_category: {current_category}, current_items: {current_items}")
                        if current_category and current_items:
                            selected_item = select_item_by_option(current_items, button)
                            print(f"Selected item: {selected_item}")
                            print(f"request_in_progress_flag: {request_in_progress_flag}")
                            if selected_item and not request_in_progress_flag:
                                request_in_progress_flag = True
                                threading.Thread(target=send_request, args=(button, selected_item)).start()
                            else:
                                print("Not sending request. Selected item or request_in_progress_flag condition not met.")
                        else:
                            print("Not sending request. current_category or current_items is None.")
                    else:
                        message = {'button': button}
                        print(f"Emitting message: {message}")
                        socketio.emit('button_hover', message)
                    hover_start_time.pop(button)
            else:
                if button in hover_start_time:
                    hover_start_time.pop(button)

capture_requested_recommand = False

#don't forget to change the w and h to align with the window 
# and also change it in the html code 
frame_width, frame_height = 1080, 1920  # Default values

def gen_frames():
    global camera
    global capture_requested_recommand
    global frame_width, frame_height
    camera = cv2.VideoCapture(camera_index)
    
    mp_hands = mp.solutions.hands
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame = cv2.flip(frame, 1)
            
            # Always resize the frame to match the window size
            frame = cv2.resize(frame, (frame_width, frame_height))
            
            # Draw buttons on the frame
            for button, coords in buttons.items():
                cv2.rectangle(frame,
                            coords['top_left'],
                            coords['bottom_right'],
                            (255, 255, 255))
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                   
            results = hands.process(frame_rgb)
            finger_tip_coords = None

            if results.multi_hand_landmarks:
                # Process only the first detected hand for finger tip
                hand_landmarks = results.multi_hand_landmarks[0]
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                h, w, c = frame.shape
                cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                finger_tip_coords = {'x': cx, 'y': cy}
                # print((cx, cy))
                cv2.circle(frame, (cx, cy), 20, (255, 255, 255), 2)
                check_button_hover(finger_tip_coords)

            if capture_requested_recommand:
                input_folder = r'D:\OSC\MirwearInterface\static\imagesformcam'
                os.makedirs(input_folder, exist_ok=True)
                capture_path = os.path.join(input_folder, 'latest_capture.jpg')
                cv2.imwrite(capture_path, frame)
                print(f"Image captured and saved to {capture_path}")
                capture_requested_recommand = False
                socketio.emit('image_captured', {'message': 'Image captured successfully'})

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
    camera.release()


capture_folder = r'D:\OSC\MirwearInterface\static\imagesformcam'

def capture_and_crop_image_for_send():
    global capture_requested_send, camera
    # Emit a message to ask the user to adjust their pose
    socketio.emit('pose_adjustment_needed_send', {'message': 'Please adjust your pose for better capture'})
    
    # Wait for 3 seconds
    time.sleep(3)
    
    # Capture the image
    success, frame = camera.read()
    if success:
        cv2.imwrite(CAPTURED_IMAGE_PATH, frame)
        print(f"Image captured and saved to {CAPTURED_IMAGE_PATH}")
    else:
        print("Failed to capture image")
        return
    
    # Crop the image
    crop_person_for_send(CAPTURED_IMAGE_PATH, CROPPED_IMAGE_PATH)

def crop_person_for_send(input_path, output_path):
    # Set the device to CPU
    device = torch.device('cpu')

    # Load the YOLOv8 model and run it on CPU
    model = YOLO('yolov8n.pt').to(device)

    # Load the image
    image = cv2.imread(input_path)

    if image is None:
        print(f"Error: Could not load image from {input_path}")
        return

    # Get image dimensions
    image_height, image_width, _ = image.shape

    # Run YOLOv8 inference on the CPU
    results = model(image)

    # Process the results
    for result in results:
        for box in result.boxes:
            # Class ID 0 is 'person' in YOLO models
            if int(box.cls) == 0:
                # Get the bounding box coordinates
                x_min, y_min, x_max, y_max = map(int, box.xyxy[0])

                # Apply padding (40 pixels) and ensure coordinates stay within image boundaries
                padding = 40
                x_min = max(x_min - padding, 0)
                y_min = max(y_min - padding, 0)
                x_max = min(x_max + padding, image_width)
                y_max = min(y_max + padding, image_height)

                # Crop the image to the detected person with padding
                cropped_image = image[y_min:y_max, x_min:x_max]

                # Save the cropped image
                cv2.imwrite(output_path, cropped_image)
                print(f"Cropped image saved to {output_path}")

                # We only need to process the first person detected, so we can break here
                break

    print("Person cropping completed.")

def send_request(button, selected_item):
    global request_in_progress_send
    global request_in_progress_flag  # Added this line
    print(f"send_request called with button: {button}, selected_item: {selected_item}")
    try:
        # Run the capture and crop process
        capture_and_crop_image_for_send()
        
        # Define the paths and parameters based on the selected_item
        vton_img_path = CROPPED_IMAGE_PATH
        garm_img_path = os.path.join(r'D:\OSC\MirwearInterface\static\ClothsImageTest', selected_item)  
        output_folder = r'D:\OSC\MirwearInterface\static\output'  

        print(f"vton_img_path: {vton_img_path}")
        print(f"garm_img_path: {garm_img_path}")
        print(f"output_folder: {output_folder}")

        # Determine the category based on the selected item
        with open(r'D:\OSC\MirwearInterface\static\JSONstyles\itemsByType.json', 'r') as f:
            items_by_type = json.load(f)
        
        if selected_item in items_by_type.get('top', {}):
            category = 'Upper-body'
        elif selected_item in items_by_type.get('bottom', {}):
            category = 'Lower-body'
        elif selected_item in items_by_type.get('foot', {}):
            category = 'Dress'
        else:
            category = 'Upper-body'  

        print(f"Sending request for {button} with item: {selected_item}, category: {category}")
        
        # Emit a message to inform the client that the request is being sent
        socketio.emit('outfit_image_ready', {'status': 'sending', 'message': 'Request is being sent'})
        
        # Run the appropriate function based on the category
        if category == 'Lower-body':
            print("Sending request with send_request_and_save function")
            send_request_and_save(vton_img_path, garm_img_path, output_folder, category)
        else:
            print("Sending request with send_request_and_save_for_upperbody function")
            send_request_and_save_for_upperbody(vton_img_path, garm_img_path, output_folder)
        
        print("Request completed")
        request_in_progress_send = False
        request_in_progress_flag = False
        
        output_file_path = os.path.join(output_folder, 'generated_image.webp')
        if os.path.exists(output_file_path):
            print(f"Generated image found at: {output_file_path}")
            # Emit a message to inform the client that the image is ready
            socketio.emit('outfit_image_ready', {'status': 'complete', 'path': output_file_path})
            
            # Call monitor_folder function to emit the new image
            monitor_folder(output_folder)
        else:
            print(f"Generated image not found at: {output_file_path}")
            socketio.emit('outfit_image_ready', {'status': 'error', 'message': 'Generated image not found'})
    
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        socketio.emit('outfit_image_ready', {'status': 'error', 'message': str(e)})
    
    finally:
        request_in_progress_send = False
        request_in_progress_flag = False  # This now correctly modifies the global variable


def send_request_and_save(vton_img_path, garm_img_path, output_folder, category):
    client = Client("Nouhaila-B1/MirrWearOOTD", hf_token=hf_token)

    # Start time before the prediction
    start_time = time.time()

    # Run the prediction
    result = client.predict(
        vton_img=handle_file(vton_img_path),
        garm_img=handle_file(garm_img_path),
        category=category,  # Use the determined category
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
        output_file_path = os.path.join(output_folder, 'generated_image.webp')  # Define the path to save the image

        # Check if the source image file exists
        if os.path.exists(image_path):
            # Copy the image to the output folder
            shutil.copy(image_path, output_file_path)
            print(f"Image successfully saved at: {output_file_path}")

            # Open and display the image using PIL (optional)
            # image = Image.open(output_file_path)
            # image.show()

            # Wait for 1 second
            time.sleep(1)

            # Emit a message in the websocket with the relative image path
            relative_path = os.path.relpath(output_file_path, start=os.getcwd())
            socketio.emit('outfit_image_ready_in_request', {'status': 'complete', 'path': relative_path})
            print('The relative path : ')
            print(relative_path)
        else:
            print(f"File not found: {image_path}")
            socketio.emit('outfit_image_ready_in_request', {'status': 'error', 'message': 'Generated image not found'})
    else:
        print(f"Unexpected result format: {result}")
        socketio.emit('outfit_image_ready_in_request', {'status': 'error', 'message': 'Unexpected result format'})



def send_request_and_save_for_upperbody(vton_img_path, garm_img_path, output_folder):
    client = Client("Nouhaila-B1/MirrWearOOTD", hf_token=hf_token)

    # Start time before the prediction
    start_time = time.time()

    # Run the prediction
    result = client.predict(
        vton_img=handle_file(vton_img_path),
        garm_img=handle_file(garm_img_path),
        n_samples=1,
        n_steps=20,
        image_scale=2,
        seed=-1,
        api_name="/process_hd"
    )

    # End time after the prediction
    end_time = time.time()

    # Calculate the time taken
    time_taken = end_time - start_time
    print(f"Time taken for the request: {time_taken:.2f} seconds")

    # Check if the result is a list and contains a dictionary with the image path
    if isinstance(result, list) and len(result) > 0 and 'image' in result[0]:
        image_path = result[0]['image']  # Access the image path
        output_file_path = os.path.join(output_folder, 'generated_image.webp')  # Define the path to save the image

        # Check if the source image file exists
        if os.path.exists(image_path):
            # Copy the image to the output folder
            shutil.copy(image_path, output_file_path)
            print(f"Image successfully saved at: {output_file_path}")

            # Wait for 1 second
            time.sleep(1)

            # Emit a message in the websocket with the relative image path
            relative_path = os.path.relpath(output_file_path, start=os.getcwd())
            socketio.emit('outfit_image_ready_in_request', {'status': 'complete', 'path': relative_path})
            print('The relative path : ')
            print(relative_path)
        else:
            print(f"File not found: {image_path}")
            socketio.emit('outfit_image_ready_in_request', {'status': 'error', 'message': 'Generated image not found'})
    else:
        print(f"Unexpected result format: {result}")
        socketio.emit('outfit_image_ready_in_request', {'status': 'error', 'message': 'Unexpected result format'})

# button_season = {
#     'winter': {'top_left': (130, 225), 'bottom_right': (200, 251)},
#     'summer': {'top_left': (130, 226), 'bottom_right': (200, 295)},
#     'spring': {'top_left': (130, 313), 'bottom_right': (200, 336)},
#     'fall': {'top_left': (130, 352), 'bottom_right': (200, 376)},
# }

@socketio.on('button_positions_recommand')
def handle_button_positions(button_positions):
    # print('Received button positions:', button_positions)

    # Update buttons_recommand with received positions
    for button, coords in button_positions.items():
        if button in buttons_recommand:
            buttons_recommand[button]['top_left'] = (
                int(coords['top_left']['x']),
                int(coords['top_left']['y'])
            )
            buttons_recommand[button]['bottom_right'] = (
                int(coords['bottom_right']['x']),
                int(coords['bottom_right']['y'])
            )

    # Update arrow_recommand with received positions
    for button, coords in button_positions.items():
        if button in arrow_recommand:
            arrow_recommand[button]['top_left'] = (
                int(coords['top_left']['x']),
                int(coords['top_left']['y'])
            )
            arrow_recommand[button]['bottom_right'] = (
                int(coords['bottom_right']['x']),
                int(coords['bottom_right']['y'])
            )

    # Emit a response if needed
    emit('response', {'status': 'success', 'message': 'Button positions updated'})

buttons_recommand = {
    'Season': {'top_left': (175, 114), 'bottom_right': (233, 126)},
    'winter': {'top_left': (175, 132), 'bottom_right': (233, 137)},
    'summer': {'top_left': (175, 142), 'bottom_right': (233, 147)},
    'spring': {'top_left': (175, 152), 'bottom_right': (233, 157)},
    'fall': {'top_left': (175, 162), 'bottom_right': (233, 167)},

    'Gender': {'top_left':  (252, 114), 'bottom_right': (308, 126)},
    'male': {'top_left': (252, 132), 'bottom_right': (308, 137)},
    'female': {'top_left': (252, 142), 'bottom_right': (308, 147)},
    'unisex': {'top_left': (252, 152), 'bottom_right': (308, 157)},
    'kids': {'top_left': (252, 162), 'bottom_right': (308, 167)},

    'Color': {'top_left': (329, 114), 'bottom_right': (383, 126)},
    'red': {'top_left': (329, 132), 'bottom_right': (383, 137)},
    'blue': {'top_left': (329, 142), 'bottom_right': (383, 147)},
    'green': {'top_left': (329, 152), 'bottom_right': (383, 157)},
    'yellow': {'top_left': (329, 162), 'bottom_right': (383, 167)},

    'Style': {'top_left':  (406, 114), 'bottom_right': (458, 126)},
    'casual': {'top_left': (406, 132), 'bottom_right': (458, 137)},
    'formal': {'top_left': (406, 142), 'bottom_right': (458, 147)},
    'sport': {'top_left': (406, 152), 'bottom_right': (458, 157)},
    'vintage': {'top_left': (406, 162), 'bottom_right': (458, 167)},

    'recommand': {'top_left': (152, 431), 'bottom_right': (362, 460)},
}

arrow_recommand = {
    'topLeft': {'top_left': (118, 191), 'bottom_right': (155, 228)},
    'topright': {'top_left': (481, 188), 'bottom_right': (518, 225)},

    'bottomLeft': {'top_left': (483, 226), 'bottom_right': (513, 256)},
    'bottomRight': {'top_left': (130, 225), 'bottom_right': (160, 255)},
    
    'shoesLeft': {'top_left': (121, 255), 'bottom_right': (158, 292)},
    'shoesRight': {'top_left': (479, 258), 'bottom_right': (516, 295)},
  
    'shoffle': {'top_left': (574, 288), 'bottom_right': (594, 308)},

    'refresh': {'top_left': (274, 431), 'bottom_right': (362, 460)},
    
    # (552, 191) (620, 217)
    'topRecommandItem': {'top_left': (552, 191), 'bottom_right': (620, 217)}, 
    'bottomRecommandItem': {'top_left':  (552, 223), 'bottom_right': (624, 251)},
    'footRecommandItem': {'top_left': (552, 260), 'bottom_right': (622, 283)},
}


hover_start_time_recommand = {}
hover_duration = 0.5  # 1 second hover duration
current_recommand_mode = 'buttons'
selected_recommanded_items = {'item': None}
request_in_progress = False
capture_requested = False


def check_button_hover_recommand(finger_tip_coords):
    global hover_start_time_recommand
    global current_recommand_mode
    global selected_recommanded_items
    global displayed_images
    global request_in_progress

    coords_to_check = buttons_recommand if current_recommand_mode == 'buttons' else arrow_recommand

    if finger_tip_coords:
        for button, coords in coords_to_check.items():
            if (coords['top_left'][0] <= finger_tip_coords['x'] <= coords['bottom_right'][0] and
                coords['top_left'][1] <= finger_tip_coords['y'] <= coords['bottom_right'][1]):
                
                if button not in hover_start_time_recommand:
                    hover_start_time_recommand[button] = time.time()
                elif time.time() - hover_start_time_recommand[button] >= hover_duration:
                    message = {'button_recommand': button}
                    print(f"Emitting message: {message}")
                    socketio.emit('button_hover_recommand', message)
                    hover_start_time_recommand.pop(button)
                    
                    if button in ['topRecommandItem', 'bottomRecommandItem', 'footRecommandItem']:
                        index = ['topRecommandItem', 'bottomRecommandItem', 'footRecommandItem'].index(button)
                        if index < len(displayed_images):
                            selected_recommanded_items['item'] = os.path.basename(displayed_images[index])
                            print(f"Selected item: {selected_recommanded_items['item']}")
                            
                            # Send the request asynchronously
                            if not request_in_progress:
                                request_in_progress = True
                                threading.Thread(target=send_request_recommand, args=(button, selected_recommanded_items['item'])).start()
                            else:
                                print("Not sending request. request_in_progress is True.")
                        else:
                            print(f"Index {index} is out of range for displayed_images: {displayed_images}")
                    
                    return
            else:
                if button in hover_start_time_recommand:
                    hover_start_time_recommand.pop(button)


def gen_frames_for_recommandation():
    global camera_recommand
    global selected_recommanded_items, capture_requested
    camera = cv2.VideoCapture(0)
    camera_recommand = camera
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (frame_width, frame_height))

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Draw rectangles based on the received positions
            if current_recommand_mode == 'buttons':
                for button, coords in buttons_recommand.items():
                    cv2.rectangle(frame, 
                                coords['top_left'], 
                                coords['bottom_right'], 
                                (255, 255, 255), 1)  # White rectangle with thickness of 1

            if current_recommand_mode == 'arrows':
                for button, coords in arrow_recommand.items():
                    cv2.rectangle(frame,
                                coords['top_left'],
                                coords['bottom_right'],
                                (255, 255, 255), 1)      
                    
            # print("The frame has been finish drowing")
                
            results = hands.process(frame_rgb)
            finger_tip_coords = None

            if results.multi_hand_landmarks:
                # Process only the first detected hand
                hand_landmarks = results.multi_hand_landmarks[0]
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                h, w, _ = frame.shape
                cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                finger_tip_coords = {'x': cx, 'y': cy}
                # print("the finger tip index")
                # print((cx, cy))
                cv2.circle(frame, (cx, cy), 20, (255, 255, 255), 2)
                check_button_hover_recommand(finger_tip_coords)

            if capture_requested:
                input_folder = r'D:\OSC\MirwearInterface\static\imagesformcam'
                os.makedirs(input_folder, exist_ok=True)
                capture_path = os.path.join(input_folder, 'latest_capture.jpg')
                cv2.imwrite(capture_path, frame)
                print(f"Image captured and saved to {capture_path}")
                capture_requested = False
                socketio.emit('image_captured', {'message': 'Image captured successfully'})

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    camera.release()

camera_recommand = None
CAPTURED_IMAGE_PATH = r'D:\OSC\MirwearInterface\static\imagesformcam\latest_capture.jpg'
CROPPED_IMAGE_PATH = r'D:\OSC\MirwearInterface\static\models\cropped_person_image.jpg'

async def capture_and_crop_image():
    global camera_recommand
    # Emit a message to ask the user to adjust their pose
    socketio.emit('pose_adjustment_needed', {'message': 'Please adjust your pose for better capture'})
    
    # Wait for 3 seconds
    await asyncio.sleep(3)
    
    # Capture the image
    success, frame = camera_recommand.read()
    if success:
        # Save the captured frame to the specified path
        cv2.imwrite(CAPTURED_IMAGE_PATH, frame)
        print(f"Image captured and saved to {CAPTURED_IMAGE_PATH}")
    else:
        print("Failed to capture image")
        return

    # Crop the captured image asynchronously
    await asyncio.to_thread(crop_person_from_image)



def send_request_recommand(button, selected_item):
    global request_in_progress
    print(f"send_request_recommand called with button: {button}, selected_item: {selected_item}")
    try:
        # Ensure camera_recommand is valid
        if camera_recommand is None:
            print("Error: camera_recommand is not initialized.")
            raise Exception("Camera not initialized")

        # Run the capture and crop process asynchronously
        print("Starting capture_and_crop_image")
        asyncio.run(capture_and_crop_image())
        print("Finished capture_and_crop_image")
        
        # Define the paths and parameters based on the selected_item
        models_folder = r'D:\OSC\MirwearInterface\static\models'
        # Ensure that there is at least one jpg file in models_folder
        jpg_files = [f for f in os.listdir(models_folder) if f.endswith('.jpg')]
        if not jpg_files:
            raise Exception(f"No jpg files found in {models_folder}")
        vton_img_path = max([os.path.join(models_folder, f) for f in jpg_files], key=os.path.getmtime)
        garm_img_path = os.path.join(r'D:\OSC\MirwearInterface\static\ClothsImageTest', selected_item)  
        output_folder = r'D:\OSC\MirwearInterface\static\output'  

        print(f"vton_img_path: {vton_img_path}")
        print(f"garm_img_path: {garm_img_path}")
        print(f"output_folder: {output_folder}")

        # Determine the category based on the selected item
        with open(r'D:\OSC\MirwearInterface\static\JSONstyles\itemsByType.json', 'r') as f:
            items_by_type = json.load(f)
        
        if selected_item in items_by_type.get('top', {}):
            category = 'Upper-body'
        elif selected_item in items_by_type.get('bottom', {}):
            category = 'Lower-body'
        elif selected_item in items_by_type.get('foot', {}):
            category = 'Dress'
        else:
            category = 'Upper-body'  

        print(f"Sending request for {button} with item: {selected_item}, category: {category}")
        
        # Emit a message to inform the client that the request is being sent
        socketio.emit('outfit_image_ready_recommand', {'status': 'sending', 'message': 'Request is being sent'})
        
        # Run the send_request_and_save function
        if category == 'Lower-body':
            print("Sending request with send_request_and_save function")
            send_request_and_save(vton_img_path, garm_img_path, output_folder, category)
        else:
            print("Sending request with send_request_and_save_for_upperbody function")
            send_request_and_save_for_upperbody(vton_img_path, garm_img_path, output_folder)      

        print("Request completed")
        request_in_progress = False
        
        output_file_path = os.path.join(output_folder, 'generated_image.webp')
        if os.path.exists(output_file_path):
            print(f"Generated image found at: {output_file_path}")
            # Emit a message to inform the client that the image is ready
            socketio.emit('outfit_image_ready_recommand', {'status': 'complete', 'path': output_file_path})
            
            # Call monitor_folder function to emit the new image
            monitor_folder(output_folder)
        else:
            print(f"Generated image not found at: {output_file_path}")
            socketio.emit('outfit_image_ready_recommand', {'status': 'error', 'message': 'Generated image not found'})
    
    except Exception as e:
        print(f"An error occurred in send_request_recommand: {e}")
        import traceback
        traceback.print_exc()
        socketio.emit('outfit_image_ready_recommand', {'status': 'error', 'message': str(e)})
    
    finally:
        print("Resetting request_in_progress to False")
        request_in_progress = False


def crop_person_from_image():
    # Set the device to CPU
    device = torch.device('cpu')

    # Load the YOLOv8 model and run it on CPU
    model = YOLO('yolov8n.pt').to(device)

    # Define input and output folders
    input_folder = r'D:\OSC\MirwearInterface\static\imagesformcam'
    output_folder = r'D:\OSC\MirwearInterface\static\models'

    # Get the latest image from the input folder
    latest_image = max([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith('.jpg')], key=os.path.getmtime)

    # Load the image
    image = cv2.imread(latest_image)

    if image is None:
        print(f"Error: Could not load image from {latest_image}")
        return

    # Get image dimensions
    image_height, image_width, _ = image.shape

    # Run YOLOv8 inference on the CPU
    results = model(image)

    # Process the results
    for result in results:
        for box in result.boxes:
            # Class ID 0 is 'person' in YOLO models
            if int(box.cls) == 0:
                # Get the bounding box coordinates
                x_min, y_min, x_max, y_max = map(int, box.xyxy[0])

                # Apply padding (20 pixels) and ensure coordinates stay within image boundaries
                padding = 40
                x_min = max(x_min - padding, 0)
                y_min = max(y_min - padding, 0)
                x_max = min(x_max + padding, image_width)
                y_max = min(y_max + padding, image_height)

                # Crop the image to the detected person with padding
                cropped_image = image[y_min:y_max, x_min:x_max]

                # Create the output folder if it doesn't exist
                os.makedirs(output_folder, exist_ok=True)

                # Define the output path for the cropped image
                save_path = os.path.join(output_folder, 'cropped_person_image.jpg')

                # Save the cropped image
                cv2.imwrite(save_path, cropped_image)
                print(f"Cropped image saved to {save_path}")

                # We only need to process the first person detected, so we can break here
                break

    print("Person cropping completed.")



@socketio.on('displayed_images')
def handle_displayed_images(images):
    global displayed_images
    global selected_recommanded_items
    print(f"Currently displayed images: {images}")
    
    # Update the global displayed_images list with the new images
    displayed_images = images
    print(f"Updated displayed images: {displayed_images}")
    
    # Check if any of the recommendation items are being hovered
    for button, category in [('topRecommandItem', 'top'), ('bottomRecommandItem', 'bottom'), ('footRecommandItem', 'foot')]:
        if button in hover_start_time_recommand:
            index = ['top', 'bottom', 'foot'].index(category)
            selected_recommanded_items['item'] = os.path.basename(displayed_images[index])  # Store only the item name
            
            print(f"Selected {button}: {selected_recommanded_items['item']}")
            break  # Exit after processing one hover to avoid multiple selections



outline_points = {
    'nose': {'x': 300, 'y': 200, 'threshold': 50},
}

def is_within_circle(point_x, point_y, circle_x, circle_y, radius=20):
    return (point_x - circle_x) ** 2 + (point_y - circle_y) ** 2 <= radius ** 2

def gen_frames_for_outline():
    cam = cv2.VideoCapture(camera_index)
    
    if not cam.isOpened():
        print("Error: Could not open video source.")
        yield b''
        return

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break
        
        frame = cv2.flip(frame, 1)
        frame_h, frame_w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            nose = results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
            nose_x, nose_y = int(nose.x * frame_w), int(nose.y * frame_h)
            nose_check = is_within_circle(nose_x, nose_y, outline_points['nose']['x'], outline_points['nose']['y'], outline_points['nose']['threshold'])
            if nose_check:
                print("User is standing correctly in the outline.")
                socketio.emit('user_status', {'status': 'standing_still'})
            else:
                print("User is not standing still in the outline.")
                socketio.emit('user_status', {'status': 'not_standing_still'})
        else:
            print("Pose landmarks not detected.")
            socketio.emit('user_status', {'status': 'no_landmarks'})
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    cam.release()
    cv2.destroyAllWindows()
    yield b''



# buttons_recommand = {
#     'Season': {'top_left': (102, 167), 'bottom_right': (186, 203)},
#     'Gender': {'top_left': (226, 160), 'bottom_right': (305, 198)},
#     'Color': {'top_left': (345, 160), 'bottom_right': (419, 203)},
#     'Style': {'top_left': (460, 161), 'bottom_right': (535, 204)},

#     'winter': {'top_left': (130, 225), 'bottom_right': (200, 251)},
#     'summer': {'top_left': (130, 265), 'bottom_right': (200, 295)},
#     'spring': {'top_left': (130, 313), 'bottom_right': (200, 336)},
#     'fall': {'top_left': (130, 352), 'bottom_right': (200, 376)},

#     'male': {'top_left': (234, 226), 'bottom_right': (304, 251)},
#     'female': {'top_left': (234, 265), 'bottom_right': (304, 295)},
#     'unisex': {'top_left': (234, 310), 'bottom_right': (304, 336)},
#     'kids': {'top_left': (234, 352), 'bottom_right': (304, 376)},

#     'red': {'top_left': (334, 226), 'bottom_right': (412, 251)},
#     'blue': {'top_left': (334, 265), 'bottom_right': (412, 295)},
#     'green': {'top_left': (334, 310), 'bottom_right': (412, 336)},
#     'yellow': {'top_left': (334, 352), 'bottom_right': (412, 376)},

#     'casual': {'top_left': (442, 226), 'bottom_right': (512, 251)},
#     'formal': {'top_left': (442, 265), 'bottom_right': (512, 295)},
#     'sport': {'top_left': (442, 310), 'bottom_right': (512, 336)},
#     'vintage': {'top_left': (442, 352), 'bottom_right': (512, 376)},

#     'recommand': {'top_left': (274, 431), 'bottom_right': (362, 460)},

#     'shoffle': {'top_left': (548, 428), 'bottom_right': (596, 476)}
# }
            



qr_buttons = {
    'qr_button1': {'top_left': (100, 100), 'bottom_right': (200, 200)},
    'qr_button2': {'top_left': (300, 300), 'bottom_right': (400, 400)},
}

def check_qrcode_button_hover(finger_tip_coords):
    # Example of how to check for hover
    for button, coords in qr_buttons.items():
        if (coords['top_left'][0] <= finger_tip_coords['x'] <= coords['bottom_right'][0] and
            coords['top_left'][1] <= finger_tip_coords['y'] <= coords['bottom_right'][1]):
            print(f"Hovering over {button}")

def gen_qrcode_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            for button, coords in qr_buttons.items():
                cv2.rectangle(frame,
                            coords['top_left'],
                            coords['bottom_right'],
                            (255, 255, 255))
                   
            results = hands.process(frame_rgb)
            finger_tip_coords = None

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    h, w, _ = frame.shape
                    cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                    finger_tip_coords = {'x': cx, 'y': cy}
                    cv2.circle(frame, (cx, cy), 20, (255, 255, 255), 2)
                    check_qrcode_button_hover(finger_tip_coords)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def select_item_by_option(items, option):
    # Define a mapping between options and their respective indices in the items list
    option_mapping = {
        'option1_1': 0,  # Select the first item
        'option1_2': 1,  # Select the second item
        'option1_3': 2   # Select the third item
    }

    # Check if the option is valid and there is a corresponding index in the items list
    if option in option_mapping:
        index = option_mapping[option]
        if index < len(items):
            selected_item = items[index]
            print(f"Selected item for {option}: {selected_item}")
            return selected_item
        else:
            print(f"No item available for {option}")
            return None
    else:
        print(f"Invalid option: {option}")
        return None


# Define the function
def send_request_and_save_test(vton_img_path, garm_img_path, output_folder, category):
    client = Client("Nouhaila-B1/MirrWearOOTD", hf_token="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")

    # Start time before the prediction
    start_time = time.time()

    # Run the prediction
    result = client.predict(
        vton_img=handle_file(vton_img_path),
        garm_img=handle_file(garm_img_path),
        n_samples=1,
        n_steps=20,
        image_scale=2,
        seed=-1,
        category=category,  # Pass the category to the API
        api_name="/process_hd"
    )

    # End time after the prediction
    end_time = time.time()

    # Calculate the time taken
    time_taken = end_time - start_time
    print(f"Time taken for the request: {time_taken:.2f} seconds")

    # Check if the result is a list and contains a dictionary with the image path
    if isinstance(result, list) and len(result) > 0 and 'image' in result[0]:
        image_path = result[0]['image']  # Access the image path
        output_file_path = os.path.join(output_folder, 'generated_image.webp')  # Define the path to save the image

        # Check if the source image file exists
        if os.path.exists(image_path):
            # Copy the image to the output folder
            shutil.copy(image_path, output_file_path)
            print(f"Image successfully saved at: {output_file_path}")

            # Open and display the image using PIL (optional)
            image = Image.open(output_file_path)
            image.show()
        else:
            print(f"File not found: {image_path}")
    else:
        print(f"Unexpected result format: {result}")


# the image send the last image in the folder to the web socket and handle this in js 
# also don't forget that the emit message in websokects to when the process is complete or no
def get_latest_image(folder_path):
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if files:
        latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
        return os.path.join(folder_path, latest_file)
    return None


def monitor_folder(folder_path):
    last_modified = 0
    while True:
        latest_image = get_latest_image(folder_path)
        if latest_image:
            current_modified = os.path.getmtime(latest_image)
            if current_modified > last_modified:
                last_modified = current_modified
                relative_path = os.path.relpath(latest_image, start=os.path.dirname(__file__))
                print("The new message is emited : ")
                print(relative_path)
                socketio.emit('try_on_result', {'path': relative_path})
        time.sleep(1)  # Check every second


# # Monitor the folder path
# @socketio.on('connect')
# def handle_connect():
#     threading.Thread(target=monitor_folder, args=(folder_path,), daemon=True).start()


@app.route('/video_feed_outline')
def video_feed_outline():
    return Response(gen_frames_for_outline(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/outline')
def outline():
    return render_template('outline.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed_recommandation')
def video_feed_recommandation():
    return Response(gen_frames_for_recommandation(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/recommandation')
def recommandation():
    return render_template('recommandation.html')

@app.route('/qrPage')
def qr_page():
    return render_template('qrPage.html')

@app.route('/video_feed_qr_code')
def video_feed_qr_code():
    return Response(gen_qrcode_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/generate_qr')
def generate_qr():
    # Data to encode
    data = "Hello from the Here"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create an image from the QR code instance
    img = qr.make_image(fill='black', back_color='white')

    # Save the image to a bytes buffer
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Send the image as a response
    return send_file(img_io, mimetype='image/png')



@app.route('/generate_cloths')
def generate_cloths():
        client = Client("levihsu/OOTDiffusion")

        # Run the prediction
        result = client.predict(
            vton_img=handle_file(r'D:\OSC\APIOOTD\00034_00.jpg'),
            garm_img=handle_file(r'D:\OSC\APIOOTD\00069_00.jpg'),
            n_samples=1,
            n_steps=20,
            image_scale=2,
            seed=-1,
            api_name="/process_hd"
        )

        # Check if the result is a list and contains a dictionary with the image path
        if isinstance(result, list) and len(result) > 0 and 'image' in result[0]:
            image_path = result[0]['image']  # Access the image path
            static_folder_path = os.path.join('static', 'images')  # Define static folder for images
            output_file_path = os.path.join(static_folder_path, 'generated_image.webp')  # Save in static/images folder
            
            # Create the folder if it doesn't exist
            if not os.path.exists(static_folder_path):
                os.makedirs(static_folder_path)
            
            # Check if the source image file exists
            if os.path.exists(image_path):
                # Copy the image to the static folder
                shutil.copy(image_path, output_file_path)
                print(f"Image successfully saved at: {output_file_path}")
                
                # Pass the image path to the template
                return render_template('display_image.html', image_file='images/generated_image.webp')
            else:
                return "File not found", 404
        else:
            return "Unexpected result format", 500



@app.route('/static/JSONstyles/itemsByType.json')
def serve_json():
    with open('static/JSONstyles/itemsByType.json') as json_file:
        data = json.load(json_file)
    return jsonify(data)


@socketio.on('ui_update')
def handle_ui_update(data):
    global current_recommand_mode
    element = data.get('element')

    if element == 'recommandationButtonsContainer':
        current_recommand_mode = 'buttons'
        print("Switched to buttons mode.")
    elif element == 'arrowIcones':
        current_recommand_mode = 'arrows'
        print("Switched to arrows mode.")


@socketio.on('update_displayed_items')
def handle_displayed_items(data):
    global current_category
    global current_items
    current_category = data['category']
    current_items = data['items']
    print("this happend when the websockets is triggered")
    print(f"Received update for {current_category}: {current_items}")
    

wardrobe_file_path = r'D:\OSC\MirwearInterface\static\JSONstyles\itemsByType.json'
processing_in_progress = False  # Flag to track if processing is in progress

@socketio.on('recommendation_selected')
def handle_recommendation_selected(data):
    global processing_in_progress
    
    if processing_in_progress:
        print("Processing is already in progress. Skipping this request.")
        return  # Skip if a process is already running
    
    print("Received recommendation selections:", data)
    processing_in_progress = True  # Set the flag to indicate processing has started
    
    # Emit that the processing is starting
    socketio.emit('process_status', {'status': 'in_progress'})
    
    # Load the wardrobe data from the JSON file
    wardrobe_data = load_wardrobe_data(wardrobe_file_path)
    
    # Criteria received from the client
    criteria = {
        "season": data.get('Season', "None"),
        "gender": data.get('Gender', "None"),
        "color": data.get('Color', "None"),
        "style": data.get('Style', "None")
    }

    # Define the prompt with the criteria and wardrobe data
    prompt = f"""
    Prompt:

    You are tasked with creating fashion style recommendations based on the provided JSON data and specific criteria.

    User wardrobe data:
    User wardrobe data:
    {json.dumps(wardrobe_data, indent=2)}

    Recommendation criteria:
    {json.dumps(criteria, indent=2)}

    Your goal is to generate complete style recommendations that meet the criteria provided. Each style should include a distinct top, bottom, and shoes. Ensure that each item (top, bottom, shoes) used in a style is unique and not repeated in other styles. The combinations should be coherent, stylish, and diverse across the styles.

    If any criteria elements are None, then simply recommend styles that include a top, bottom, and shoes that look good together, while respecting the gender of the items. For example, generate complete random styles for men or women, but do not mix items for women in a men's style and vice versa.

    If there are multiple items available in a category (e.g., multiple tops), make sure to use different items in each style. No item should be repeated across different styles. If you run out of unique items to use, limit the number of styles generated accordingly.

    The output should be formatted as follows:

    json
    {{
        "style_1": {{
            "top": {{
                "image": "image_name.jpg",
                "type": "Top_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }},
            "bottom": {{
                "image": "image_name.jpg",
                "type": "Bottom_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }},
            "shoes": {{
                "image": "image_name.jpg",
                "type": "Shoes_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }}
        }},
        "style_2": {{
            "top": {{
                "image": "another_image_name.jpg",
                "type": "Another_Top_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }},
            "bottom": {{
                "image": "another_image_name.jpg",
                "type": "Another_Bottom_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }},
            "shoes": {{
                "image": "another_image_name.jpg",
                "type": "Another_Shoes_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }}
        }},
        "style_3": {{
            // Another complete outfit recommendation with distinct items if available
        }}
    }}
    Please provide at least three style options that align with the given criteria, ensuring that each style is unique and does not repeat items across different styles. If the criteria elements are None, create complete random styles that look good together while respecting the gender of the items.

    Response Format:

    The response should be a JSON object containing the recommended styles, with no additional text.
"""


    try:
        # Request completion from the model
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=4096,
            top_p=1,
            stream=False,
            stop=None,
        )

        response_content = completion.choices[0].message['content'] if 'content' in completion.choices[0].message else completion.choices[0].message

        # Extract and save the JSON
        extract_and_save_json(response_content=response_content, file_path='D:/OSC/MirwearInterface/static/JSONstyles/style_recommendations.json')
        # Emit that the processing is complete
        socketio.emit('process_status', {'status': 'complete'})
    
    finally:
        processing_in_progress = False  # Reset the flag once processing is complete

def extract_and_save_json(response_content, file_path):
    # Check if response_content is a ChatCompletionMessage object and extract content
    if hasattr(response_content, 'content'):
        response_content = response_content.content

    # Print the response to the terminal 
    print("The response of the llama model is:")
    print(response_content)

    # Ensure response_content is now a string
    if isinstance(response_content, str):
        # Use a regular expression to extract content between ```json ... ```
        json_match = re.search(r'```json\s*(.*?)\s*```', response_content, re.DOTALL)
        if json_match:
            json_string = json_match.group(1)
            
            try:
                # Convert the string to a dictionary
                json_data = json.loads(json_string)
                
                # Write the dictionary to a file as JSON
                with open(file_path, 'w') as json_file:
                    json.dump(json_data, json_file, indent=4)
                
                print(f"JSON content has been saved to {file_path}")
                
                # Emit the JSON data via socketio to the client
                socketio.emit('style_recommendations', json_data)
                print("The data is emitted:", json_data)

            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")
        else:
            print("No JSON content found between the ```json ... ``` markers.")
    else:
        print(f"Expected a string, but got {type(response_content)}")


def load_wardrobe_data(file_path):
    with open(file_path, 'r') as json_file:
        return json.load(json_file)



if __name__ == '__main__':
    socketio.run(app, debug=True)