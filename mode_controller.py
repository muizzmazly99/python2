class ModeController:
    def __init__(self, default_mode="GESTURE"):
        self.current_mode = default_mode
        self.last_mode_text = f"Mode: {self.current_mode}"

    def switch_mode(self, new_mode):
        if self.current_mode != new_mode:
            self.current_mode = new_mode
            self.last_mode_text = f"Mode: {self.current_mode}"

    def get_mode(self):
        return self.current_mode
