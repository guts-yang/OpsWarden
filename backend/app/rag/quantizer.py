"""向量量化：网格吸附 anchor_vec = round(v / ε) * ε。"""
import hashlib

import numpy as np


def quantize_vector(vec: list[float], epsilon: float) -> np.ndarray:
    v = np.asarray(vec, dtype=np.float64)
    return np.round(v / epsilon) * epsilon


def quant_key_from_vector(quantized: np.ndarray) -> str:
    """稳定锚点去重用 SHA256（量化后 float32 字节）。"""
    q = np.asarray(quantized, dtype=np.float32)
    return hashlib.sha256(q.tobytes()).hexdigest()
