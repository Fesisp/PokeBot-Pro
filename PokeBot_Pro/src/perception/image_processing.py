import cv2
import numpy as np


class ImageProcessor:
    """Utilitários de processamento de imagem para apoiar OCR e detecção.

    Hoje foca em duas funções principais:
    - process_dynamic_background_text: isola texto branco em botões/labels coloridos
    - extract_roi: recorte seguro de regiões da tela por coordenadas absolutas
    """

    def __init__(self):
        pass

    def process_dynamic_background_text(self, image):
        """Isola texto branco brilhante em fundo colorido (botões de moves / HUD).

        Estratégia:
        - Faz upscale 3x para suavizar pixel art
        - Converte para HSV e filtra apenas regiões de baixo croma (quase branco)
        - Remove ruído e engrossa traços para Tesseract
        - Adiciona padding branco para evitar corte nas bordas
        """
        if image is None or image.size == 0:
            return image

        # Upscaling (3x) com interpolação cúbica
        h, w = image.shape[:2]
        img_big = cv2.resize(image, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)

        # Converter para HSV
        hsv = cv2.cvtColor(img_big, cv2.COLOR_BGR2HSV)

        # Filtro de branco: baixa saturação, alto valor
        lower_white = np.array([0, 0, 140])
        upper_white = np.array([180, 60, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)

        # Pequena limpeza de ruído e leve engrossamento
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Inverte para texto preto em fundo branco
        inverted = cv2.bitwise_not(mask)
        inverted = cv2.erode(inverted, kernel, iterations=1)

        # Padding branco para o Tesseract não cortar letras
        final_img = cv2.copyMakeBorder(
            inverted, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )

        return final_img

    def extract_roi(self, image, roi_coords):
        """Extrai ROI a partir de [x1, y1, x2, y2], com clamps de segurança."""
        if image is None or image.size == 0:
            return None
        if not roi_coords or len(roi_coords) != 4:
            return None

        x1, y1, x2, y2 = roi_coords

        h, w = image.shape[:2]
        x1, y1 = max(0, int(x1)), max(0, int(y1))
        x2, y2 = min(w, int(x2)), min(h, int(y2))

        if x2 <= x1 or y2 <= y1:
            return None

        return image[y1:y2, x1:x2]
