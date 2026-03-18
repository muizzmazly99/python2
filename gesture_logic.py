def count_fingers(hand_landmarks):
    landmarks = hand_landmarks.landmark

    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]

    thumb_ip = landmarks[3]
    index_pip = landmarks[6]
    middle_pip = landmarks[10]
    ring_pip = landmarks[14]
    pinky_pip = landmarks[18]

    finger_states = {
        "thumb": False,
        "index": False,
        "middle": False,
        "ring": False,
        "pinky": False,
    }

    if thumb_tip.x < thumb_ip.x:
        finger_states["thumb"] = True

    if index_tip.y < index_pip.y:
        finger_states["index"] = True
    if middle_tip.y < middle_pip.y:
        finger_states["middle"] = True
    if ring_tip.y < ring_pip.y:
        finger_states["ring"] = True
    if pinky_tip.y < pinky_pip.y:
        finger_states["pinky"] = True

    total_fingers = sum(finger_states.values())
    return total_fingers, finger_states


def detect_gesture(hand_landmarks):
    total_fingers, finger_states = count_fingers(hand_landmarks)

    if total_fingers >= 4:
        return "OPEN_PALM"

    if total_fingers == 0:
        return "FIST"

    if (
        finger_states["index"]
        and finger_states["middle"]
        and not finger_states["ring"]
        and not finger_states["pinky"]
    ):
        return "PEACE"

    return "UNKNOWN"
