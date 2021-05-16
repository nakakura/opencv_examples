import cv2
import time

width = 1920
height = 1080
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FPS, 60)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

fps = 45
video_out = cv2.VideoWriter(
    "appsrc ! videoconvert ! video/x-raw,format=I420  ! autovideosink",
    cv2.CAP_GSTREAMER, 0, fps, (width, height), True)

tm = cv2.TickMeter()
tm.start()

count = 0
max_count = 10
fps = 0

while True:
    ret, frame = cap.read()

    #cv2.imshow('Raw Frame', frame)
    video_out.write(frame)

    if count == max_count:
        tm.stop()
        fps = max_count / tm.getTimeSec()
        tm.reset()
        tm.start()
        count = 0
        print(fps)
    count += 1



cap.release()
cv2.destroyAllWindows()
