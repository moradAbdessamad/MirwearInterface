from flask import Flask, Response, render_template, url_for, redirect, session, jsonify
import threading
from flask_socketio import SocketIO, emit
import cv2
import mediapipe as mp
import time

app = Flask(__name__)
socketio = SocketIO(app)
size_capture_done = False

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

if __name__ == '__main__':
    socketio.run(app, debug=True)
