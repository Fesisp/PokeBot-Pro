import cv2
import numpy as np
import pytesseract
from loguru import logger

class OCREngine:
    def __init__(self, tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def extract_text_optimized(self, image, whitelist=None, invert_for_white_text=False):
        """Extrai texto com pré-processamento forte e suporte a texto branco.

        - Faz upscale para melhorar fontes pequenas.
        - Aplica sharpen + binarização.
        - Quando ``invert_for_white_text`` é True, destaca texto branco/brilhante.
        - Aceita ``whitelist`` de caracteres para melhorar precisão.
        """
        try:
            if image is None or image.size == 0:
                return ""

            # Upscale para melhorar leitura de fontes pequenas
            img_big = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

            if invert_for_white_text:
                # Converter para HSV e pegar apenas regiões bem claras (texto branco)
                hsv = cv2.cvtColor(img_big, cv2.COLOR_BGR2HSV)
                lower_white = np.array([0, 0, 200])
                upper_white = np.array([255, 60, 255])
                mask = cv2.inRange(hsv, lower_white, upper_white)
                ocr_img = mask
            else:
                # Modo genérico: escala de cinza
                gray = cv2.cvtColor(img_big, cv2.COLOR_BGR2GRAY)
                # Sharpen leve para destacar bordas do texto
                kernel = np.array([[0, -1, 0],
                                   [-1, 5, -1],
                                   [0, -1, 0]])
                sharp = cv2.filter2D(gray, -1, kernel)
                # Binarização adaptativa
                ocr_img = cv2.adaptiveThreshold(
                    sharp, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,
                    2
                )

            # Configuração do Tesseract
            config = "--psm 7 --oem 1"
            if whitelist:
                config += f" -c tessedit_char_whitelist={whitelist}"

            text = pytesseract.image_to_string(ocr_img, config=config)
            return text.strip()
        except Exception as e:
            logger.error(f"Erro no OCR Otimizado: {e}")
            return ""