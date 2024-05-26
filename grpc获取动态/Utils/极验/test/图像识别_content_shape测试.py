import math
from collections import Counter
from dataclasses import dataclass, field

import ddddocr
import cv2
import numpy as np
from PIL import Image
from loguru import logger
from matplotlib import pyplot as plt
from scipy.optimize import linear_sum_assignment


def Edge_detection(img, kernel_size=(3, 3), thresh1=50, thresh2=200):
    """
    边缘检测算法 （图像预处理）
    1. 直方图去背景
    2. Canny算子检测边缘
    """

    canny = cv2.Canny(img, thresh1, thresh2)

    return canny


def context_shape_match(img1, img2, N=200, angle=32, distance=None) -> float:
    """
    图形匹配
    path1: 图片路径1
    path2: 图片路径2
    N: 采样点数
    angle: 上下文极坐标角度划分个数
    """

    if distance is None:
        distance = [0, 0.125, 0.25, 0.5, 1.0, 2.0]

    def Jitendra_Sample(_points, _N=100, k=3):
        """
        Jitendra’s sampling
        points: 样本点，shape为[I, 2]，其中I为点的个数
        N: 采样的点的数目
        k: 阈值
        """
        # 样本点个数
        I = _points.shape[0]
        # 首先需要对样本点进行乱序
        _points = np.random.permutation(_points)

        NStart = min(k * _N, I)
        # 阈值
        if I > k * _N:
            NStart_sample_points = _points[:NStart]
        else:
            NStart_sample_points = _points
        # 计算欧式距离矩阵
        dist = np.sqrt(np.sum(
            np.square(NStart_sample_points.reshape((1, NStart, 2)) - NStart_sample_points.reshape((NStart, 1, 2))),
            axis=-1)) + np.eye(NStart, dtype=int) * 999999999999

        # 迭代，删到只剩N个点
        for num in range(NStart - _N):
            # 将该点删去，实现是设置为很大
            # i = np.where(dist == np.min(dist))[0][0]
            j = np.where(dist == np.min(dist))[1][0]
            dist[j, :] = 999999999999
            dist[:, j] = 999999999999

        # 获取序列，注意去重
        _i = np.unique(np.where(dist < 999999999999)[0])
        sample_points = NStart_sample_points[_i]
        return sample_points

    def Shape_Context(_points, _angle=12, _distance=None):
        """
        形状上下文直方图矩阵的构建
        points: 输入的采样点 shape[N,2]
        angle:  划分的角度区域个数
        distance: 划分的距离区域
        """
        # 计算欧式距离矩阵
        if _distance is None:
            _distance = [0, 0.125, 0.25, 0.5, 1.0, 2.0]
        _N = _points.shape[0]
        dist = np.sqrt(np.sum(np.square(_points.reshape((1, _N, 2)) - _points.reshape((_N, 1, 2))), axis=-1))

        # 距离均值
        mean_dist = np.sum(dist) / (_N * _N - _N)
        # 除以均值，减少缩放敏感性
        dist = np.log(dist / mean_dist + 0.000000000001) + np.eye(_N, dtype=int) * 999
        # print(dist)

        # 角度计算
        theta = np.arctan((_points[:, 1].reshape(1, _N) - _points[:, 1].reshape(_N, 1)) / (
                _points[:, 0].reshape(1, _N) - _points[:, 0].reshape(_N, 1) + 0.000000000001)) / math.pi + (
                        (_points[:, 0].reshape(1, _N) - _points[:, 0].reshape(_N, 1)) < 0).astype(
            int) + 0.5  # range(0, 2)

        histogram_feature = np.zeros((_N, _angle, len(_distance)))

        for _i in range(_angle):
            # angle range
            angle_matrix = (theta > (2 / _angle * _i)) * (theta <= (2 / _angle * (_i + 1)))
            for j in range(1, len(_distance)):
                distance_matrix = (dist < _distance[j]) * (dist > _distance[j - 1])

                histogram_feature[:, _i, j - 1] = np.sum(angle_matrix * distance_matrix, axis=1)
        return histogram_feature

    def Cost_function_Shape_Context(histogram1, histogram2):
        """
        代价矩阵
        histogram1: N1*A*D
        histogram2: N2*A*D
        """
        A = histogram1.shape[1]
        D = histogram1.shape[2]
        N1 = histogram1.shape[0]
        N2 = histogram2.shape[0]
        assert histogram1.shape[1] == histogram2.shape[1]
        assert histogram1.shape[2] == histogram2.shape[2]
        cost = 0.5 * np.sum(np.sum(
            np.square(
                histogram1.reshape((N1, 1, A, D)) - histogram2.reshape((1, N2, A, D))) / (
                    histogram1.reshape((N1, 1, A, D)) + histogram2.reshape((1, N2, A, D)) + 0.000000001)
            , axis=-1), axis=-1)
        return cost

    def Cost_function_Local_Appearance(_img1, _img2, _sample_points1, _sample_points2):
        """
        Local Appearance
        """
        N1 = _sample_points1.shape[0]
        N2 = _sample_points2.shape[0]

        sobel1_x = cv2.Sobel(_img1, cv2.CV_64F, 1, 0, ksize=3)
        sobel1_y = cv2.Sobel(_img2, cv2.CV_64F, 0, 1, ksize=3)

        sobel2_x = cv2.Sobel(_img1, cv2.CV_64F, 1, 0, ksize=3)
        sobel2_y = cv2.Sobel(_img2, cv2.CV_64F, 0, 1, ksize=3)

        cos1 = sobel1_x[_sample_points1[:, 0], _sample_points1[:, 1]]
        cos2 = sobel2_x[_sample_points2[:, 0], _sample_points2[:, 1]]
        sin1 = sobel1_y[_sample_points1[:, 0], _sample_points1[:, 1]]
        sin2 = sobel2_y[_sample_points2[:, 0], _sample_points2[:, 1]]

        cost = 0.5 * np.sqrt(
            np.square(cos2.reshape(1, N2) - cos1.reshape(N1, 1)) + np.square(sin2.reshape(1, N2) - sin1.reshape(N1, 1))
        )
        return cost

    # 边缘检测
    _im = img1
    # 采样点
    points = np.array([np.where(_im == 255)[0], np.where(_im == 255)[1]]).T
    sample_points1 = Jitendra_Sample(points, _N=N, k=3)
    # sample_points1 = np.random.permutation(points)[:N]
    # 上下文直方图
    histogram_feature1 = Shape_Context(sample_points1, angle, distance)

    # image2高度与image1一致对齐：
    img2 = cv2.resize(img2, (int(img1.shape[0] / img2.shape[0] * img2.shape[1]), img1.shape[0]))
    # 边缘检测
    _im = img2
    # 采样点
    points = np.array([np.where(_im == 255)[0], np.where(_im == 255)[1]]).T
    sample_points2 = Jitendra_Sample(points, _N=N, k=3)
    # sample_points2 = np.random.permutation(points)[:N]
    # 上下文直方图
    histogram_feature2 = Shape_Context(sample_points2, angle, distance)

    # 代价矩阵
    # cost_matrix = Cost_function(histogram_feature1, histogram_feature2)
    cost_matrix = 0.5 * Cost_function_Shape_Context(histogram_feature1,
                                                    histogram_feature2) + 0.5 * Cost_function_Local_Appearance(img1,
                                                                                                               img2,
                                                                                                               sample_points1,
                                                                                                               sample_points2)

    # 匈牙利匹配
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    min_cost = cost_matrix[row_ind, col_ind].sum()
    return min_cost


