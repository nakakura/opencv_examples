import numpy as np
import cv2
from multiprocessing import Process

def send_process():
    print(cv2.CAP_GSTREAMER)
    video_in = cv2.VideoCapture("videotestsrc ! video/x-raw,framerate=20/1 ! videoscale ! videoconvert ! appsink", cv2.CAP_GSTREAMER)
    video_out = cv2.VideoWriter("appsrc ! videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! rtph264pay ! udpsink host=[destination_ip] port=12345", cv2.CAP_GSTREAMER, 0, 24, (800,600), True)

    if not video_in.isOpened() or not video_out.isOpened():
        print("VideoCapture or VideoWriter not opened")
        exit(0)

    while True:
        ret,frame = video_in.read()

        if not ret: break

        video_out.write(frame)

        cv2.imshow("send_process", frame)
        if cv2.waitKey(1)&0xFF == ord("q"):
            break

    video_in.release()
    video_out.release()

def receive_process():
    cap_receive = cv2.VideoCapture('udpsrc port=12345 caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" ! rtph264depay ! decodebin ! videoconvert ! appsink', cv2.CAP_GSTREAMER)

    if not cap_receive.isOpened():
        print("VideoCapture not opened")
        exit(0)

    while True:
        ret,frame = cap_receive.read()

        if not ret: break

        cv2.imshow('receive_process', frame)
        if cv2.waitKey(1)&0xFF == ord('q'):
            break

    cap_receive.release()

if __name__ == '__main__':
    print(cv2.getBuildInformation())
    s = Process(target=send_process)
    r = Process(target=receive_process)
    s.start()
    r.start()
    s.join()
    r.join()

    cv2.destroyAllWindows()