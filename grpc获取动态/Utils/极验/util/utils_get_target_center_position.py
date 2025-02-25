"""
顺序获取点选验证码的目标中心位置，返回[[x1,y1],[x2,y2]]每个代表中心坐标
"""
import json
import os
import re
import threading
import time
from io import BytesIO
import cv2
import ddddocr
import subprocess
from functools import partial
from fastapi接口.log.base_log import Voucher352_logger

subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")
import execjs
import numpy as np
import open_clip
import pandas as pd
import torch
from PIL import Image
from curl_cffi import requests
from matplotlib import pyplot as plt
from scipy.optimize import linear_sum_assignment
from grpc获取动态.Utils.极验.models.captcha_models import CaptchaInfo, CaptchaResultInfo
from grpc获取动态.Utils.极验.util.utils_embedding_pic_preprocess import PlugPicPreprocess, PicPreprocessType
from grpc获取动态.Utils.极验.util.utils_embedding_simularity_gen import PlugSimilarityGen, SimilarityType
from utl.designMode.singleton import Singleton


def imshow(im):
    plt.figure()
    plt.imshow(im)
    plt.show()


class CaptchaDetector:
    _lock = threading.Lock()
    _instance = None
    class LogPath:
        detect_result_pic: str = 'log/detect_result_pic/'
        detect_failed_pic: str = 'log/detect_failed_pic/'

        def init(self, root_path: str):
            if not os.path.exists(os.path.join(root_path, self.detect_result_pic)):
                os.makedirs(os.path.join(root_path, self.detect_result_pic))
            if not os.path.exists(os.path.join(root_path, self.detect_failed_pic)):
                os.makedirs(os.path.join(root_path, self.detect_failed_pic))

    class PluginChoose:
        pic_preprocess = PlugPicPreprocess.pic_preprocess_gen(PicPreprocessType.NonProcess)
        similarity_func = PlugSimilarityGen.get_similarity_gen(SimilarityType.COSINE_SIMILARITY)

    def __init__(self):
        self.model = None
        self.preprocess = None
        self.det = ddddocr.DdddOcr(det=True, beta=True, show_ad=False, use_gpu=True)
        self.ocr = ddddocr.DdddOcr(det=False, ocr=True, beta=True, show_ad=False, use_gpu=True)
        self.__device: str = "cuda" if torch.cuda.is_available() else "cpu"
        self.current_file_root_dir = os.path.dirname(os.path.abspath(__file__))  # 就是当前文件的路径目录

        self.log_switch = True  # 开启日志，记录图片
        self.log_path = self.LogPath()
        self.log_path.init(self.current_file_root_dir)
        self.inited = False

    def init_model(self):
        if self.inited:
            return
        self.inited = True
        Voucher352_logger.critical('初始化一个CLIP模型实例')
        self.model, _, self.preprocess = open_clip.create_model_and_transforms('ViT-B-16-SigLIP',
                                                                               pretrained='webli',
                                                                               device=self.__device,
                                                                               )
        Voucher352_logger.critical('CLIP模型实例初始化完成')

    def gen_cost_matrix(self, origin_matrix):
        """
        将将numpy的nxn的矩阵，按行从大到小将排名插入原顺序，遇到大小相同的数据，就按照先遇到的顺序排名，最小的数字从1开始
        :param origin_matrix:
[
    [0.5488135  0.71518937 0.60276338 0.54488318 0.4236548 ]
    [0.64589411 0.43758721 0.891773   0.96366276 0.38344152]
    [0.79172504 0.52889492 0.56804456 0.92559664 0.07103606]
    [0.0871293  0.0202184  0.83261985 0.77815675 0.87001215]
    [0.97861834 0.79915856 0.46147936 0.78052918 0.11827443]
]
        :return:
[
    [3 1 2 4 5]
    [3 4 2 1 5]
    [2 4 3 1 5]
    [4 5 2 3 1]
    [1 2 4 3 5]
]
        """
        # 将numpy数组转换为pandas DataFrame
        df = pd.DataFrame(origin_matrix)
        # 按行对DataFrame进行排名，method='first'表示在相同值的情况下保持原始顺序
        df_ranked = df.rank(axis=1, method='first', ascending=False)
        # 将排名结果转换回numpy数组，并向下取整（因为rank()的结果是浮点数）
        arr_ranked = df_ranked.values.astype(int)
        return arr_ranked

    # region 插件替换位置

    def _get_single_image_embedding(self, my_image: np.ndarray) -> np.ndarray:
        """
        获取单个图片的向量 总共1024个维度
        :param my_image:
        :return:
        """
        if self.model is None:
            self.init_model()
        _image = self.preprocess(
            Image.fromarray(my_image),
        ).unsqueeze(0).to(self.__device)

        embedding = self.model.encode_image(_image)
        # 将嵌入转换为NumPy数组
        embedding_as_np = embedding.cpu().detach().numpy()

        return embedding_as_np

    def _get_img_diff_score(self, captcha_info1: CaptchaInfo, captcha_info2: CaptchaInfo) -> float:
        """
        图片相似度越高，得分也越高
        :param captcha_info1:
        :param captcha_info2:
        :return:
        """
        # plt.subplot(1, 2, 1) # 查看对应的图片和相似度得分
        # plt.imshow(captcha_info1.img)
        # plt.subplot(1, 2, 2)
        # plt.imshow(captcha_info2.img)
        # plt.show()
        # print(captcha_info1.embeddings)
        # print(captcha_info2.embeddings)
        sim_score = self.PluginChoose.similarity_func(captcha_info1.embeddings, captcha_info2.embeddings)
        Voucher352_logger.debug(f'【{self.PluginChoose.similarity_func.__name__}】相似度得分：{sim_score}')
        return sim_score  # 因为匈牙利算法需要的是成本矩阵，与相似度得分成逆相关

    def _get_preprocessed_pic(self, im: np.ndarray) -> np.ndarray:
        """
        根据模型的图片大小，resize成同一个大小的图片
        :param im:
        :return:
        """
        return self.PluginChoose.pic_preprocess(src=im, dsize=(224, 224, 3))

    # endregion

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
        im = origin_im.copy()
        for idx, bbox in enumerate(bboxes):
            x1, y1, x2, y2 = bbox
            im = cv2.rectangle(origin_im, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.imwrite(os.path.join(self.current_file_root_dir, file_name), im)

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

        Voucher352_logger.debug(f'\n检测图框：{bboxes}')

        target_img_list = []
        src_img_list = []
        for idx, bbox in enumerate(bboxes):
            x1, y1, x2, y2 = bbox
            box_img = im[y1:y2, x1:x2].copy()
            if y1 > 340:
                src_img_list.append(
                    CaptchaInfo(
                        self._get_preprocessed_pic(box_img), bbox,
                    )
                )
            else:
                if x2 - x1 > 50 and y2 - y1 > 50:
                    target_img_list.append(
                        CaptchaInfo(
                            self._get_preprocessed_pic(box_img), bbox,
                        )
                    )
        if len(target_img_list) < len(src_img_list):
            Voucher352_logger.error(f'ddddocr识别失败！图像识别数量不足\n{bboxes}')
            self.save_draw_rectangle(im, bboxes, self.log_path.detect_failed_pic + f'ddddocr_det_fail_{img_name}')
            captcha_result_info = CaptchaResultInfo(None, img_name, im, bboxes)
            return captcha_result_info

        for _s in src_img_list:
            _s.embeddings = self._get_single_image_embedding(_s.img)
        for _t in target_img_list:
            _t.embeddings = self._get_single_image_embedding(_t.img)

        origin_cost_match_matrix = np.zeros((len(src_img_list), len(target_img_list)), dtype=np.float32)
        for idx_i, src_img in enumerate(src_img_list):
            for idx_j, target_img in enumerate(target_img_list):
                origin_cost_match_matrix[idx_i][idx_j] = self._get_img_diff_score(src_img, target_img)

        cost_match_matrix = self.gen_cost_matrix(origin_cost_match_matrix)
        row_indices, col_indices = linear_sum_assignment(cost_match_matrix)
        pairings = [(row, col) for row, col in zip(row_indices, col_indices)]
        spend_ts = int(time.time()) - start_ts

        Voucher352_logger.debug(
            f"\n图片【{img_name}】 \n图像配对情况：\n{pairings}\n原矩阵：{origin_cost_match_matrix}\n构成图像配对成本矩阵({cost_match_matrix.shape})：\n{cost_match_matrix}\n"
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
            self.save_draw_rectangle(im, bboxes, self.log_path.detect_result_pic + f'{img_name}')
        captcha_result_info = CaptchaResultInfo(ret_position, img_name, im, bboxes)
        return captcha_result_info

    def ddddocr_js_break(self, gt, challenge):
        url = 'https://api.geevisit.com/get.php'
        ajax_url = "http://api.geevisit.com/ajax.php"

        def get_c_s():
            params = {
                'gt': gt,
                'challenge': challenge,
                "callback": f"geetest_{int(time.time() * 1000)}",
            }
            resp = requests.get(url, params=params)
            resp_text = resp.text
            res = ''.join(re.findall('.*\((.*?)\)', resp_text))
            res = json.loads(res)
            _c = res['data']['c']
            _s = res['data']['s']
            return _c, _s

        def get_type():
            params = {
                'gt': gt,
                'challenge': challenge,
                "callback": f"geetest_{int(time.time() * 1000)}",
            }
            resp = requests.get(ajax_url, params=params)
            resp_text = resp.text
            res = ''.join(re.findall('.*\((.*?)\)', resp_text))
            res = json.loads(res)
            result = res['data']['result']
            return result

        def get_new_c_s_args():
            params = {
                'gt': gt,
                'challenge': challenge,
                "is_next": True,
                "offline": False,
                "isPC": True,
                "type": _type,
                "lang": "zh-cn",
                "https": True,
                "protocol": "https://",
                "product": 'popup',
                "api_server": "api.geevisit.com",
                "autoReset": True,
                "width": "100%",
                "callback": f"geetest_{int(time.time() * 1000)}",
            }
            resp = requests.get(url, params=params)
            resp_text = resp.text
            res = ''.join(re.findall('.*\((.*?)\)', resp_text))
            res = json.loads(res)
            _c = res['data']['c']
            _s = res['data']['s']
            static_server = res['data']['static_servers'][0]
            pic_url = f'https://{static_server}{res["data"]["pic"].strip("/")}'
            return _c, _s, pic_url

        def _get_max_probability_char(char_result):
            # 根据概率选择最大可能性的字符
            probabilities = char_result['probability'][0]
            max_index = probabilities.index(max(probabilities))
            return char_result['charsets'][max_index]

        def calculate_key(pic_url):
            pic_img = self._get_geetest_pic(pic_url)
            pic_img = Image.open(BytesIO(pic_img))

            # 裁剪背景图和文本图
            bg_img = pic_img.crop((0, 0, 344, 344))
            text_img = pic_img.crop((0, 345, 116, 385))

            # 识别文本图
            text_bytes = BytesIO()
            text_img.save(text_bytes, format='PNG')
            text_bytes.seek(0)
            s_text = self.ocr.classification(text_bytes.read(), False)
            self.ocr.set_ranges(s_text)
            self.det.set_ranges(s_text)
            bg_bytes = BytesIO()
            bg_img.save(bg_bytes, format='PNG')
            bg_bytes.seek(0)
            det = self.det.detection(bg_bytes.read())

        def generate_w():
            click_w = execjs.compile('./js/click.js')
            return click_w.call("click_result", key, gt, challenge, str(c), s, "abcdefghijklmnop")

        def verify():
            params = {
                'gt': gt,
                'challenge': challenge,
                "callback": f"geetest_{int(time.time() * 1000)}",
            }
            resp = requests.get(ajax_url, params=params)
            resp_text = resp.text
            res = ''.join(re.findall('.*\((.*?)\)', resp_text))
            res = json.loads(res)
            return res['data']['result'], res['data']['validate']

        _, _ = get_c_s()
        _type = get_type()
        c, s, args = get_new_c_s_args()
        before_calculate_key = time.time()
        key = calculate_key(args)
        w = generate_w()
        w_use_time = time.time() - before_calculate_key
        print("w生成时间：", w_use_time)
        if w_use_time < 2:
            time.sleep(2 - w_use_time)
        (msg, validate) = verify()
        print(validate)


captcha_detector = CaptchaDetector()
