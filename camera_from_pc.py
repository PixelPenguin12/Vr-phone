import cv2
import numpy as np

def map_val(value, from_min, from_max, to_min, to_max) -> float:
    # Calculate the ratio of how far 'value' is between 'from_min' and 'from_max'
    ratio = (value - from_min) / (from_max - from_min)
    
    # Map this ratio to the new range between 'to_min' and 'to_max'
    mapped_value = ratio * (to_max - to_min) + to_min
    
    return mapped_value

# Initialize the camera
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use 0 for the default camera, change if you have multiple cameras

cap.set(cv2.CAP_PROP_FPS, 90)

# Check if the camera is opened correctly
if not cap.isOpened():
    print("Error: Unable to open the camera.")
    exit()

# Define the pattern
pattern = np.array([[0, 0, 1],
                    [1, 0, 1],
                    [0, 1, 1]], dtype=np.uint8)

while True:
    # Capture a frame from the camera
    ret, frame = cap.read()

    # Check if the frame is captured correctly
    if not ret:
        print("Error: Unable to capture frame.")
        break

    # Convert frame to grayscale
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)

    # Perform edge detection
    edges = cv2.Canny(blurred_frame, 20, 100)

    # Find contours in the edge-detected image
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Iterate through contours to find the rectangular contour of the paper
    # Iterate through contours to find the rectangular contour of the paper
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

        # Draw the vertices (for debugging)
        approx_enum = enumerate(approx)
        for i,pos in approx_enum:
            color = map_val(i, 0, len(approx), 0, 255)
            cv2.rectangle(img=frame, pt1=pos[0], pt2=pos[0], color=(color, 0, map_val(color, 0, 255, 255, 0)), thickness=5)
        
        # If the contour has four vertices, it may represent a rectangle
        if len(approx) == 4:
            # Calculate the area of the contour
            area = cv2.contourArea(approx)

            # Check if the area is within a certain range to filter out small contours
            if 5000 < area < 20000:  # Adjust these thresholds according to your application
                # Draw rectangle around the contour
                x, y, w, h = cv2.boundingRect(approx)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                # Crop the region of interest (ROI) containing the pattern
                pattern_roi = gray_frame[y:y+h, x:x+w]

                # Perform template matching on the pattern ROI
                result = cv2.matchTemplate(pattern_roi, pattern, cv2.TM_CCOEFF_NORMED)
                
                # Define a threshold to consider a match
                threshold = 0.9999
                
                # Find locations where the result is above the threshold
                locations = np.where(result >= threshold)
                
                # If any match is found, draw a rectangle around it
                if len(locations[0]) > 0:
                    top_left = (locations[1][0] + x, locations[0][0] + y)
                    bottom_right = (top_left[0] + pattern.shape[1], top_left[1] + pattern.shape[0])
                    cv2.rectangle(frame, top_left, bottom_right, (255, 0, 0), 2)
                    #break  # Stop processing further contours once a pattern is detected

    cv2.imshow("Frame", frame)
    cv2.imshow("Edges", edges)

    # Wait for key press (exit on 'q')
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()