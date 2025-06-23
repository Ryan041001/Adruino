#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头实时人脸检测程序
功能：使用摄像头实时检测人脸并用矩形框标出
"""

import cv2

def detect_faces_camera():
    """
    摄像头实时人脸检测
    """
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("无法打开摄像头")
        return
    
    # 加载人脸检测分类器
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    print("摄像头人脸检测已启动，按 'q' 键退出")
    
    while True:
        # 读取摄像头帧
        ret, frame = cap.read()
        
        if not ret:
            print("无法读取摄像头数据")
            break
        
        # 转换为灰度图像
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 检测人脸
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        # 在检测到的人脸周围画矩形框
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # 显示人脸数量
        cv2.putText(frame, f'Faces: {len(faces)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 显示结果
        cv2.imshow('Camera Face Detection', frame)
        
        # 按 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    print("摄像头已关闭")

if __name__ == "__main__":
    detect_faces_camera()