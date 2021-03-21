import numpy as np
import cv2
import pytesseract
import re

from backend import Backend

frame_occupation_threshold = 0.65

def contourRectArea(contour):
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    return cv2.contourArea(box)

def is_blurry(img, threshold):
    laplacian = cv2.Laplacian(img, cv2.CV_64F)
    # print(np.percentile(laplacian, 99))
    return np.percentile(laplacian, 99) < threshold

# A name is an uppercase letter followed by some number of lowercase letters (or a dash). An optional space is then matched. Repeat this
name_matcher = re.compile("(([A-Z][a-z\-]*)+( )*)+")
id_matcher = re.compile("899[0-9]{6}")
video = cv2.VideoCapture(0)
if not(video.isOpened):
    print("Cannot open camera")
    exit()


async def get_card_info():
    # Flush out video buffer
    for _ in range(10):
        video.grab()
    print("Trying to detect a card...")
    while True:
        ret, frame = video.read()

        if not(ret):
            print("Cannot read frame")
            break
        
        # Blur image so red color is easier to detect
        blur = cv2.blur(frame, (25,25))
        hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

        # Establish red range
        lower_red = np.array([150,100,50])
        upper_red = np.array([180,255,255])

        # Mask red section and remove noise in mask
        mask = cv2.inRange(hsv, lower_red, upper_red)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5,5),np.uint8))
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Get contours and sort by area. Pick two two biggest and form a rectangle around them
        sorted_contours = sorted(contours, key=cv2.contourArea)
        if len(sorted_contours) >= 2:
            # Merge top two biggest contours into one contour and form rectangle
            big_contour = np.vstack((sorted_contours[-1], sorted_contours[-2]))
            rect = cv2.minAreaRect(np.array(big_contour))
            angle = rect[-1]

            box = cv2.boxPoints(rect)
            box = np.int0(box)

            # Retarget the rectangle into axis aligned rectangle
            height = int(np.linalg.norm(box[0] - box[1]))
            width = int(np.linalg.norm(box[0] - box[3]))
            retarget_points = np.array([[0, height], [0, 0], [width, 0], [width, height]])
            retarget_map = cv2.getPerspectiveTransform(np.float32(box), np.float32(retarget_points))
            retarget_img = cv2.warpPerspective(frame, retarget_map, (width, height))


            if height > width:
                retarget_img = cv2.rotate(retarget_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

            # Mask white section
            retarget_img_gray = cv2.cvtColor(retarget_img, cv2.COLOR_BGR2GRAY)
            ret, retarget_mask = cv2.threshold(retarget_img_gray, 125, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            retarget_mask = cv2.morphologyEx(retarget_mask, cv2.MORPH_CLOSE, np.ones((20, 20), np.uint8))
            # cv2.imshow("retarget_mask", retarget_mask)
            retarget_img = cv2.bitwise_and(retarget_img, retarget_img, mask=retarget_mask)

            # Compute what percentage of the frame the detected box takes up
            frame_occupation_percentage = (width * height) / (frame.shape[0]*frame.shape[1])
            # Once percentage passes threshold, run OCR which is computationally expensive
            if frame_occupation_percentage > frame_occupation_threshold:
                text = pytesseract.image_to_string(retarget_img_gray, lang="eng")
                student_id = id_matcher.search(text)
                student_name = name_matcher.search(text)
                if student_id != None and student_name != None:
                    student_name = student_name.group(0).strip()
                    student_id = student_id.group(0)
                    # Check to make sure that a last name exists
                    if len(student_name.split(" ")) >= 2:
                        print(f"Name: {student_name}")
                        print(f"ID: {student_id}")
                        # Clean up by destroying windows and flush buffer
                        # cv2.destroyAllWindows()
                        frame[:] = (0, 255, 0)
                        cv2.putText(frame, "Sign In.", (10, 50), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 0, 0), 1, cv2.LINE_AA)
                        cv2.imshow("Preview", frame)
                        cv2.waitKey(1)                        
                        return (student_name, student_id)

            # cv2.imshow("retarget", retarget_img)

            text_location = cv2.boundingRect(big_contour)[0:2]
            reading_aid_msg = f"Bring Card Closer ... {round(frame_occupation_percentage / frame_occupation_threshold, 2) * 100}%"
            if frame_occupation_percentage >= frame_occupation_threshold:
                reading_aid_msg = "Keep Still ..."
                cv2.drawContours(frame,[box],0,(0,255,0),3)
                cv2.putText(frame, reading_aid_msg, (text_location[0], text_location[1]), cv2.FONT_HERSHEY_PLAIN, 2.0, (0, 255, 0), 1, cv2.LINE_AA)
            else:
                cv2.drawContours(frame,[box],0,(0,0,255),3)
                cv2.putText(frame, reading_aid_msg, (text_location[0], text_location[1]), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 0, 255), 1, cv2.LINE_AA)


        cv2.putText(frame, "Face Student ID Towards The Camera.", (10, 50), cv2.FONT_HERSHEY_PLAIN, 1.2, (255, 0, 0), 1, cv2.LINE_AA)
        cv2.imshow("Preview", frame)

        cv2.waitKey(1)

server = Backend(get_card_info)
