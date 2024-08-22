from flask import Flask, Response, render_template, url_for, redirect, session, jsonify
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

buttons = {
    'Option 1': {'top_left': (20, 90), 'bottom_right': (118, 175)},
    'Option 2': {'top_left': (20, 200), 'bottom_right': (108, 286)},
    'Option 3': {'top_left': (30, 300), 'bottom_right': (105, 396)},
    'Recommend': {'top_left': (267, 419), 'bottom_right': (385, 462)},
}



hover_start_time = {}
hover_duration = 1  # Duration to hover in seconds

def check_user_in_outline_v1():
    cap = cv2.VideoCapture(0)
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
    

def check_button_hover(finger_tip_coords):
    global hover_start_time

    if finger_tip_coords:
        for button, coords in buttons.items():
            if (coords['top_left'][0] <= finger_tip_coords['x'] <= coords['bottom_right'][0] and
                coords['top_left'][1] <= finger_tip_coords['y'] <= coords['bottom_right'][1]):
                
                if button not in hover_start_time:
                    hover_start_time[button] = time.time()
                elif time.time() - hover_start_time[button] >= hover_duration:
                    message = {'button': button}
                    print(f"Emitting message: {message}")
                    socketio.emit('button_hover', message)
                    hover_start_time.pop(button)
                    return
            else:
                if button in hover_start_time:
                    hover_start_time.pop(button)

def gen_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            finger_tip_coords = None

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    h, w, c = frame.shape
                    cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                    finger_tip_coords = {'x': cx, 'y': cy}
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
    cam = cv2.VideoCapture(0)
    
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

hover_start_time_recommand = {}
hover_duration = 0.5  # 1 second hover duration

def check_button_hover_recommand(finger_tip_coords):
    global hover_start_time_recommand

    if finger_tip_coords:
        for button, coords in buttons_recommand.items():
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
            for button, coords in buttons_recommand.items():
                cv2.rectangle(frame, 
                              coords['top_left'], 
                              coords['bottom_right'], 
                              (0, 255, 0), 2)  # Green rectangle with thickness of 2
            
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




def load_wardrobe_data(file_path):
    with open(file_path, 'r') as json_file:
        return json.load(json_file)

# Path to the wardrobe data JSON file
wardrobe_file_path = r'D:\OSC\MirwearInterface\JSONstyles\style.json'

@socketio.on('recommendation_selected')
def handle_recommendation_selected(data):
    print("Received recommendation selections:", data)
    
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
    You are tasked with creating fashion style recommendations based on the user's wardrobe data and specific criteria.

    User wardrobe data:
    {json.dumps(wardrobe_data, indent=2)}

    Recommendation criteria:
    {json.dumps(criteria, indent=2)}

    Your goal is to generate complete style recommendations that meet the criteria provided. Each style should include a distinct top, bottom, and shoes. Ensure that each item (top, bottom, shoes) used in a style is unique and not repeated in other styles. The combinations should be coherent, stylish, and diverse across the styles.

    If any criteria elements are `None`, then simply recommend styles that include a top, bottom, and shoes that look good together, while respecting the gender of the items. For example, generate complete random styles for men or women, but do not mix items for women in a men's style and vice versa.

    If there are multiple items available in a category (e.g., multiple tops), make sure to use different items in each style. No item should be repeated across different styles. If you run out of unique items to use, limit the number of styles generated accordingly.

    The output should be formatted as follows and match the JSON pattern:

    ```json
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
"""

    # Request completion from the model
    completion = client.chat.completions.create(
        model="llama3-groq-70b-8192-tool-use-preview",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=1500,
        top_p=1,
        stream=False,
        stop=None,
    )

    response_content = completion.choices[0].message['content'] if 'content' in completion.choices[0].message else completion.choices[0].message

    # Extract and save the JSON
    extract_and_save_json(response_content=response_content, file_path='D:/OSC/MirwearInterface/JSONstyles/style_recommendations.json')


def extract_and_save_json(response_content, file_path):
    # Check if response_content is a ChatCompletionMessage object and extract content
    if hasattr(response_content, 'content'):
        response_content = response_content.content
    
    # Print the response to the terminal 
    print("The response of the llama-3.1-70b-versatile is:")
    print(response_content)

    # Ensure response_content is now a string
    if isinstance(response_content, str):        
        # Since the JSON is already in the response_content, we can attempt to directly parse it
        try:
            # Convert the string to a dictionary
            json_data = json.loads(response_content)
            
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
        print(f"Expected a string, but got {type(response_content)}")





if __name__ == '__main__':
    socketio.run(app, debug=True)
