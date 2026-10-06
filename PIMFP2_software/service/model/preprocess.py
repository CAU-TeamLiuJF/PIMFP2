import cv2
import numpy as np
from PIL.Image import Image


def preprocess(image: Image, target_size: tuple[int, int], crop_box: tuple[float, float, float, float]) -> np.ndarray:
    image = image.convert('RGB')
    cropped = image.crop(crop_box)

    cropped_np = np.array(cropped)
    resized_rgb = cv2.resize(cropped_np, target_size, interpolation=cv2.INTER_AREA)

    lab = cv2.cvtColor(resized_rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)

    lab_clahe = cv2.merge((l_clahe, a, b))
    return cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2RGB)
