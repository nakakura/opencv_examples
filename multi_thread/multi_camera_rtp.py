import cv2
import multiprocessing
import multiprocessing.sharedctypes
import time
import numpy

CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
IMAGE_WIDTH = 2560
IMAGE_HEIGHT = 720

# H264 encode from the source
VCAPS="video/x-raw,width=2560,height=720,framerate=60/1"

# rtp送信用のパラメータ
DEST = "127.0.0.1"

DEST_VIDEO_RTP_PORT=20000
DEST_VIDEO_RTCP_PORT=20001

SRC_VIDEO_RTCP_PORT=20002

def undistort_and_crop(frame, mapx, mapy):
    dst = cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)
    dst = dst.get()[180:900, 320:1600]  # トリミング
    return dst

def open_camera(num):
    try:
        camera = cv2.VideoCapture(num, cv2.CAP_V4L2)
    except TypeError:
        camera = cv2.VideoCapture(num)

    while not camera.isOpened():
        print("not is opened")
        continue

    return camera

def camera_reader(out_buf, buf1_ready):
    # 歪み補正の値をセットアップ
    # http://opencv.jp/opencv-2svn/py/camera_calibration_and_3d_reconstruction.html
    # simulator
    # https://kamino410.github.io/cv-snippets/camera_distortion_simulator/
    mtx = [[1.69699655e+03, 0.00000000e+00, 9.56941641e+02],
           [0.00000000e+00, 1.85621271e+03, 5.61461687e+02],
           [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]]
    # k1, k2, p1, p2, k3
    dist = [[-0.4847862, -0.44138978, -0.01640419, 0.00071213, -0.36719414]]
    mtx = cv2.UMat(numpy.array(mtx, dtype=numpy.float32))
    dist = cv2.UMat(numpy.array(dist, dtype=numpy.float32))

    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (CAMERA_WIDTH, CAMERA_HEIGHT), 1,
                                                      (CAMERA_WIDTH, CAMERA_HEIGHT))
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (CAMERA_WIDTH, CAMERA_HEIGHT), 5)

    left_camera_capture = open_camera(2)
    right_camera_capture = open_camera(0)

    left_camera_capture.set(cv2.CAP_PROP_BUFFERSIZE, 4)
    left_camera_capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    left_camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    left_camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    left_camera_capture.set(cv2.CAP_PROP_FPS, 60)

    right_camera_capture.set(cv2.CAP_PROP_BUFFERSIZE, 4)
    right_camera_capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    right_camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    right_camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    right_camera_capture.set(cv2.CAP_PROP_FPS, 60)

    while (True):
        try:
            capture_start_time = time.time()
            ret_l, frame_l = left_camera_capture.read()
            ret_r, frame_r = right_camera_capture.read()
            if ret_l is False or ret_r is False:
                continue
            buf1_ready.clear()

            frame_l = undistort_and_crop(frame_l, mapx, mapy)
            frame_r = undistort_and_crop(frame_r, mapx, mapy)
            frame = cv2.hconcat([cv2.rotate(frame_l, cv2.ROTATE_180), cv2.rotate(frame_r, cv2.ROTATE_180)])
            memoryview(out_buf).cast('B')[:] = memoryview(frame).cast('B')[:]
            buf1_ready.set()
        except KeyboardInterrupt:
            # 終わるときは CTRL + C を押す
            break
        except Exception:
            continue

    left_camera_capture.release()
    right_camera_capture.release()


if __name__ == "__main__":
    buf1 = multiprocessing.sharedctypes.RawArray('B', IMAGE_HEIGHT * IMAGE_WIDTH * 3)
    buf1_ready = multiprocessing.Event()
    buf1_ready.clear()
    p1 = multiprocessing.Process(target=camera_reader, args=(buf1, buf1_ready), daemon=True)
    p1.start()

    captured_bgr_image = numpy.empty((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=numpy.uint8)

    tm = cv2.TickMeter()
    tm.start()

    gst_pipeline = "rtpbin name=rtpbin rtp-profile=avpf " \
                   "appsrc ! videoconvert ! {} ! videoconvert " \
                   "! nvh264enc qos=true preset=5 ! rtph264pay pt=100 mtu=1400 " \
                   "! rtprtxqueue max-size-packets=0 max-size-time=200 ! rtpbin.send_rtp_sink_0 " \
                   "rtpbin.send_rtp_src_0 ! udpsink port={} host={} sync=false async=false name=vrtpsink " \
                   "rtpbin.send_rtcp_src_0 ! udpsink port={} host={} sync=false async=false name=vrtcpsink " \
                   "udpsrc port={} name=vrtpsrc ! rtpbin.recv_rtcp_sink_0".format(VCAPS, DEST_VIDEO_RTP_PORT, "127.0.0.1", DEST_VIDEO_RTCP_PORT, "127.0.0.1", SRC_VIDEO_RTCP_PORT)
    video_out = cv2.VideoWriter(
        gst_pipeline,
        cv2.CAP_GSTREAMER, 0, 60, (IMAGE_WIDTH, IMAGE_HEIGHT), True)

    count = 0
    max_count = 10
    fps = 0

    while True:
        try:
            display_start_time = time.time()
            buf1_ready.wait()
            captured_bgr_image[:, :, :] = numpy.reshape(buf1, (IMAGE_HEIGHT, IMAGE_WIDTH, 3))
            buf1_ready.clear()
            video_out.write(captured_bgr_image)

            # calc fps
            if count == max_count:
                tm.stop()
                fps = max_count / tm.getTimeSec()
                tm.reset()
                tm.start()
                count = 0
            count += 1
        except KeyboardInterrupt:
            # 終わるときは CTRL + C を押す
            print("Waiting camera reader to finish.")
            p1.join(10)
            break

    cv2.destroyAllWindows()
