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
        """
        Build a more stable pointer anchor using a weighted blend of:
        - index tip (8)
        - index PIP (6)
        - index MCP (5)

        This is more stable than tracking the fingertip alone,
        especially during pinch gestures.
        """
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

        # Clamp to control region
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

        # Remap control region to full screen space
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

        # Optional center gain expansion
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
        """
        Behavior:
        - short pinch -> click
        - hold pinch -> drag
        - release after stable unpinch -> drop
        """
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]

        distance = math.sqrt(
            (thumb_tip.x - index_tip.x) ** 2 +
            (thumb_tip.y - index_tip.y) ** 2
        )

        is_pinched = distance < self.click_threshold
        current_time = time.time()

        # Pinch just started
        if is_pinched and not self.pinching:
            self.pinching = True
            self.pinch_start_time = current_time
            self.release_start_time = None
            return "Mouse: Pinch started"

        # Pinch is active
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

        # Pinch temporarily lost
        if not is_pinched and self.pinching:
            if self.release_start_time is None:
                self.release_start_time = current_time
                return "Mouse: Release pending"

            release_duration = current_time - self.release_start_time

            # Ignore brief tracking glitches
            if release_duration < config.PINCH_RELEASE_GRACE_TIME:
                if self.dragging:
                    return "Mouse: Dragging"
                return "Mouse: Holding pinch"

            pinch_duration = current_time - self.pinch_start_time

            # End drag
            if self.dragging:
                pyautogui.mouseUp()
                self.dragging = False
                self.pinching = False
                self.pinch_start_time = None
                self.release_start_time = None
                return "Mouse: Drop"

            # Short pinch = click
            if pinch_duration < self.drag_hold_time:
                pyautogui.click()

            self.pinching = False
            self.pinch_start_time = None
            self.release_start_time = None
            return "Mouse: Click"

        return "Mouse: Moving"

    def reset(self):
        if self.dragging:
            pyautogui.mouseUp()

        self.prev_x = None
        self.prev_y = None
        self.pinching = False
        self.pinch_start_time = None
        self.release_start_time = None
        self.dragging = False

    def is_hand_in_control_region(self, hand_landmarks):
        """
        Use raw index fingertip for region presence detection.
        This is better for checking whether the hand is actually
        inside the visible control box.
        """
        index_tip = hand_landmarks.landmark[8]
        x, y = self._apply_axis_inversion(index_tip.x, index_tip.y)

        return (
            config.CONTROL_REGION_MIN_X <= x <= config.CONTROL_REGION_MAX_X
            and config.CONTROL_REGION_MIN_Y <= y <= config.CONTROL_REGION_MAX_Y
        )

    def get_pointer_anchor_normalized(self, hand_landmarks):
        return self._get_pointer_anchor(hand_landmarks)
