import cv2
import multiprocessing
import multiprocessing.sharedctypes
import time
import numpy

WIDTH=1920
HEIGHT=1080

def camera_reader(out_buf, buf1_ready):
  try:
    left_camera_capture = cv2.VideoCapture(0, cv2.CAP_V4L2)
    right_camera_capture = cv2.VideoCapture(2, cv2.CAP_V4L2)
  except TypeError:
    left_camera_capture = cv2.VideoCapture(0)
    right_camera_capture = cv2.VideoCapture(2)

  if left_camera_capture.isOpened() is False:
    raise IOError
  if right_camera_capture.isOpened() is False:
    raise IOError

  left_camera_capture.set(cv2.CAP_PROP_BUFFERSIZE, 4)
  left_camera_capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
  left_camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
  left_camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
  left_camera_capture.set(cv2.CAP_PROP_FPS, 60)

  right_camera_capture.set(cv2.CAP_PROP_BUFFERSIZE, 4)
  right_camera_capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
  right_camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
  right_camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
  right_camera_capture.set(cv2.CAP_PROP_FPS, 60)

  while(True):
    try:
      capture_start_time = time.time()
      ret_l, frame_l = left_camera_capture.read()
      ret_r, frame_r = right_camera_capture.read()
      if ret_l is False:
        raise IOError
      buf1_ready.clear()

      frame = cv2.hconcat([cv2.rotate(frame_l, cv2.ROTATE_180), cv2.rotate(frame_r, cv2.ROTATE_180)])
      memoryview(out_buf).cast('B')[:] = memoryview(frame).cast('B')[:]
      buf1_ready.set()
    except KeyboardInterrupt:
      # 終わるときは CTRL + C を押す
      break
  left_camera_capture.release()

if __name__ == "__main__":
  buf1 = multiprocessing.sharedctypes.RawArray('B', HEIGHT*WIDTH*2*3)
  buf1_ready = multiprocessing.Event()
  buf1_ready.clear()
  p1=multiprocessing.Process(target=camera_reader, args=(buf1,buf1_ready), daemon=True)
  p1.start()

  captured_bgr_image = numpy.empty((HEIGHT, WIDTH*2, 3), dtype=numpy.uint8)

  tm = cv2.TickMeter()
  tm.start()

  count = 0
  max_count = 10
  fps = 0

  while True:
    try:
      display_start_time = time.time()
      buf1_ready.wait()
      captured_bgr_image[:,:,:] = numpy.reshape(buf1, (HEIGHT, WIDTH*2, 3))
      buf1_ready.clear()
      cv2.imshow('frame', captured_bgr_image)

      #calc fps
      if count == max_count:
        tm.stop()
        fps = max_count / tm.getTimeSec()
        tm.reset()
        tm.start()
        count = 0
        print(fps)
      count += 1

      cv2.waitKey(1)
    except KeyboardInterrupt:
      # 終わるときは CTRL + C を押す
      print("Waiting camera reader to finish.")
      p1.join(10)
      break

  cv2.destroyAllWindows()
