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
        self.cfg_detection = config.get('detection', {})
        self.templates = self._load_templates(config)

    def _load_templates(self, config):
        # Carrega imagem de shiny, talk e botões de batalha
        assets_dir = config.get('assets', {}).get('templates_dir', 'assets/templates/')
        shiny_path = assets_dir + config.get('assets', {}).get('shiny_image', 'shiny.png')
        talk_path = assets_dir + config.get('assets', {}).get('talk_image', 'talk.png')
        fight_path = assets_dir + config.get('assets', {}).get('fight_image', 'fight.png')
        bag_path = assets_dir + config.get('assets', {}).get('bag_image', 'bag.png')
        pokemon_path = assets_dir + config.get('assets', {}).get('pokemon_image', 'pokemon.png')
        run_path = assets_dir + config.get('assets', {}).get('run_image', 'run.png')
        return {
            'shiny': cv2.imread(shiny_path),
            'talk': cv2.imread(talk_path),
            'fight': cv2.imread(fight_path),
            'bag': cv2.imread(bag_path),
            'pokemon': cv2.imread(pokemon_path),
            'run': cv2.imread(run_path),
        }

    def detect_state(self, image):
        # 1. Verifica SHINY (Prioridade Absoluta)
        if self._detect_shiny(image):
            return GameState.SHINY_FOUND

        # 2. Verifica Botões de Batalha (qualquer um dos 4) via template matching
        # em uma única região ampla de combate (battle_area)
        battle_area = self.cfg_detection.get('battle_area')
        if battle_area and isinstance(battle_area, (list, tuple)) and len(battle_area) == 4:
            x1, y1, x2, y2 = battle_area
            battle_roi = image[y1:y2, x1:x2]
        else:
            battle_roi = image

        battle_templates = {
            'fight': 'fight',
            'items': 'bag',
            'pokemon': 'pokemon',
            'run': 'run',
        }

        battle_thresh = float(self.cfg_detection.get('battle_button_threshold', 0.75))

        for name, tpl_key in battle_templates.items():
            template = self.templates.get(tpl_key)
            if template is None:
                continue

            try:
                res = cv2.matchTemplate(battle_roi, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
            except cv2.error as e:
                logger.error(f"Erro em matchTemplate para {tpl_key}: {e}")
                continue

            if max_val >= battle_thresh:
                logger.debug(
                    f"Botão de batalha '{name}' detectado com score={max_val:.3f} (threshold={battle_thresh})"
                )
                return GameState.IN_BATTLE

        return GameState.EXPLORING

    def _detect_shiny(self, image):
        template = self.templates.get('shiny')
        if template is None:
            return False

        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        # Threshold configurável via settings.yaml (fallback 0.85)
        shiny_thresh = float(self.cfg_detection.get('shiny_threshold', 0.85))

        if max_val >= shiny_thresh:
            logger.info(f"Template de SHINY detectado com score={max_val:.3f} (threshold={shiny_thresh})")
            return True

        return False

    def get_battle_info(self, image):
        """Extrai nome do inimigo e HP"""
        enemy_name_img = self._crop_roi(image, self.rois['enemy_name'])
        # Apenas letras, traço e espaço para nomes de Pokémon
        enemy_name_raw = self.ocr.extract_text_optimized(
            enemy_name_img,
            whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz- ",
            invert_for_white_text=True
        )

        enemy_name = enemy_name_raw.replace("Lv", "").strip()
        
        return {
            "enemy_name": enemy_name,
            # Adicionar leitura de HP e Level aqui usando as ROIs
        }

    def _crop_roi(self, image, roi_coords):
        """Recorta ROI aceitando formatos [x,y,w,h] ou [x1,y1,x2,y2]."""
        if not roi_coords or len(roi_coords) != 4:
            return image

        x1, y1, x2, y2 = roi_coords

        # Se parecer [x,y,w,h] (w/h positivos pequenos), converte para [x1,y1,x2,y2]
        if x2 <= x1 or y2 <= y1:
            x, y, w, h = roi_coords
            x1, y1, x2, y2 = int(x), int(y), int(x + w), int(y + h)

        h_img, w_img = image.shape[:2]
        x1 = max(0, min(int(x1), w_img - 1))
        x2 = max(0, min(int(x2), w_img))
        y1 = max(0, min(int(y1), h_img - 1))
        y2 = max(0, min(int(y2), h_img))

        if x2 <= x1 or y2 <= y1:
            return image

        return image[y1:y2, x1:x2]