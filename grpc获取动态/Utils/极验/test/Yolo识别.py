import cv2
import numpy as np
from ultralytics import YOLO

# 加载YOLOv8模型（你需要替换为你自己的模型路径）
model = YOLO('yolov8x-seg.pt', task='segment')  # 替换为你的YOLOv8分割模型路径

# 读取输入图像
image_path_1 = 'img_1.png'  # 替换为你的第一张图像路径
image_1 = cv2.imread(image_path_1)

# 进行图像分割
results = model.predict(source=image_1)  # 返回结果包含分割信息
results[0].show()
