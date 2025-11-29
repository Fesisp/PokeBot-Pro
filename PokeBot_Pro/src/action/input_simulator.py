import pyautogui
import time

class InputSimulator:
    def __init__(self):
        # Desabilita o fail-safe para evitar paradas bruscas se o mouse for para o canto
        # CUIDADO: Isso impede que você pare o bot movendo o mouse para o canto!
        pyautogui.FAILSAFE = False

    def click(self, x, y):
        pyautogui.click(x, y)

    def press(self, key):
        pyautogui.press(key)
    
    def click_in_slot(self, slot_index):
        # Placeholder for slot clicking logic
        pass