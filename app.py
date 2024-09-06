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
import base64


app = Flask(__name__)
socketio = SocketIO(app)
size_capture_done = False

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
    
buttons = {
    'Top': {'top_left': (13, 156), 'bottom_right': (60, 210)},
    'Bottom': {'top_left': (13, 200), 'bottom_right': (60, 286)},
    'Foot': {'top_left': (13, 280), 'bottom_right': (60, 333)},
    'Recommend': {'top_left': (267, 419), 'bottom_right': (385, 462)},
    'Changedown': {'top_left': (567, 395), 'bottom_right': (607, 435)},
    'ChangeUp': {'top_left': (559, 55), 'bottom_right': (599, 95)},
    'option1_1': {'top_left': (545, 129), 'bottom_right': (617, 205)},
    'option1_2': {'top_left': (545, 216), 'bottom_right': (617, 295)},
    'option1_3': {'top_left': (545, 303), 'bottom_right': (617, 385)},
}

def check_button_hover(finger_tip_coords):
    global hover_start_time
    global current_category
    global current_items

    if finger_tip_coords:
        for button, coords in buttons.items():
            if (coords['top_left'][0] <= finger_tip_coords['x'] <= coords['bottom_right'][0] and
                coords['top_left'][1] <= finger_tip_coords['y'] <= coords['bottom_right'][1]):
                
                if button not in hover_start_time:
                    hover_start_time[button] = time.time()
                elif time.time() - hover_start_time[button] >= hover_duration:
                    if button in ['option1_1', 'option1_2', 'option1_3']:
                        print(f"{button} is hovered")
                        if current_category and current_items:
                            selected_item = select_item_by_option(current_items, button)
                            print("The selected items : ")
                            print(selected_item)

                            if selected_item:
                                message = {'button': button, 'selected_item': selected_item}
                                print(f"Emitting selected item: {message}")
                    else:
                        message = {'button': button}
                        print(f"Emitting message: {message}")
                        socketio.emit('button_hover', message)
                    hover_start_time.pop(button)
                    return
            else:
                if button in hover_start_time:
                    hover_start_time.pop(button)

def gen_frames():
    camera = cv2.VideoCapture(camera_index)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            for button, coords in buttons.items():
                cv2.rectangle(frame,
                            coords['top_left'],
                            coords['bottom_right'],
                            (255, 255, 255))
                   
            results = hands.process(frame_rgb)
            finger_tip_coords = None

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    h, w, c = frame.shape
                    cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                    finger_tip_coords = {'x': cx, 'y': cy}
                    # print("The coord of finger : ", (cx, cy))
                    cv2.circle(frame, (cx, cy), 20, (255, 255, 255), 2)
                    check_button_hover(finger_tip_coords)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
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

button_season = {
    'winter': {'top_left': (130, 225), 'bottom_right': (200, 251)},
    'summer': {'top_left': (130, 226), 'bottom_right': (200, 295)},
    'spring': {'top_left': (130, 313), 'bottom_right': (200, 336)},
    'fall': {'top_left': (130, 352), 'bottom_right': (200, 376)},
}

