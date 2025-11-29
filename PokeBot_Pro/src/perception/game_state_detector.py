import cv2
import numpy as np
import winsound
from enum import Enum
from loguru import logger

class GameState(Enum):
    EXPLORING = "exploring"
    IN_BATTLE = "in_battle"
    SHINY_FOUND = "shiny_found"
    UNKNOWN = "unknown"

class GameStateDetector:
    def __init__(self, screen_capture, ocr_engine, config):
        self.cap = screen_capture
        self.ocr = ocr_engine
        self.rois = config.get('rois', {})
        self.templates = self._load_templates(config)

    def _load_templates(self, config):
        # Carrega imagem de shiny e goto
        assets_dir = config.get('assets', {}).get('templates_dir', 'assets/templates/')
        shiny_path = assets_dir + config.get('assets', {}).get('shiny_image', 'shiny.png')
        return {
            'shiny': cv2.imread(shiny_path)
        }

    def detect_state(self, image):
        # 1. Verifica SHINY (Prioridade Absoluta)
        if self._detect_shiny(image):
            return GameState.SHINY_FOUND

        # 2. Verifica Botões de Batalha (Lógica dos 4 botões)
        # Verifica apenas o botão FIGHT para ser rápido, ou todos para certeza
        fight_roi = self._crop_roi(image, self.rois['btn_fight'])
        # Aqui você poderia usar template matching no botão Fight, 
        # mas a presença de texto "Fight" via OCR também funciona e é robusta
        text = self.ocr.extract_text_optimized(fight_roi)
        
        if "ight" in text or "FIGHT" in text:
            return GameState.IN_BATTLE

        return GameState.EXPLORING

    def _detect_shiny(self, image):
        template = self.templates.get('shiny')
        if template is None: return False
        
        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return max_val > 0.85

    def get_battle_info(self, image):
        """Extrai nome do inimigo e HP"""
        enemy_name_img = self._crop_roi(image, self.rois['enemy_name'])
        enemy_name = self.ocr.extract_text_optimized(enemy_name_img)
        
        return {
            "enemy_name": enemy_name,
            # Adicionar leitura de HP e Level aqui usando as ROIs
        }

    def _crop_roi(self, image, roi_coords):
        # roi_coords = [x1, y1, x2, y2]
        x1, y1, x2, y2 = roi_coords
        return image[y1:y2, x1:x2]