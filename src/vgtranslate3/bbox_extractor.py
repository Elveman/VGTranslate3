import cv2
import numpy as np
from PIL import Image
from typing import List, Dict


def extract_bounding_boxes(image: Image.Image) -> List[Dict[str, int]]:
    """
    Extract bounding boxes from image using OpenCV heuristics.
    
    Algorithm:
    1. Convert to grayscale
    2. Binary threshold (Otsu)
    3. Find contours
    4. Filter by area (text regions)
    5. Return list of {x, y, w, h}
    
    Args:
        image: PIL Image
        
    Returns:
        List of bounding boxes: [{"x": x, "y": y, "w": w, "h": h}, ...]
    """
    img_array = np.array(image.convert("L"))
    
    _, binary = cv2.threshold(
        img_array, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=2)
    eroded = cv2.erode(dilated, kernel, iterations=1)
    
    contours, _ = cv2.findContours(
        eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    boxes = []
    img_w, img_h = image.size
    
    min_area = (img_w * img_h) * 0.0001
    max_area = (img_w * img_h) * 0.3
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        
        if min_area <= area <= max_area:
            boxes.append({
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h)
            })
    
    boxes.sort(key=lambda b: (b["y"] // 10 * 10, b["x"]))
    
    return boxes


def match_texts_to_boxes(texts: List[str], boxes: List[Dict]) -> List[Dict]:
    """
    Match texts to bounding boxes (simple ordering).
    
    Args:
        texts: List of text strings
        boxes: List of bounding boxes
        
    Returns:
        List of blocks with text and bbox
    """
    blocks = []
    
    for i, text in enumerate(texts):
        if i < len(boxes):
            blocks.append({
                "text": text,
                "bbox": boxes[i]
            })
        else:
            blocks.append({
                "text": text,
                "bbox": {"x": 0, "y": 0, "w": 0, "h": 0}
            })
    
    return blocks
