#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import matplotlib.pyplot as plt
import numpy

capture = cv2.VideoCapture(0, cv2.CAP_V4L2)
capture.set(cv2.CAP_PROP_FPS, 60)           # カメラFPSを60FPSに設定
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) # カメラ画像の横幅を1280に設定
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080) # カメラ画像の縦幅を720に設定
capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

mtx = [[1.69699655e+03, 0.00000000e+00, 9.56941641e+02],
       [0.00000000e+00, 1.85621271e+03, 5.61461687e+02],
       [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]]

# k1, k2, p1, p2, k3
# http://opencv.jp/opencv-2svn/py/camera_calibration_and_3d_reconstruction.html
# simulator
# https://kamino410.github.io/cv-snippets/camera_distortion_simulator/
dist = [[-0.4847862, -0.44138978, -0.01640419, 0.00071213, -0.36719414]]

mtx = cv2.UMat(numpy.array(mtx, dtype=numpy.float32))
dist = cv2.UMat(numpy.array(dist, dtype=numpy.float32))

h = 1080
w = 1920

newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
mapx,mapy = cv2.initUndistortRectifyMap(mtx,dist,None,newcameramtx,(w,h),5)

while True:
    ret, img = capture.read()
    dst = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)
    dst = dst.get()[180:900, 320:1600] # トリミング
    #dst = cv2.resize(dst, (1408, 720))
    cv2.imshow('image', dst)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
