import math
import time
import pyautogui
import config


class ActionController:
    def __init__(self):
        self.last_action_text = "None"

        self.volume_pinching = False
        self.volume_pinch_start_time = None
        self.volume_prev_y = None
        self.last_volume_step_time = 0
        self.volume_anchor_y = None

    def trigger_action(self, gesture):
        if gesture == "FIST":
            pyautogui.press("volumemute")
            self.last_action_text = "Action: Mute"

        return self.last_action_text

    def set_status(self, text):
        self.last_action_text = text
        return self.last_action_text

    def is_volume_pinch_active(self, hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]

        distance = math.sqrt(
            (thumb_tip.x - index_tip.x) ** 2 +
            (thumb_tip.y - index_tip.y) ** 2
        )

        if self.volume_pinching:
            return distance < config.VOLUME_PINCH_RELEASE_THRESHOLD
        return distance < config.VOLUME_PINCH_START_THRESHOLD

    def handle_volume_pinch(self, hand_landmarks):
        index_tip = hand_landmarks.landmark[8]
        current_time = time.time()

        # Detect pinch
        thumb_tip = hand_landmarks.landmark[4]
        distance = ((thumb_tip.x - index_tip.x) ** 2 +
                    (thumb_tip.y - index_tip.y) ** 2) ** 0.5

        if self.volume_pinching:
            is_pinched = distance < config.VOLUME_PINCH_RELEASE_THRESHOLD
        else:
            is_pinched = distance < config.VOLUME_PINCH_START_THRESHOLD

        # Start pinch → set anchor
        if is_pinched and not self.volume_pinching:
            self.volume_pinching = True
            self.volume_anchor_y = index_tip.y
            self.last_volume_step_time = 0
            self.last_action_text = "Action: Volume control started"
            return self.last_action_text

        # While pinched → use displacement from anchor
        if is_pinched and self.volume_pinching:
            delta = self.volume_anchor_y - index_tip.y

            if abs(delta) < config.VOLUME_DEADZONE:
                return "Action: Adjusting volume"

            # Convert displacement into steps
            steps = int(delta * config.VOLUME_SENSITIVITY * 10)

            # Limit steps per frame
            steps = max(-3, min(3, steps))

            if steps != 0 and current_time - self.last_volume_step_time > config.VOLUME_STEP_COOLDOWN:
                if steps > 0:
                    for _ in range(steps):
                        pyautogui.press("volumeup")
                    self.last_action_text = f"Action: Volume Up x{steps}"
                else:
                    for _ in range(abs(steps)):
                        pyautogui.press("volumedown")
                    self.last_action_text = f"Action: Volume Down x{abs(steps)}"

                self.last_volume_step_time = current_time

            return self.last_action_text

        # Release pinch
        if not is_pinched and self.volume_pinching:
            self.volume_pinching = False
            self.volume_anchor_y = None
            self.last_action_text = "Action: Volume control ended"
            return self.last_action_text

        return None

    def reset_volume_pinch(self):
        self.volume_pinching = False
        self.volume_prev_y = None
