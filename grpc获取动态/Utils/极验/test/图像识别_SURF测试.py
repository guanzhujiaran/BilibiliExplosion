import math
from dataclasses import dataclass, field
import ddddocr
import numpy as np
from loguru import logger
from matplotlib import pyplot as plt
from scipy.optimize import linear_sum_assignment
import cv2


def get_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def surf_feature_matching(img1, img2):
    # 初始化SURF检测器
    img2 = cv2.resize(img2,(img1.shape[0],img1.shape[1]))
    surf = cv2.SIFT_create()

    # 检测关键点和计算描述子
    keypoints1, descriptors1 = surf.detectAndCompute(img1, None)
    keypoints2, descriptors2 = surf.detectAndCompute(img2, None)
    if descriptors1 is None or descriptors2 is None:
        return 999999
    # 匹配描述子
    # 使用BFMatcher（Brute Force Matcher）
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(descriptors1, descriptors2, k=2)

    good = []
    plt.subplot(1, 2, 1)
    plt.imshow(img1)
    plt.subplot(1, 2, 2)
    plt.imshow(img2)
    plt.show()
    for m, n in matches:
        if m.distance < 0.8 * n.distance:
            good.append(m)
    if len(good) < 10:
        return 4  # 完全不匹配
    src_pts = np.float32([keypoints1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    matchesMask = mask.ravel().tolist()
    good = [good[matchesMask.index(i)] for i in matchesMask if i == 1]
    img3 = cv2.drawMatches(img1, keypoints1, img2, keypoints2, good, None)
    plt.figure()
    plt.imshow(img3)
    plt.show()
    good = sorted(good, key=lambda x: x.distance)
    if len(good) < 10:
        return 4  # 完全不匹配
    else:
        good = good[0:10]
        distance_sum = 0  # 特征点2d物理坐标偏移总和
        for m in good:
            distance_sum += get_distance(keypoints1[m.queryIdx].pt, keypoints2[m.trainIdx].pt)
        distance = distance_sum / len(good)  # 单个特征点2D物理位置平均偏移量

        if distance < 4:
            return 1  # 完全匹配
        elif distance < 10 and distance >= 4:
            return 2  # 部分偏移
        else:
            return 3  # 场景匹配


det = ddddocr.DdddOcr(det=True, beta=True)

for i in range(3):
    img_path = f"test_pic/{i}.jpg"
    with open(img_path, 'rb') as f:
        image = f.read()

    bboxes = det.detection(image)

    print(f'检测图框：{bboxes}')

    im = cv2.imread(img_path)


    @dataclass
    class CaptchaInfo:
        img: np.ndarray
        position: list[int, int, int, int]  # x1,y1,x2,y2
        target_position: list[int] = field(default_factory=list)


    target_img_list = []
    src_img_list = []
    for idx, bbox in enumerate(bboxes):
        x1, y1, x2, y2 = bbox
        if y1 > 340:
            src_img_list.append(
                CaptchaInfo(
                    im[y1:y2, x1:x2], bbox
                )
            )
        else:
            if x2 - x1 > 50 and y2 - y1 > 50:
                target_img_list.append(
                    CaptchaInfo(
                        im[y1:y2, x1:x2], bbox
                    )
                )
    if len(target_img_list) < len(src_img_list):
        logger.error(f'ddddocr识别失败！图像识别数量不足\n{bboxes}')
        for bbox in bboxes:
            x1, y1, x2, y2 = bbox
            im = cv2.rectangle(im, (x1, y1), (x2, y2), color=(0, 0, 255), thickness=2)
        cv2.imwrite(f'test_failed_pic/{i}.jpg', im)
        continue

    src_img_list.sort(key=lambda x: x.position[0])  # 排序

    # 构建一个图像的成本矩阵
    #      tar1  tar2 tar3 ...
    # src1  xx    xx   xx
    # src2  xx    xx   xx
    # src3  xx    xx   xx
    #  .    ..    ..   ..
    #  .    ..    ..   ..
    #  .    ..    ..   ..

    img_match_mat = np.zeros((len(src_img_list), len(target_img_list)), dtype=np.float32)

    for idx_i, src_img in enumerate(src_img_list):
        for idx_j, target_img in enumerate(target_img_list):
            img_match_mat[idx_i][idx_j] = surf_feature_matching(src_img.img, target_img.img)
    print(f'构成图像配对矩阵({img_match_mat.shape})：\n{img_match_mat}')
    row_indices, col_indices = linear_sum_assignment(img_match_mat)
    pairings = [(row, col) for row, col in zip(row_indices, col_indices)]
    print("图像配对情况：")
    print(pairings)
    for row, col in pairings:
        src_img_list[row].target_position = target_img_list[col].position
    for idx, src_img in enumerate(src_img_list):
        im = cv2.putText(im, str(idx), (src_img.target_position[2], src_img.target_position[3]),
                         cv2.FONT_HERSHEY_SIMPLEX,
                         0.75, (255, 255, 255), 2)
        im = cv2.putText(im, str(idx), (src_img.position[2], src_img.position[3]),
                         cv2.FONT_HERSHEY_SIMPLEX,
                         0.75, (255, 255, 255), 2)
    for idx, bbox in enumerate(bboxes):
        x1, y1, x2, y2 = bbox
        im = cv2.rectangle(im, (x1, y1), (x2, y2), (0, 255, 0), 2)
    plt.figure()
    plt.imshow(im)
    plt.show()
    cv2.imwrite(f'test_result_pic/result{i}.jpg', im)
