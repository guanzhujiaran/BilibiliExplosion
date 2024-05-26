"""
顺序获取点选验证码的目标中心位置，返回[[x1,y1],[x2,y2]]每个代表中心坐标
"""
import os
import time
import cv2
import ddddocr
import numpy as np
import torch
from PIL import Image
from cn_clip.clip import load_from_name
from curl_cffi import requests
from loguru import logger
from scipy.optimize import linear_sum_assignment
from sklearn.metrics.pairwise import cosine_similarity
from grpc获取动态.Utils.极验.models.captcha_models import CaptchaInfo, CaptchaResultInfo


def get_img_diff_score(captcha_info1: CaptchaInfo, captcha_info2: CaptchaInfo) -> int:
    # plt.subplot(1, 2, 1) # 查看对应的图片和相似度得分
    # plt.imshow(captcha_info1.img)
    # plt.subplot(1, 2, 2)
    # plt.imshow(captcha_info2.img)
    # plt.show()
    sim_score = cosine_similarity(captcha_info1.embeddings, captcha_info2.embeddings)
    return 1 - sim_score[0][0]  # 因为匈牙利算法需要的是成本矩阵，与相似性成逆相关


class CaptchaDetector:
    instance = None
    det = ddddocr.DdddOcr(det=True, beta=False, show_ad=False, use_gpu=True)
    __device: str = "cuda" if torch.cuda.is_available() else "cpu"
    current_file_root_dir = os.path.dirname(os.path.abspath(__file__))  # 就是当前文件的路径目录
    model, preprocess = load_from_name("ViT-H-14", device=__device,
                                       download_root=os.path.join(current_file_root_dir, 'clip_model/'))
    log_switch = True  # 开启日志，记录图片

    def __new__(cls, *args, **kwargs):  # 单例模式
        if cls.instance is None:
            cls.instance = object.__new__(cls)
        return cls.instance

    def _get_single_image_embedding(self, my_image: np.ndarray) -> np.ndarray:
        """
        获取单个图片的向量 总共1024个维度
        :param my_image:
        :return:
        """
        _image = self.preprocess(
            Image.fromarray(my_image),
        ).unsqueeze(0).to(self.__device)

        embedding = self.model.encode_image(_image)
        # 将嵌入转换为NumPy数组
        embedding_as_np = embedding.cpu().detach().numpy()

        return embedding_as_np

    def _get_geetest_pic(self, geetest_pic_url) -> bytes:
        pic_resp = requests.get(geetest_pic_url, impersonate='chrome120')
        return pic_resp.content

    def save_draw_rectangle(self, origin_im: np.ndarray, bboxes: list[list[int]], file_name: str):
        """
        保存图片在指定文件夹下
        :param origin_im:
        :param bboxes:
        :param file_name:
        :return:
        """
        for idx, bbox in enumerate(bboxes):
            x1, y1, x2, y2 = bbox
            im = cv2.rectangle(origin_im, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.imwrite(os.path.join(self.current_file_root_dir, file_name), origin_im)

    def detect(self, geetest_pic_url: str) -> CaptchaResultInfo:
        """
        传入极验图片地址，直接返回对应的点图结果，检测失败则返回None
        :param geetest_pic_url:
        :return:
        """
        start_ts = int(time.time())
        img_name = geetest_pic_url.split('/')[-1].split('?')[0]
        image_bytes: bytes = self._get_geetest_pic(geetest_pic_url)
        img_buffer_numpy = np.frombuffer(image_bytes, dtype=np.uint8)
        im = cv2.imdecode(img_buffer_numpy, flags=1)
        bboxes = self.det.detection(image_bytes)

        logger.debug(f'\n检测图框：{bboxes}')

        target_img_list = []
        src_img_list = []
        for idx, bbox in enumerate(bboxes):
            x1, y1, x2, y2 = bbox
            box_img = im[y1:y2, x1:x2]
            if y1 > 340:
                src_img_list.append(
                    CaptchaInfo(
                        box_img, bbox,
                    )
                )
            else:
                if x2 - x1 > 50 and y2 - y1 > 50:
                    target_img_list.append(
                        CaptchaInfo(
                            box_img, bbox,
                        )
                    )
        if len(target_img_list) < len(src_img_list):
            logger.error(f'ddddocr识别失败！图像识别数量不足\n{bboxes}')
            self.save_draw_rectangle(im, bboxes, f'log/detect_failed_pic/ddddocr识别失败_{img_name}')
            captcha_result_info = CaptchaResultInfo(None, img_name, im, bboxes)
            return captcha_result_info

        for _s in src_img_list:
            _s.embeddings = self._get_single_image_embedding(_s.img)
        for _t in target_img_list:
            _t.embeddings = self._get_single_image_embedding(_t.img)

        img_match_mat = np.zeros((len(src_img_list), len(target_img_list)), dtype=np.float32)
        for idx_i, src_img in enumerate(src_img_list):
            for idx_j, target_img in enumerate(target_img_list):
                img_match_mat[idx_i][idx_j] = get_img_diff_score(src_img, target_img)

        row_indices, col_indices = linear_sum_assignment(img_match_mat)
        pairings = [(row, col) for row, col in zip(row_indices, col_indices)]
        spend_ts = int(time.time()) - start_ts

        logger.debug(
            f"\n图片【{img_name}】 \n图像配对情况：\n{pairings}\n构成图像配对成本矩阵({img_match_mat.shape})：\n{img_match_mat}\n"
            f"本次识别耗时：{spend_ts}秒")
        for row, col in pairings:
            src_img_list[row].target_position = target_img_list[col].position
        ret_position = []
        for idx, src_img in enumerate(src_img_list):
            x1, y1, x2, y2 = src_img.target_position
            ret_position.append([(x1 + x2) / 2, (y1 + y2) / 2])
            if self.log_switch:
                im = cv2.putText(im, str(idx), (src_img.target_position[2], src_img.target_position[3]),
                                 cv2.FONT_HERSHEY_SIMPLEX,
                                 0.75, (255, 255, 255), 2)
                im = cv2.putText(im, str(idx), (src_img.position[2], src_img.position[3]),
                                 cv2.FONT_HERSHEY_SIMPLEX,
                                 0.75, (255, 255, 255), 2)
        if self.log_switch:
            self.save_draw_rectangle(im, bboxes, f'log/detect_result_pic/{img_name}')
        captcha_result_info = CaptchaResultInfo(ret_position, img_name, im, bboxes)
        return captcha_result_info
