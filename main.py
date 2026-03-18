import time
import cv2

import config
from hand_tracker import HandTracker
from gesture_logic import detect_gesture, is_thumbs_up, is_scroll_gesture
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
    pinch_smoothing=config.MOUSE_PINCH_SMOOTHING,
    click_threshold=config.MOUSE_CLICK_THRESHOLD,
    gain_x=config.MOUSE_GAIN_X,
    gain_y=config.MOUSE_GAIN_Y,
    drag_hold_time=config.PINCH_DRAG_HOLD_TIME,
)
mode_controller = ModeController(default_mode=config.DEFAULT_MODE)

cap = cv2.VideoCapture(config.CAMERA_INDEX)
last_action_time = 0
outside_box_start_time = None

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
                    mouse.reset()
                    stabilizer.reset()
                    actions.set_status("Action: Switched to MOUSE mode")
                    last_action_time = current_time
                    outside_box_start_time = None

                elif (
                    detected_gesture == "FIST"
                    and current_time - last_action_time > config.COOLDOWN_SECONDS
                ):
                    actions.trigger_action("FIST")
                    last_action_time = current_time

                elif detected_gesture == "OPEN_PALM":
                    actions.set_status("Action: Gesture mode ready")

            elif current_mode == config.MODE_MOUSE:
                in_control_region = mouse.is_hand_in_control_region(
                    hand_landmarks)

                if in_control_region:
                    outside_box_start_time = None

                    # Always move cursor first in normal mouse interactions
                    mouse.move_cursor_from_landmarks(hand_landmarks)

                    # Pinch gets highest priority, including release handling
                    pinch_active = mouse.is_pinch_active(hand_landmarks)
                    should_handle_pinch = pinch_active or mouse.pinching or mouse.dragging

                    if should_handle_pinch:
                        mouse.reset_scroll()
                        mouse_status = mouse.handle_pinch_click(hand_landmarks)

                    elif is_scroll_gesture(hand_landmarks):
                        mouse_status = mouse.handle_scroll(hand_landmarks)

                    elif is_thumbs_up(hand_landmarks):
                        mouse.reset_scroll()
                        mouse_status = mouse.handle_right_click()

                    else:
                        mouse.reset_scroll()
                        mouse_status = "Mouse: Moving"
                else:
                    if config.AUTO_SWITCH_TO_GESTURE_ON_OUTSIDE:
                        if outside_box_start_time is None:
                            outside_box_start_time = current_time
                            mouse_status = f"Mouse: Outside box ({config.OUTSIDE_BOX_TIMEOUT:.1f}s)"
                        else:
                            elapsed = current_time - outside_box_start_time
                            remaining = max(
                                0, config.OUTSIDE_BOX_TIMEOUT - elapsed)
                            mouse_status = f"Mouse: Outside box ({remaining:.1f}s)"

                            if elapsed >= config.OUTSIDE_BOX_TIMEOUT:
                                mode_controller.switch_mode(
                                    config.MODE_GESTURE)
                                mouse.reset()
                                stabilizer.reset()
                                actions.set_status(
                                    "Action: Auto-switched to GESTURE mode")
                                last_action_time = current_time
                                outside_box_start_time = None
                    else:
                        mouse_status = "Mouse: Outside control region"

                if (
                    detected_gesture == "OPEN_PALM"
                    and current_time - last_action_time > config.COOLDOWN_SECONDS
                ):
                    mode_controller.switch_mode(config.MODE_GESTURE)
                    mouse.reset()
                    stabilizer.reset()
                    actions.set_status("Action: Switched to GESTURE mode")
                    last_action_time = current_time
                    outside_box_start_time = None
    else:
        current_time = time.time()
        current_mode = mode_controller.get_mode()

        stabilizer.reset()

        if current_mode == config.MODE_MOUSE:
            if config.AUTO_SWITCH_TO_GESTURE_ON_OUTSIDE:
                if outside_box_start_time is None:
                    outside_box_start_time = current_time
                    mouse_status = f"Mouse: No hand / outside box ({config.OUTSIDE_BOX_TIMEOUT:.1f}s)"
                else:
                    elapsed = current_time - outside_box_start_time
                    remaining = max(0, config.OUTSIDE_BOX_TIMEOUT - elapsed)
                    mouse_status = f"Mouse: No hand / outside box ({remaining:.1f}s)"

                    if elapsed >= config.OUTSIDE_BOX_TIMEOUT:
                        mode_controller.switch_mode(config.MODE_GESTURE)
                        mouse.reset()
                        stabilizer.reset()
                        actions.set_status(
                            "Action: Auto-switched to GESTURE mode")
                        last_action_time = current_time
                        outside_box_start_time = None
            else:
                mouse.reset()
        else:
            mouse.reset()
            outside_box_start_time = None

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
