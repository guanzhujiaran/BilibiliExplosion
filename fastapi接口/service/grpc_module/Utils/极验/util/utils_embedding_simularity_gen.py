from enum import Enum

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity, sigmoid_kernel, laplacian_kernel, rbf_kernel, polynomial_kernel, \
    linear_kernel, chi2_kernel, additive_chi2_kernel
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize

class SimilarityType(str, Enum):
    COSINE_SIMILARITY = "cosine_similarity"
    SIGMOID_KERNEL = "sigmoid_kernel"
    LAPLACIAN_KERNEL = "laplacian_kernel"
    RBF_KERNEL = "rbf_kernel"
    POLYNOMIAL_KERNEL = "polynomial_kernel"
    LINEAR_KERNEL = "linear_kernel"
    CHI2_KERNEL = "chi2_kernel"
    ADDITIVE_CHI2_KERNEL = "additive_chi2_kernel"
    KNN_SIMILARITY = "knn_similarity"


class PlugSimilarityGen:
    @staticmethod
    def cosine_similarity(vect1, vect2) -> float:
        return cosine_similarity(vect1, vect2)[0][0]

    @staticmethod
    def sigmoid_kernel(vect1, vect2) -> float:
        return sigmoid_kernel(vect1, vect2)[0][0]

    @staticmethod
    def laplacian_kernel(vect1, vect2) -> float:
        return laplacian_kernel(vect1, vect2)[0][0]

    @staticmethod
    def rbf_kernel(vect1, vect2) -> float:
        return rbf_kernel(vect1, vect2)[0][0]

    @staticmethod
    def polynomial_kernel(vect1, vect2) -> float:
        return polynomial_kernel(vect1, vect2)[0][0]

    @staticmethod
    def linear_kernel(vect1, vect2) -> float:
        return linear_kernel(vect1, vect2)[0][0]

    @staticmethod
    def chi2_kernel(vect1, vect2) -> float:
        return chi2_kernel(vect1, vect2)[0][0]

    @staticmethod
    def additive_chi2_kernel(vect1, vect2) -> float:
        return additive_chi2_kernel(vect1, vect2)[0][0]
    @staticmethod
    def knn_similarity(vect1, vect2) -> float:

        # 创建一个包含所有向量的数据集
        dataset = np.vstack(vect2)
        model_knn = NearestNeighbors(metric='cosine', algorithm='brute')
        # 拟合模型
        model_knn.fit(dataset)
        # 查询vector_a的最相似向量
        distances, indices = model_knn.kneighbors(vect1, n_neighbors=1)
        # 输出结果
        nearest_distance = 1 - distances[0][0]  # 转换为相似度，因为KNN给出的是距离
        return nearest_distance

    @staticmethod
    def get_similarity_gen(similarity_type:SimilarityType):
        if similarity_type == SimilarityType.COSINE_SIMILARITY:
            return PlugSimilarityGen.cosine_similarity
        elif similarity_type == SimilarityType.SIGMOID_KERNEL:
            return PlugSimilarityGen.sigmoid_kernel
        elif similarity_type == SimilarityType.LAPLACIAN_KERNEL:
            return PlugSimilarityGen.laplacian_kernel
        elif similarity_type == SimilarityType.RBF_KERNEL:
            return PlugSimilarityGen.rbf_kernel
        elif similarity_type == SimilarityType.POLYNOMIAL_KERNEL:
            return PlugSimilarityGen.polynomial_kernel
        elif similarity_type == SimilarityType.LINEAR_KERNEL:
            return PlugSimilarityGen.linear_kernel
        elif similarity_type == SimilarityType.CHI2_KERNEL:
            return PlugSimilarityGen.chi2_kernel
        elif similarity_type == SimilarityType.ADDITIVE_CHI2_KERNEL:
            return PlugSimilarityGen.additive_chi2_kernel
        elif similarity_type == SimilarityType.KNN_SIMILARITY:
            return PlugSimilarityGen.knn_similarity
        else:
            raise Exception("Unknown similarity type")