buttons_recommand = {
    'Season': {'top_left': (150, 156), 'bottom_right': (221, 185)},
    'Gender': {'top_left': (240, 156), 'bottom_right': (315, 185)},
    'Color': {'top_left': (330, 156), 'bottom_right': (409, 185)},
    'Style': {'top_left': (420, 156), 'bottom_right': (493, 185)},

    'winter': {'top_left': (150, 200), 'bottom_right': (223, 222)},
    'summer': {'top_left': (150, 237), 'bottom_right': (223, 263)},
    'spring': {'top_left': (150, 274), 'bottom_right': (223, 304)},
    'fall': {'top_left': (150, 311), 'bottom_right': (223, 345)},

    'male': {'top_left': (246, 200), 'bottom_right': (314, 222)},
    'female': {'top_left': (246, 237), 'bottom_right': (314, 260)},
    'unisex': {'top_left': (246, 274), 'bottom_right': (314, 298)},
    'kids': {'top_left': (246, 311), 'bottom_right': (314, 336)},

    'red': {'top_left': (338, 200), 'bottom_right': (407, 222)},
    'blue': {'top_left': (338, 237), 'bottom_right': (407, 260)},
    'green': {'top_left': (338, 274), 'bottom_right': (407, 298)},
    'yellow': {'top_left': (338, 311), 'bottom_right': (407, 336)},

    'casual': {'top_left': (430, 200), 'bottom_right': (493, 222)},
    'formal': {'top_left': (430, 237), 'bottom_right': (493, 260)},
    'sport': {'top_left': (430, 274), 'bottom_right': (493, 298)},
    'vintage': {'top_left': (430, 311), 'bottom_right': (493, 336)},

    'recommand': {'top_left': (274, 431), 'bottom_right': (362, 460)},

    'shoffle': {'top_left': (548, 428), 'bottom_right': (596, 476)}
}

arrow_recommand = {
    'topLeft': {'top_left': (490, 150), 'bottom_right': (520, 180)},
    'topright': {'top_left': (123, 147), 'bottom_right': (153, 177)},
    'bottomLeft': {'top_left': (483, 226), 'bottom_right': (513, 256)},
    'bottomRight': {'top_left': (130, 225), 'bottom_right': (160, 255)},
    'shoesLeft': {'top_left': (486, 303), 'bottom_right': (516, 333)},
    'shoesRight': {'top_left': (118, 301), 'bottom_right': (148, 331)},
    'shoffle': {'top_left': (548, 428), 'bottom_right': (596, 476)},

    'refresh': {'top_left': (274, 431), 'bottom_right': (362, 460)},
}

hover_start_time_recommand = {}
hover_duration = 0.5  # 1 second hover duration
current_recommand_mode = 'buttons'

def check_button_hover_recommand(finger_tip_coords):
    global hover_start_time_recommand
    global current_recommand_mode

    # Determine which set of coordinates to use
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
                    return
            else:
                if button in hover_start_time_recommand:
                    hover_start_time_recommand.pop(button)

def gen_frames_for_recommandation():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Draw rectangles based on the received positions
            # if current_recommand_mode == 'buttons':
            #     for button, coords in buttons_recommand.items():
            #         cv2.rectangle(frame, 
            #                     coords['top_left'], 
            #                     coords['bottom_right'], 
            #                     (255, 255, 255), 1)  # Green rectangle with thickness of 2

            # if current_recommand_mode == 'arrows':
            #     for button, coords in arrow_recommand.items():
            #         cv2.rectangle(frame,
            #                     coords['top_left'],
            #                     coords['bottom_right'],
            #                     (255, 255, 255), 1)      
                
            results = hands.process(frame_rgb)
            finger_tip_coords = None

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    h, w, _ = frame.shape
                    cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                    # print("The fingertip index:", (cx, cy))
                    finger_tip_coords = {'x': cx, 'y': cy}
                    cv2.circle(frame, (cx, cy), 20, (255, 255, 255), 2)
                    check_button_hover_recommand(finger_tip_coords)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            

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


def get_latest_image(folder_path):
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not files:
        return None
    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
    return os.path.join(folder_path, latest_file)


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
    folder_path = r"D:\OSC\MirwearInterface\static\output"
    image_path = get_latest_image(folder_path)
    
    image_data = None
    mime_type = None
    
    if image_path:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Determine the MIME type based on the file extension
        file_extension = os.path.splitext(image_path)[1].lower()
        mime_type = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp'
        }.get(file_extension, 'image/webp')  # Default to webp if unknown

    return render_template('index.html', image_data=image_data, mime_type=mime_type)


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
    print("this happend when the websockets is triggered : ")
    print(current_category)
    print(current_items)
    print(f"Received update for {current_category}: {current_items}")
    print("the finale of the web sockect trigger")
    

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