det = ddddocr.DdddOcr(det=True, beta=True)

for i in range(50, 51):
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
                    Edge_detection(im[y1:y2, x1:x2]), bbox
                )
            )
        else:
            if x2 - x1 > 50 and y2 - y1 > 50:
                target_img_list.append(
                    CaptchaInfo(
                        Edge_detection(im[y1:y2, x1:x2]), bbox
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
    #      tar1 tar2 tar3 ...
    # src1  xx   xx   xx
    # src2  xx   xx   xx
    # src3  xx   xx   xx
    #  .    ..   ..   ..
    #  .    ..   ..   ..
    #  .    ..   ..   ..
    img_match_mat = np.zeros((len(src_img_list), len(target_img_list)), dtype=np.float32)
    for idx_i, src_img in enumerate(src_img_list):
        for idx_j, target_img in enumerate(target_img_list):
            img_match_mat[idx_i][idx_j] = context_shape_match(src_img.img, target_img.img, N=200, angle=60)
    print(f'构成图像配对矩阵：\n{img_match_mat}')
    row_indices, col_indices = linear_sum_assignment(img_match_mat)
    pairings = [(row, col) for row, col in zip(row_indices, col_indices)]
    print(f"图像配对情况：\n{pairings}")
    for row, col in pairings:
        src_img_list[row].target_position = target_img_list[col].position
    for idx, src_img in enumerate(src_img_list):
        im = cv2.putText(im, str(idx), (src_img.target_position[2], src_img.target_position[3]),
                         cv2.FONT_HERSHEY_SIMPLEX,
                         0.75, (255, 255, 255), 2)
        im = cv2.putText(im, str(idx), (src_img.position[2], src_img.position[3]),
                         cv2.FONT_HERSHEY_SIMPLEX,
                         0.75, (255, 255, 255), 2)

    # 配对完毕之后添加方框
    for idx, bbox in enumerate(bboxes):
        x1, y1, x2, y2 = bbox
        im = cv2.rectangle(im, (x1, y1), (x2, y2), (0, 255, 0), 2)
    plt.figure()
    plt.imshow(im)
    plt.show()
    cv2.imwrite(f'test_result_pic/result{i}.jpg', im)
    print(f'当前进度：{i + 1}/100')
