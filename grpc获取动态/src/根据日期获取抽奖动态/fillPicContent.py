import cv2
import numpy as np
from PIL import Image
# 读取图片
image_path = './favicon.ico'  # 替换为你的图片路径
ico_image = Image.open(image_path)

# 将图像保存为.png格式
ico_image.save('temp_icon.png', 'PNG')
image = cv2.imread('temp_icon.png')
# 将图片转换为灰度图
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 使用Canny边缘检测算法找出边缘
edges = cv2.Canny(gray_image, threshold1=50, threshold2=150)

# 创建一个与原图相同大小的掩码，初始化为0
mask = np.zeros(image.shape[:2], dtype=np.uint8)

# 找出边缘内部的像素，并在掩码中标记为1
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(mask, contours, -1, 1, thickness=cv2.FILLED)

# 使用掩码和原始图像来填充边缘内部区域为C0C0C0
# 首先，创建一个全灰色的图像
gray_color = (192, 192, 192)  # C0C0C0 in decimal RGB
gray_image_filled = np.full_like(image, gray_color, dtype=np.uint8)

# 然后，用原图的像素替换掩码为0（即边缘外部）的像素
gray_image_filled[mask == 0] = image[mask == 0]

# 显示结果
cv2.imshow('Original Image', image)
cv2.imshow('Edge Detection', edges)
cv2.imshow('Filled with C0C0C0', gray_image_filled)
cv2.waitKey(0)
cv2.destroyAllWindows()
