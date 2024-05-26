import time
from dataclasses import dataclass, field
import cv2
import ddddocr
import numpy as np
import torch
from PIL import Image
from scipy.optimize import linear_sum_assignment
from sklearn.metrics.pairwise import cosine_similarity
from cn_clip.clip import load_from_name
from loguru import logger
from matplotlib import pyplot as plt

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = load_from_name("ViT-H-14", device=device, download_root='./clip_model/')


@dataclass
class CaptchaInfo:
    img: np.ndarray
    position: list[int, int, int, int]  # x1,y1,x2,y2
    target_position: list[int] = field(default_factory=list)
    embeddings: np.ndarray = field(default_factory=list)


def get_single_image_embedding(my_image: np.ndarray) -> np.ndarray:
    _image = preprocess(
        Image.fromarray(my_image),
    ).unsqueeze(0).to(device)

    embedding = model.encode_image(_image)
    # 将嵌入转换为NumPy数组
    embedding_as_np = embedding.cpu().detach().numpy()

    return embedding_as_np


def get_img_diff_score(captcha_info1: CaptchaInfo, captcha_info2: CaptchaInfo) -> int:
    # plt.subplot(1, 2, 1) # 查看对应的图片和相似度得分
    # plt.imshow(captcha_info1.img)
    # plt.subplot(1, 2, 2)
    # plt.imshow(captcha_info2.img)
    # plt.show()
    sim_score = cosine_similarity(captcha_info1.embeddings, captcha_info2.embeddings)
    return 1 - sim_score[0][0]  # 因为匈牙利算法需要的是成本矩阵，与相似性成逆相关


det = ddddocr.DdddOcr(det=True, beta=False,show_ad=False,use_gpu=True)



for i in range(100):
    start_ts=int(time.time())
    img_path = f"test_pic/{i}.jpg"
    with open(img_path, 'rb') as f:
        image = f.read()

    bboxes = det.detection(image)

    print(f'检测图框：{bboxes}')

    im = cv2.imread(img_path)

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
        for bbox in bboxes:
            x1, y1, x2, y2 = bbox
            im = cv2.rectangle(im, (x1, y1), (x2, y2), color=(0, 0, 255), thickness=2)
        cv2.imwrite(f'test_failed_pic/{i}.jpg', im)
        continue
    for _s in src_img_list:
        _s.embeddings = get_single_image_embedding(_s.img)
    for _t in target_img_list:
        _t.embeddings = get_single_image_embedding(_t.img)

    img_match_mat = np.zeros((len(src_img_list), len(target_img_list)), dtype=np.float32)
    for idx_i, src_img in enumerate(src_img_list):
        for idx_j, target_img in enumerate(target_img_list):
            img_match_mat[idx_i][idx_j] = get_img_diff_score(src_img, target_img)


    print(f'图片【{i}】 构成图像配对矩阵({img_match_mat.shape})：\n{img_match_mat}')
    row_indices, col_indices = linear_sum_assignment(img_match_mat)
    pairings = [(row, col) for row, col in zip(row_indices, col_indices)]
    print(f"图片【{i}】 图像配对情况：\n{pairings}")
    spend_ts=int(time.time()) - start_ts
    print(f'图片【{i}】 本次识别耗时：{spend_ts}秒')
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

