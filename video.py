import cv2
import time

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FPS, 60)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

tm = cv2.TickMeter()
tm.start()

count = 0
max_count = 10
fps = 0

while True:
    ret, frame = cap.read()

    cv2.imshow('Raw Frame', frame)

    if count == max_count:
        tm.stop()
        fps = max_count / tm.getTimeSec()
        tm.reset()
        tm.start()
        count = 0
    count += 1

    print(fps)

    k = cv2.waitKey(1)
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()
