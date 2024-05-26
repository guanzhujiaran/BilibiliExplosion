import math
from dataclasses import field, dataclass

import cv2
import ddddocr
import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import linear_sum_assignment


def geetestCaptchaRecg(im: np.ndarray):
    """
    极验验证码获取中心坐标
    :param im: 极验的验证码图片原图，344*384的格式
    :return:返回从左到右每一个目标点位的中心坐标[[x1,y1],[x2,y2]...]
    """

    def context_shape_match(img1, img2, N=100, angle=12, distance=None):
        """
        图形匹配
        path1: 图片路径1
        path2: 图片路径2
        N: 采样点数
        angle: 上下文极坐标角度划分个数
        """

        if distance is None:
            distance = [0, 0.125, 0.25, 0.5, 1.0, 2.0]

        def Edge_detection(img, kernel_size=(3, 3), thresh1=50, thresh2=150):
            """
            边缘检测算法
            1. 高斯滤波平滑图像
            2. Canny算子检测边缘
            """
            img = cv2.GaussianBlur(img, kernel_size, 0)
            canny = cv2.Canny(img, thresh1, thresh2)
            return canny

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
            i = np.unique(np.where(dist < 999999999999)[0])
            sample_points = NStart_sample_points[i]
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
            N = _points.shape[0]
            dist = np.sqrt(np.sum(np.square(_points.reshape((1, N, 2)) - _points.reshape((N, 1, 2))), axis=-1))

            # 距离均值
            mean_dist = np.sum(dist) / (N * N - N)
            # 除以均值，减少缩放敏感性
            dist = np.log(dist / mean_dist + 0.000000000001) + np.eye(N, dtype=int) * 999
            # print(dist)

            # 角度计算
            theta = np.arctan((_points[:, 1].reshape(1, N) - _points[:, 1].reshape(N, 1)) / (
                    _points[:, 0].reshape(1, N) - _points[:, 0].reshape(N, 1) + 0.000000000001)) / math.pi + (
                            (_points[:, 0].reshape(1, N) - _points[:, 0].reshape(N, 1)) < 0).astype(
                int) + 0.5  # range(0, 2)

            histogram_feature = np.zeros((N, _angle, len(_distance)))

            for i in range(_angle):
                # angle range
                angle_matrix = (theta > (2 / _angle * i)) * (theta <= (2 / _angle * (i + 1)))
                for j in range(1, len(_distance)):
                    distance_matrix = (dist < _distance[j]) * (dist > _distance[j - 1])

                    histogram_feature[:, i, j - 1] = np.sum(angle_matrix * distance_matrix, axis=1)
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

            img1gray = cv2.cvtColor(_img1, cv2.COLOR_RGB2GRAY)
            img2gray = cv2.cvtColor(_img2, cv2.COLOR_RGB2GRAY)

            sobel1_x = cv2.Sobel(img1gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel1_y = cv2.Sobel(img1gray, cv2.CV_64F, 0, 1, ksize=3)

            sobel2_x = cv2.Sobel(img2gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel2_y = cv2.Sobel(img2gray, cv2.CV_64F, 0, 1, ksize=3)

            cos1 = sobel1_x[_sample_points1[:, 0], _sample_points1[:, 1]]
            cos2 = sobel2_x[_sample_points2[:, 0], _sample_points2[:, 1]]
            sin1 = sobel1_y[_sample_points1[:, 0], _sample_points1[:, 1]]
            sin2 = sobel2_y[_sample_points2[:, 0], _sample_points2[:, 1]]

            cost = 0.5 * np.sqrt(
                np.square(cos2.reshape(1, N2) - cos1.reshape(N1, 1)) + np.square(
                    sin2.reshape(1, N2) - sin1.reshape(N1, 1))
            )
            return cost

        # 边缘检测
        im = Edge_detection(img1)
        # 采样点
        points = np.array([np.where(im == 255)[0], np.where(im == 255)[1]]).T
        sample_points1 = Jitendra_Sample(points, _N=N, k=3)
        # sample_points1 = np.random.permutation(points)[:N]
        # 上下文直方图
        histogram_feature1 = Shape_Context(sample_points1, angle, distance)

        # image2高度与image1一致对齐：
        img2 = cv2.resize(img2, (int(img1.shape[0] / img2.shape[0] * img2.shape[1]), img1.shape[0]))
        # 边缘检测
        im = Edge_detection(img2)
        # 采样点
        points = np.array([np.where(im == 255)[0], np.where(im == 255)[1]]).T
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
        match = np.array([[x, y] for x, y in zip(row_ind, col_ind)])

        return match

    det = ddddocr.DdddOcr(det=True)

    with open("img_1.jpg", 'rb') as f:
        image = f.read()

    bboxes = det.detection(image)
    print(bboxes)

    @dataclass
    class CaptchaInfo:
        img: np.ndarray
        position: list[int, int, int, int]  # x1,y1,x2,y2
        target_position: list[int] = field(default_factory=list)
        is_target: bool = False  # 是否是上面的点选目标
        has_couple: bool = False  # 是否已经配对

    target_img_list = []
    src_img_list = []
    for idx, bbox in enumerate(bboxes):
        plt.figure()
        x1, y1, x2, y2 = bbox
        target_img = im[y1:y2, x1:x2]
        if y1 > 340:
            src_img_list.append(
                CaptchaInfo(
                    im, bbox
                )
            )
        else:
            target_img_list.append(
                CaptchaInfo(
                    im, bbox, is_target=True
                )
            )

    src_img_list.sort(key=lambda x: x.position[0])  # 排序

    for idx, src_img in enumerate(src_img_list):
        match = 99 * 100
        matched_target = None
        for target_img in target_img_list:
            if target_img.has_couple:
                continue
            matches = context_shape_match(src_img.img, target_img.img, distance=[0, 1, 2, 3, 4, 5, 6, 7])
            s = 0
            for x, y in matches:
                s += abs(y - x)
            if s < match:
                match = s
                src_img.target_position = target_img.position
                matched_target = target_img
        matched_target.has_couple = True

    return [[(x.target_position[0] + x.target_position[2]) / 2, (x.target_position[1] + x.target_position[3]) / 2] for x
            in src_img_list]
