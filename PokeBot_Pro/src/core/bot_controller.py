import time
import cv2
import winsound
from loguru import logger
from ..perception.game_state_detector import GameState

class BotController:
    def __init__(self, config, components):
        self.cfg = config
        self.cap = components['screen']
        self.detector = components['detector']
        self.input = components['input']
        self.strategy = components['strategy']
        self.ocr = components['ocr']
        self.team_mgr = components['team_mgr']
        
        self.running = True

    def run(self):
        logger.info("Bot Iniciado! Pressione Ctrl+C para parar.")
        while self.running:
            img = self.cap.capture()
            state = self.detector.detect_state(img)

            if state == GameState.SHINY_FOUND:
                self.handle_shiny()
            elif state == GameState.IN_BATTLE:
                self.handle_battle(img)
            else:
                self.handle_exploring(img)
            
            time.sleep(0.5)

    def handle_shiny(self):
        logger.critical("SHINY ENCONTRADO! ALARME!")
        while True:
            winsound.Beep(1000, 500)
            time.sleep(0.5)
            # Trava o bot aqui para o humano assumir

    def handle_exploring(self, img):
        # Lógica de Missão: Só clica no Goto se NÃO estiver em batalha (já garantido pelo if/else do run)
        # Procura botão Goto
        goto_tpl = cv2.imread(self.cfg['assets']['templates_dir'] + self.cfg['assets']['goto_image'])
        res = cv2.matchTemplate(img, goto_tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val > 0.8:
            logger.info("Botão Goto encontrado. Seguindo missão...")
            # Clica no centro do botão encontrado
            h, w = goto_tpl.shape[:2]
            cx = max_loc[0] + w//2
            cy = max_loc[1] + h//2
            self.input.click(cx, cy)
            time.sleep(2) # Espera caminhar
        else:
            # Se não tem Goto, talvez tenha diálogo
            # Pressiona espaço periodicamente para passar diálogo
            self.input.press('space')

    def handle_battle(self, img):
        # 1. Ler Inimigo
        battle_info = self.detector.get_battle_info(img)
        enemy_name = battle_info['enemy_name']

        # 2. Ler Meus Golpes (Para aprender)
        # Recorta as 4 regiões dos botões de ataque definidas no settings.yaml
        my_moves = []
        for i in range(1, 5):
            roi = self.cfg['rois']['moves'][f'slot_{i}']
            # crop e OCR
            # ... (código de recorte e OCR aqui)
            # my_moves.append(move_text)
        
        # Salva o que aprendeu (Placeholder - precisa ler meu nome tbm)
        # self.team_mgr.save_moves("MeuPokemonAtual", my_moves)

        # 3. Decidir Ataque
        # best_slot = self.strategy.get_best_move("MeuPokemonAtual", enemy_name)
        
        # 4. Atacar
        logger.info(f"Atacando slot...")
        # self.input.click_in_slot(best_slot)
        
        time.sleep(4) # Espera animação