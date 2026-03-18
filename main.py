import time
import cv2

import config
from hand_tracker import HandTracker
from gesture_logic import detect_gesture
from action_controller import ActionController
from gesture_stabilizer import GestureStabilizer
from mouse_controller import MouseController
from mode_controller import ModeController
from ui_overlay import draw_status


tracker = HandTracker(
    static_image_mode=False,
    max_num_hands=config.MAX_NUM_HANDS,
    min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
)

actions = ActionController()
stabilizer = GestureStabilizer(
    buffer_size=config.GESTURE_BUFFER_SIZE,
    hold_time=config.GESTURE_HOLD_TIME
)
mouse = MouseController(
    smoothing=config.MOUSE_SMOOTHING,
    click_threshold=config.MOUSE_CLICK_THRESHOLD,
    gain_x=config.MOUSE_GAIN_X,
    gain_y=config.MOUSE_GAIN_Y,
)
mode_controller = ModeController(default_mode=config.DEFAULT_MODE)

cap = cv2.VideoCapture(config.CAMERA_INDEX)
last_action_time = 0


while True:
    success, frame = cap.read()
    if not success:
        print("Failed to read from webcam.")
        break

    frame = cv2.flip(frame, 1)
    results = tracker.process_frame(frame)

    detected_gesture = "No hand"
    mouse_status = None

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            tracker.draw_landmarks(frame, hand_landmarks)

            raw_gesture = detect_gesture(hand_landmarks)
            detected_gesture = stabilizer.update(raw_gesture)

            current_time = time.time()
            current_mode = mode_controller.get_mode()

            if current_mode == config.MODE_GESTURE:
                if (
                    detected_gesture == "PEACE"
                    and current_time - last_action_time > config.COOLDOWN_SECONDS
                ):
                    mode_controller.switch_mode(config.MODE_MOUSE)
                    actions.set_status("Action: Switched to MOUSE mode")
                    last_action_time = current_time

                elif (
                    detected_gesture == "FIST"
                    and current_time - last_action_time > config.COOLDOWN_SECONDS
                ):
                    actions.trigger_action("FIST")
                    last_action_time = current_time

                elif detected_gesture == "OPEN_PALM":
                    actions.set_status("Action: Gesture mode ready")

            elif current_mode == config.MODE_MOUSE:
                mouse.move_cursor_from_landmarks(hand_landmarks)
                mouse_status = mouse.handle_pinch_click(hand_landmarks)

                if (
                    detected_gesture == "OPEN_PALM"
                    and current_time - last_action_time > config.COOLDOWN_SECONDS
                ):
                    mode_controller.switch_mode(config.MODE_GESTURE)
                    mouse.reset()
                    actions.set_status("Action: Switched to GESTURE mode")
                    last_action_time = current_time
    else:
        stabilizer.reset()
        mouse.reset()

    draw_status(
        frame,
        detected_gesture,
        actions.last_action_text,
        mode_controller.last_mode_text,
        mouse_status,
    )

    cv2.imshow(config.WINDOW_NAME, frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
