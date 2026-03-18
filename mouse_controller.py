import math
import pyautogui
import config


class MouseController:
    def __init__(
        self,
        smoothing=0.25,
        click_threshold=0.04,
        gain_x=1.4,
        gain_y=1.4,
    ):
        pyautogui.FAILSAFE = True

        self.screen_width, self.screen_height = pyautogui.size()
        self.smoothing = smoothing
        self.click_threshold = click_threshold
        self.gain_x = gain_x
        self.gain_y = gain_y

        self.prev_x = None
        self.prev_y = None
        self.click_down = False

    def _apply_axis_inversion(self, x, y):
        if config.INVERT_X:
            x = 1 - x
        if config.INVERT_Y:
            y = 1 - y
        return x, y

    def move_cursor_from_landmarks(self, hand_landmarks):
        index_tip = hand_landmarks.landmark[8]
        x, y = self._apply_axis_inversion(index_tip.x, index_tip.y)

        center_x = 0.5
        center_y = 0.5

        x = center_x + (x - center_x) * self.gain_x
        y = center_y + (y - center_y) * self.gain_y

        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))

        target_x = int(x * self.screen_width)
        target_y = int(y * self.screen_height)

        if self.prev_x is None or self.prev_y is None:
            self.prev_x = target_x
            self.prev_y = target_y

        smooth_x = int(self.prev_x + (target_x - self.prev_x) * self.smoothing)
        smooth_y = int(self.prev_y + (target_y - self.prev_y) * self.smoothing)

        pyautogui.moveTo(smooth_x, smooth_y)

        self.prev_x = smooth_x
        self.prev_y = smooth_y

    def handle_pinch_click(self, hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]

        distance = math.sqrt(
            (thumb_tip.x - index_tip.x) ** 2 +
            (thumb_tip.y - index_tip.y) ** 2
        )

        if distance < self.click_threshold and not self.click_down:
            pyautogui.click()
            self.click_down = True
            return "Mouse: Click"

        if distance >= self.click_threshold:
            self.click_down = False

        return "Mouse: Moving"

    def reset(self):
        self.prev_x = None
        self.prev_y = None
        self.click_down = False
