import pyautogui


class ActionController:
    def __init__(self):
        self.screenshot_count = 0
        self.last_action_text = "None"

    def trigger_action(self, gesture):
        if gesture == "FIST":
            pyautogui.press("volumemute")
            self.last_action_text = "Action: Mute"

        return self.last_action_text

    def set_status(self, text):
        self.last_action_text = text
        return self.last_action_text
