import pyautogui
import random
import time
import cv2
import numpy as np


class InputSimulator:
    def __init__(self, config=None):
        # Desabilita o fail-safe para evitar paradas bruscas se o mouse for para o canto
        # CUIDADO: Isso impede que você pare o bot movendo o mouse para o canto!
        pyautogui.FAILSAFE = False
        self.cfg = config or {}
        self.rois = self.cfg.get('rois', {})
        self.move_duration = float(self.cfg.get('input', {}).get('mouse_move_duration', 0.0))

    def click(self, x, y):
        if self.move_duration and self.move_duration > 0:
            pyautogui.moveTo(x, y, duration=self.move_duration)
            pyautogui.click()
        else:
            pyautogui.click(x, y)

    def press(self, key):
        pyautogui.press(key)
    
    def click_in_slot(self, slot_index):
        """Clica aproximadamente no centro de um dos 4 slots de ataque (0-3)."""
        slot_map = {
            0: 'slot_1',
            1: 'slot_2',
            2: 'slot_3',
            3: 'slot_4',
        }
        key = slot_map.get(slot_index)
        if not key:
            return
        moves_rois = self.rois.get('moves', {})
        coords = moves_rois.get(key)
        if not coords:
            return

        # coords pode ser [x1, y1, x2, y2] ou [x, y, w, h]
        if len(coords) != 4:
            return

        x1, y1, x2, y2 = coords
        # Converte se estiver no formato [x, y, w, h]
        if x2 <= x1 or y2 <= y1:
            x, y, w, h = coords
            x1, y1, x2, y2 = int(x), int(y), int(x + w), int(y + h)

        # Usa apenas uma área interna (por ex. 20% de margem em cada lado)
        margin_x = int(0.2 * (x2 - x1))
        margin_y = int(0.2 * (y2 - y1))
        safe_x1 = x1 + margin_x
        safe_x2 = x2 - margin_x
        safe_y1 = y1 + margin_y
        safe_y2 = y2 - margin_y

        if safe_x2 <= safe_x1 or safe_y2 <= safe_y1:
            # Fallback para centro se ROI for muito pequena
            cx = x1 + (x2 - x1) // 2
            cy = y1 + (y2 - y1) // 2
        else:
            cx = random.randint(safe_x1, safe_x2)
            cy = random.randint(safe_y1, safe_y2)

        self.click(cx, cy)

    def click_fight_button(self):
        """Clica no botão FIGHT usando o template fight.png."""
        assets_dir = self.cfg.get('assets', {}).get('templates_dir', '')
        fight_img_name = self.cfg.get('assets', {}).get('fight_image', 'fight.png')
        template_path = assets_dir + fight_img_name

        template = cv2.imread(template_path)
        if template is None:
            return

        # Captura uma screenshot da tela inteira
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        # Threshold conservador para evitar falsos positivos
        thresh = float(self.cfg.get('detection', {}).get('fight_threshold', 0.85))
        if max_val < thresh:
            return

        h, w = template.shape[:2]
        x, y = max_loc

        # Margem interna de 20% para clicar seguro dentro do botão
        margin_x = int(0.2 * w)
        margin_y = int(0.2 * h)
        safe_x1 = x + margin_x
        safe_x2 = x + w - margin_x
        safe_y1 = y + margin_y
        safe_y2 = y + h - margin_y

        if safe_x2 <= safe_x1 or safe_y2 <= safe_y1:
            cx = x + w // 2
            cy = y + h // 2
        else:
            cx = random.randint(safe_x1, safe_x2)
            cy = random.randint(safe_y1, safe_y2)

        self.click(cx, cy)

    def click_pokemon_button(self):
        """Clica no botão POKEMON usando o template pokemon.png."""
        assets_dir = self.cfg.get('assets', {}).get('templates_dir', '')
        poke_img_name = self.cfg.get('assets', {}).get('pokemon_image', 'pokemon.png')
        template_path = assets_dir + poke_img_name

        template = cv2.imread(template_path)
        if template is None:
            return

        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        thresh = float(self.cfg.get('detection', {}).get('pokemon_threshold', 0.85))
        if max_val < thresh:
            return

        h, w = template.shape[:2]
        x, y = max_loc

        margin_x = int(0.2 * w)
        margin_y = int(0.2 * h)
        safe_x1 = x + margin_x
        safe_x2 = x + w - margin_x
        safe_y1 = y + margin_y
        safe_y2 = y + h - margin_y

        if safe_x2 <= safe_x1 or safe_y2 <= safe_y1:
            cx = x + w // 2
            cy = y + h // 2
        else:
            cx = random.randint(safe_x1, safe_x2)
            cy = random.randint(safe_y1, safe_y2)

        self.click(cx, cy)

    def click_run_button(self):
        """Clica no botão RUN usando o template run.png."""
        assets_dir = self.cfg.get('assets', {}).get('templates_dir', '')
        run_img_name = self.cfg.get('assets', {}).get('run_image', 'run.png')
        template_path = assets_dir + run_img_name

        template = cv2.imread(template_path)
        if template is None:
            return

        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        thresh = float(self.cfg.get('detection', {}).get('run_threshold', 0.85))
        if max_val < thresh:
            return

        h, w = template.shape[:2]
        x, y = max_loc

        margin_x = int(0.2 * w)
        margin_y = int(0.2 * h)
        safe_x1 = x + margin_x
        safe_x2 = x + w - margin_x
        safe_y1 = y + margin_y
        safe_y2 = y + h - margin_y

        if safe_x2 <= safe_x1 or safe_y2 <= safe_y1:
            cx = x + w // 2
            cy = y + h // 2
        else:
            cx = random.randint(safe_x1, safe_x2)
            cy = random.randint(safe_y1, safe_y2)

        self.click(cx, cy)