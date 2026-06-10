import cv2
import mediapipe as mp
import pyautogui
import time

# ------------------------------------------
# AUTO RELEASE TIMES (seconds)
# ------------------------------------------
AUTO_RELEASE_SHORT = 1.0          # left, right, space, enter, stop
AUTO_RELEASE_LONG = 7             # up, down (can be 5–10 sec)
# ------------------------------------------

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_DIP  = [3, 6, 10, 14, 18]

held_keys = {}   
key_release_times = {}


def is_finger_folded(lm, tip, dip):
    return lm[tip].y > lm[dip].y


def detect_action(folded):
    thumb, index, middle, ring, pinky = folded

    # ------------------------------------------
    # NEW RULE: Middle + Ring folded = STOP
    # ------------------------------------------
    if middle and ring:
        return "stop", AUTO_RELEASE_SHORT

    # Fist (all folded)
    if sum(folded) == 5:
        return "enter", AUTO_RELEASE_SHORT

    # Thumb = up (long auto release)
    if thumb:
        return "up", AUTO_RELEASE_LONG
    
    # NEW: Index = left
    if index:
        return "left", AUTO_RELEASE_SHORT

    # Middle = down (long)
    if middle:
        return "down", AUTO_RELEASE_LONG

    # NEW: Ring = right
    if ring:
        return "right", AUTO_RELEASE_SHORT

    # Pinky = space
    if pinky:
        return "space", AUTO_RELEASE_SHORT

    return None, None


def press_key(action, release_after):
    if action not in held_keys:
        pyautogui.keyDown(action)
        held_keys[action] = time.time()
        key_release_times[action] = release_after
        print(f"HOLD → {action}  (Release in {release_after} sec)")


def auto_release_keys():
    now = time.time()
    to_release = []

    for key in held_keys:
        hold_time = now - held_keys[key]
        release_time = key_release_times[key]

        if hold_time >= release_time:
            pyautogui.keyUp(key)
            to_release.append(key)
            print(f"RELEASED → {key}")

    for key in to_release:
        del held_keys[key]
        del key_release_times[key]


def main():
    cap = cv2.VideoCapture(0)
    window_w, window_h = 800, 700

    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7) as hands:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (window_w, window_h))
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    lm = hand_landmarks.landmark

                    folded = [
                        is_finger_folded(lm, FINGER_TIPS[i], FINGER_DIP[i])
                        for i in range(5)
                    ]

                    action, release_after = detect_action(folded)

                    if action:
                        press_key(action, release_after)
                        cv2.putText(frame, action, (10, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                                    (0, 255, 0), 3)

            auto_release_keys()

            cv2.imshow("Gesture Control", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Cleanup
    for key in list(held_keys.keys()):
        pyautogui.keyUp(key)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
