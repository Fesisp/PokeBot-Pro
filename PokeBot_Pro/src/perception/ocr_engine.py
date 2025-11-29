import cv2
import numpy as np
import pytesseract
from loguru import logger

class OCREngine:
    def __init__(self, tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def extract_text_optimized(self, image, whitelist=None):
        """
        Aplica filtro para isolar texto branco (comum em RPGs) e roda OCR.
        """
        try:
            # Upscale para melhorar leitura de fontes pequenas
            img_big = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            
            # Converter para HSV e filtrar cor branca/brilhante
            hsv = cv2.cvtColor(img_big, cv2.COLOR_BGR2HSV)
            lower_white = np.array([0, 0, 180])
            upper_white = np.array([255, 50, 255])
            mask = cv2.inRange(hsv, lower_white, upper_white)
            
            # Configuração do Tesseract
            config = "--psm 7 --oem 1"
            if whitelist:
                config += f" -c tessedit_char_whitelist='{whitelist}'"
            
            text = pytesseract.image_to_string(mask, config=config)
            return text.strip()
        except Exception as e:
            logger.error(f"Erro no OCR Otimizado: {e}")
            return ""