import copy
import csv
import os

import cv2 as cv
import mediapipe as mp

from dotenv import load_dotenv

from utils import get_args
from utils import CvFpsCalc
from utils import get_result_image
from utils import get_mode

from utils import draw_landmarks
from utils import draw_bounding_rect
from utils import draw_hand_label
from utils import show_info
from utils import show_result

from utils import calc_bounding_rect
from utils import calc_landmark_list
from utils import pre_process_landmark
from utils import log_keypoints

from model import KeyPointClassifier

load_dotenv()


def main():
    #: -
    #: Getting all arguments
    args = get_args()

    #: cv Capture
    CAP_DEVICE = args.device
    CAP_WIDTH = args.width
    CAP_HEIGHT = args.height

    #: mp Hands
    USE_STATIC_IMAGE_MODE = args.use_static_image_mode
    MAX_NUM_HANDS = args.max_num_hands
    MIN_DETECTION_CONFIDENCE = args.min_detection_confidence
    MIN_TRACKING_CONFIDENCE = args.min_tracking_confidence

    #: Drawing Rectangle
    USE_BRECT = args.use_brect
    MODE = args.mode
    DEBUG = int(os.environ.get("DEBUG", "0")) == 1
    CAP_DEVICE = 1
    #: -
    #: Capturing image
    cap = cv.VideoCapture(CAP_DEVICE)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, CAP_WIDTH)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, CAP_HEIGHT)

    #: -
    #: Setup hands
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=USE_STATIC_IMAGE_MODE,
        max_num_hands=MAX_NUM_HANDS,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE
    )

    #: -
    #: Load Model
    keypoint_classifier = KeyPointClassifier()

    #: Loading labels
    keypoint_labels_file = "model/label.csv"
    with open(keypoint_labels_file, encoding="utf-8-sig") as f:
        key_points = csv.reader(f)
        keypoint_classifier_labels = [row[0] for row in key_points]

    #: -
    #: FPS Measurement
    cv_fps = CvFpsCalc(buffer_len=10)

    #: -
    #: Main Loop Start Here...
    while True:
        #: FPS of open cv frame or window
        fps = cv_fps.get()

        #: -
        #: Setup Quit key for program
        key = cv.waitKey(10)
        if key == 27:   # ESC key
            break

        #: -
        #: Camera capture
        ret, image = cap.read()
        if not ret:
            break

        #: Flip Image for mirror display
        image = cv.flip(image, 1)
        debug_image = copy.deepcopy(image)
        result_image = get_result_image()

        #: Converting to RBG from BGR
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

        image.flags.writeable = False
        results = hands.process(image)  #: Hand's landmarks
        image.flags.writeable = True

        #: -
        #: DEBUG - Showing Debug info
        if DEBUG:
            MODE = get_mode(key, MODE)
            debug_image = show_info(debug_image, fps, MODE)

        #: -
        #: Start Detection
        if results.multi_hand_landmarks is not None:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):

                #: Calculate  BoundingBox
                use_brect = True
                brect = calc_bounding_rect(debug_image, hand_landmarks)

                #: Landmark calculation
                landmark_list = calc_landmark_list(debug_image, hand_landmarks)

                #: Conversion to relative coordinates / normalized coordinates
                pre_processed_landmark_list = pre_process_landmark(landmark_list)

                #: -
                #: Checking if in Prediction Mode or in Logging Mode
                #: If Prediction Mode it will predict the hand gesture
                #: If in Logging Mode it will Log key-points or landmarks to the csv file

                if MODE == 0:  #: Prediction Mode / Normal mode
                    #: Hand sign classification
                    hand_sign_id = keypoint_classifier(pre_processed_landmark_list)
                    hand_sign_text = keypoint_classifier_labels[hand_sign_id]

                    #: Showing Result
                    result_image = show_result(result_image, handedness, hand_sign_text)

                elif MODE == 1:  #: Logging Mode
                    log_keypoints(key, pre_processed_landmark_list)

                #: -
                #: Drawing debug info
                debug_image = draw_bounding_rect(debug_image, use_brect, brect)
                debug_image = draw_landmarks(debug_image, landmark_list)
                debug_image = draw_hand_label(debug_image, brect, handedness)

        cv.imshow("Left", result_image)

        cv.imshow("Sing Language Recognition", debug_image)

    cap.release()
    cv.destroyAllWindows()



if __name__ == "__main__":
    main()
