import time


class GestureStabilizer:
    def __init__(self, buffer_size=5, hold_time=1.0):
        self.buffer_size = buffer_size
        self.hold_time = hold_time

        self.buffer = []
        self.stable_gesture = None
        self.stable_since = None

    def update(self, gesture):
        self.buffer.append(gesture)

        if len(self.buffer) > self.buffer_size:
            self.buffer.pop(0)

        # Check stability
        if len(self.buffer) == self.buffer_size and len(set(self.buffer)) == 1:
            current = self.buffer[0]

            # New stable gesture
            if self.stable_gesture != current:
                self.stable_gesture = current
                self.stable_since = time.time()
                return "STABILIZING"

            # Same gesture held → check duration
            elapsed = time.time() - self.stable_since

            if elapsed >= self.hold_time:
                return self.stable_gesture
            else:
                return "HOLDING"

        # Not stable
        self.stable_gesture = None
        self.stable_since = None
        return "UNSTABLE"

    def reset(self):
        self.buffer.clear()
        self.stable_gesture = None
        self.stable_since = None