import cv2
import mediapipe as mp
import pyautogui

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Finger landmark index positions
FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_DIP = [3, 6, 10, 14, 18]

def is_finger_folded(lm_list, tip, dip):
    return lm_list[tip].y > lm_list[dip].y

def detect_action(fingers_folded):
    thumb, index, middle, ring, pinky = fingers_folded

    if sum(fingers_folded) == 5:
        return "enter"      # Fist

    if thumb:
        return "up"
    if index:
        return "left"
    if middle:
        return "down"
    if ring:
        return "right"
    if pinky:
        return "space"

    return None

def perform_action(action):
    print(f"Action Triggered: {action}")   # ✔ Feedback in terminal

    if action == "up":
        pyautogui.press("up")
    elif action == "left":
        pyautogui.press("left")
    elif action == "down":
        pyautogui.press("down")
    elif action == "right":
        pyautogui.press("right")
    elif action == "space":
        pyautogui.press("space")
    elif action == "enter":
        pyautogui.press("enter")

def main():
    cap = cv2.VideoCapture(0)

    # Smaller window (300x250)
    window_w = 600
    window_h = 500

    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.10) as hands:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (window_w, window_h))  # ✔ Make webcam small

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    lm = hand_landmarks.landmark

                    fingers_folded = [
                        is_finger_folded(lm, FINGER_TIPS[i], FINGER_DIP[i])
                        for i in range(5)
                    ]

                    action = detect_action(fingers_folded)

                    if action:
                        perform_action(action)
                        cv2.putText(frame, f"{action}", (10, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                                    (0, 255, 0), 3)

            cv2.imshow("Gesture Control", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
