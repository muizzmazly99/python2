import cv2
import config


def draw_status(frame, detected_gesture, last_action_text, mode_text, mouse_status=None):
    gesture_color = config.COLOR_GREEN

    if detected_gesture == "UNSTABLE":
        gesture_color = config.COLOR_RED
    elif detected_gesture in ["STABILIZING", "HOLDING"]:
        gesture_color = (0, 165, 255)  # orange

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
