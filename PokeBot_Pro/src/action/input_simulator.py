import pyautogui
import time

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
        if len(coords) == 4:
            x1, y1, x2, y2 = coords
            if x2 > x1 and y2 > y1:
                cx = x1 + (x2 - x1) // 2
                cy = y1 + (y2 - y1) // 2
            else:
                # Trata como [x, y, w, h]
                x, y, w, h = coords
                cx = x + w // 2
                cy = y + h // 2
        else:
            return

        self.click(cx, cy)

    def click_fight_button(self):
        """Clica no botão FIGHT usando uma ROI fixa (btn_fight)."""
        btn_coords = self.rois.get('btn_fight')
        if not btn_coords or len(btn_coords) != 4:
            return

        x1, y1, x2, y2 = btn_coords
        # Aceita [x1,y1,x2,y2] ou [x,y,w,h]
        if x2 > x1 and y2 > y1:
            cx = x1 + (x2 - x1) // 2
            cy = y1 + (y2 - y1) // 2
        else:
            x, y, w, h = btn_coords
            cx = x + w // 2
            cy = y + h // 2

        self.click(cx, cy)