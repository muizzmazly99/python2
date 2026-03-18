import cv2
import config


def draw_control_region(frame):
    if not config.SHOW_CONTROL_REGION:
        return

    height, width, _ = frame.shape

    x1 = int(width * config.CONTROL_REGION_MIN_X)
    y1 = int(height * config.CONTROL_REGION_MIN_Y)
    x2 = int(width * config.CONTROL_REGION_MAX_X)
    y2 = int(height * config.CONTROL_REGION_MAX_Y)

    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)


def draw_status(frame, detected_gesture, last_action_text, mode_text, mouse_status=None):
    draw_control_region(frame)

    gesture_color = (
        config.COLOR_RED if detected_gesture == "UNSTABLE" else config.COLOR_GREEN
    )

    cv2.putText(
        frame,
        f"Gesture: {detected_gesture}",
        config.TEXT_POS_GESTURE,
        cv2.FONT_HERSHEY_SIMPLEX,
        config.FONT_SCALE_GESTURE,
        gesture_color,
        config.THICKNESS_GESTURE
    )

    cv2.putText(
        frame,
        last_action_text,
        config.TEXT_POS_ACTION,
        cv2.FONT_HERSHEY_SIMPLEX,
        config.FONT_SCALE_ACTION,
        config.COLOR_YELLOW,
        config.THICKNESS_ACTION
    )

    cv2.putText(
        frame,
        mode_text,
        config.TEXT_POS_MODE,
        cv2.FONT_HERSHEY_SIMPLEX,
        config.FONT_SCALE_MODE,
        config.COLOR_CYAN,
        config.THICKNESS_MODE
    )

    hint_text = "Q = Quit"
    if mouse_status:
        hint_text = f"{mouse_status} | Q = Quit"

    cv2.putText(
        frame,
        hint_text,
        config.TEXT_POS_HINT,
        cv2.FONT_HERSHEY_SIMPLEX,
        config.FONT_SCALE_HINT,
        config.COLOR_GRAY,
        config.THICKNESS_HINT
    )
