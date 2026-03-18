import math
import time
import pyautogui
import config


class MouseController:
    def __init__(
        self,
        smoothing=0.25,
        pinch_smoothing=0.12,
        click_threshold=0.04,
        gain_x=1.0,
        gain_y=1.0,
        drag_hold_time=0.35,
    ):
        pyautogui.FAILSAFE = True

        self.screen_width, self.screen_height = pyautogui.size()

        self.smoothing = smoothing
        self.pinch_smoothing = pinch_smoothing
        self.click_threshold = click_threshold
        self.gain_x = gain_x
        self.gain_y = gain_y
        self.drag_hold_time = drag_hold_time

        self.prev_x = None
        self.prev_y = None

        self.pinching = False
        self.pinch_start_time = None
        self.dragging = False
        self.release_start_time = None

        self.last_right_click_time = 0
        self.prev_scroll_y = None
        self.scroll_accumulator = 0.0
        self.scroll_smoothing = 0.25
        self.scroll_velocity = 0.0

    def _apply_axis_inversion(self, x, y):
        if config.INVERT_X:
            x = 1 - x
        if config.INVERT_Y:
            y = 1 - y
        return x, y

    def _clamp(self, value, min_value, max_value):
        return max(min_value, min(value, max_value))

    def _remap(self, value, in_min, in_max, out_min, out_max):
        if in_max - in_min == 0:
            return out_min
        return (value - in_min) / (in_max - in_min) * (out_max - out_min) + out_min

    def _get_pointer_anchor(self, hand_landmarks):
        index_tip = hand_landmarks.landmark[8]
        index_pip = hand_landmarks.landmark[6]
        index_mcp = hand_landmarks.landmark[5]

        pointer_x = (
            index_tip.x * 0.20 +
            index_pip.x * 0.40 +
            index_mcp.x * 0.40
        )
        pointer_y = (
            index_tip.y * 0.20 +
            index_pip.y * 0.40 +
            index_mcp.y * 0.40
        )

        return self._apply_axis_inversion(pointer_x, pointer_y)

    def move_cursor_from_landmarks(self, hand_landmarks):
        x, y = self._get_pointer_anchor(hand_landmarks)

        x = self._clamp(
            x,
            config.CONTROL_REGION_MIN_X,
            config.CONTROL_REGION_MAX_X,
        )
        y = self._clamp(
            y,
            config.CONTROL_REGION_MIN_Y,
            config.CONTROL_REGION_MAX_Y,
        )

        x = self._remap(
            x,
            config.CONTROL_REGION_MIN_X,
            config.CONTROL_REGION_MAX_X,
            0.0,
            1.0,
        )
        y = self._remap(
            y,
            config.CONTROL_REGION_MIN_Y,
            config.CONTROL_REGION_MAX_Y,
            0.0,
            1.0,
        )

        center_x = 0.5
        center_y = 0.5

        x = center_x + (x - center_x) * self.gain_x
        y = center_y + (y - center_y) * self.gain_y

        x = self._clamp(x, 0.0, 1.0)
        y = self._clamp(y, 0.0, 1.0)

        target_x = int(x * self.screen_width)
        target_y = int(y * self.screen_height)

        if self.prev_x is None or self.prev_y is None:
            self.prev_x = target_x
            self.prev_y = target_y

        current_smoothing = self.pinch_smoothing if self.pinching else self.smoothing

        smooth_x = int(self.prev_x + (target_x - self.prev_x)
                       * current_smoothing)
        smooth_y = int(self.prev_y + (target_y - self.prev_y)
                       * current_smoothing)

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

        current_time = time.time()

        if self.pinching:
            is_pinched = distance < config.PINCH_RELEASE_THRESHOLD
        else:
            is_pinched = distance < config.PINCH_START_THRESHOLD

        if is_pinched and not self.pinching:
            self.pinching = True
            self.pinch_start_time = current_time
            self.release_start_time = None
            return "Mouse: Pinch started"

        if is_pinched and self.pinching:
            self.release_start_time = None
            pinch_duration = current_time - self.pinch_start_time

            if pinch_duration >= self.drag_hold_time and not self.dragging:
                pyautogui.mouseDown()
                self.dragging = True
                return "Mouse: Dragging"

            if self.dragging:
                return "Mouse: Dragging"

            return "Mouse: Holding pinch"

        if not is_pinched and self.pinching:
            if self.release_start_time is None:
                self.release_start_time = current_time
                return "Mouse: Release pending"

            release_duration = current_time - self.release_start_time

            if release_duration < config.PINCH_RELEASE_GRACE_TIME:
                if self.dragging:
                    return "Mouse: Dragging"
                return "Mouse: Holding pinch"

            pinch_duration = current_time - self.pinch_start_time

            if self.dragging:
                pyautogui.mouseUp()
                self.dragging = False
                self.pinching = False
                self.pinch_start_time = None
                self.release_start_time = None
                return "Mouse: Drop"

            if pinch_duration < self.drag_hold_time:
                pyautogui.click()

            self.pinching = False
            self.pinch_start_time = None
            self.release_start_time = None
            return "Mouse: Click"

        return "Mouse: Moving"

    def handle_right_click(self):
        current_time = time.time()
        if current_time - self.last_right_click_time >= config.RIGHT_CLICK_COOLDOWN:
            pyautogui.rightClick()
            self.last_right_click_time = current_time
            return "Mouse: Right Click"
        return "Mouse: Right Click cooldown"

    def handle_scroll(self, hand_landmarks):
        """
        Continuous smooth scrolling using movement accumulation.
        Small hand movement builds up gradually into scroll steps.
        """
        index_tip = hand_landmarks.landmark[8]
        index_pip = hand_landmarks.landmark[6]
        middle_tip = hand_landmarks.landmark[12]

        scroll_y = (
            index_tip.y * 0.4 +
            index_pip.y * 0.3 +
            middle_tip.y * 0.3
        )

        _, y = self._apply_axis_inversion(index_tip.x, scroll_y)

        if self.prev_scroll_y is None:
            self.prev_scroll_y = y
            self.scroll_velocity = 0.0
            self.scroll_accumulator = 0.0
            return "Mouse: Scroll ready"

        delta_y = y - self.prev_scroll_y

        if abs(delta_y) < config.SCROLL_DEADZONE:
            delta_y = 0.0

        target_velocity = (-delta_y) * config.SCROLL_SENSITIVITY
        self.scroll_velocity += (target_velocity -
                                 self.scroll_velocity) * config.SCROLL_SMOOTHING

        self.scroll_accumulator += self.scroll_velocity

        scroll_step = int(self.scroll_accumulator)

        if scroll_step != 0:
            scroll_step = max(
                -config.SCROLL_MAX_STEP,
                min(config.SCROLL_MAX_STEP, scroll_step)
            )
            pyautogui.scroll(scroll_step)
            self.scroll_accumulator -= scroll_step

        self.prev_scroll_y = y
        return f"Mouse: Scrolling ({scroll_step if scroll_step != 0 else 0})"

    def reset_scroll(self):
        self.prev_scroll_y = None
        self.scroll_velocity = 0.0
        self.scroll_accumulator = 0.0

    def reset(self):
        if self.dragging:
            pyautogui.mouseUp()

        self.prev_x = None
        self.prev_y = None
        self.pinching = False
        self.pinch_start_time = None
        self.release_start_time = None
        self.dragging = False
        self.prev_scroll_y = None

    def is_hand_in_control_region(self, hand_landmarks):
        index_tip = hand_landmarks.landmark[8]
        x, y = self._apply_axis_inversion(index_tip.x, index_tip.y)

        return (
            config.CONTROL_REGION_MIN_X <= x <= config.CONTROL_REGION_MAX_X
            and config.CONTROL_REGION_MIN_Y <= y <= config.CONTROL_REGION_MAX_Y
        )

    def get_pointer_anchor_normalized(self, hand_landmarks):
        return self._get_pointer_anchor(hand_landmarks)

    def is_pinch_active(self, hand_landmarks):
        from gesture_logic import is_thumbs_up

        # Block pinch if thumbs up
        if is_thumbs_up(hand_landmarks):
            return False

        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]

        distance = math.sqrt(
            (thumb_tip.x - index_tip.x) ** 2 +
            (thumb_tip.y - index_tip.y) ** 2
        )

        if self.pinching:
            return distance < config.PINCH_RELEASE_THRESHOLD
        return distance < config.PINCH_START_THRESHOLD
