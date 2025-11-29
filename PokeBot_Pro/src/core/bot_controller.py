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
        self.debug = bool(self.cfg.get('bot', {}).get('debug_mode', False))

    def run(self):
        logger.info("Bot Iniciado! Pressione Ctrl+C para parar.")
        while self.running:
            img = self.cap.capture()
            state = self.detector.detect_state(img)

            if self.debug:
                logger.debug(f"Estado detectado: {state.name}")

            if state == GameState.SHINY_FOUND:
                self.handle_shiny()
            elif state == GameState.IN_BATTLE:
                self.handle_battle(img)
            else:
                self.handle_exploring(img)
            
            time.sleep(0.5)

    def handle_shiny(self):
        logger.critical("SHINY ENCONTRADO! ALARME!")
        # Toca um alarme contínuo por alguns ciclos e para o bot completamente
        for _ in range(10):
            winsound.Beep(1000, 500)
            time.sleep(0.5)
        self.running = False

    def handle_exploring(self, img):
        # 1) Verifica se há diálogo (talk.png) antes de qualquer coisa
        talk_tpl = cv2.imread(self.cfg['assets']['templates_dir'] + self.cfg['assets']['talk_image'])
        if talk_tpl is not None:
            # If a specific search area is configured, crop the image to that ROI to avoid false positives
            talk_area = self.cfg.get('detection', {}).get('talk_search_area')
            search_img = img
            if talk_area and isinstance(talk_area, (list, tuple)) and len(talk_area) == 4:
                x1, y1, x2, y2 = talk_area
                # Accept formats [x,y,w,h] or [x1,y1,x2,y2]
                if x2 <= x1 or y2 <= y1:
                    # probably [x,y,w,h]
                    x, y, w, h = talk_area
                    x1, y1, x2, y2 = int(x), int(y), int(x + w), int(y + h)
                else:
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                # Clamp to image bounds
                h_img, w_img = img.shape[:2]
                x1 = max(0, min(x1, w_img - 1))
                x2 = max(0, min(x2, w_img))
                y1 = max(0, min(y1, h_img - 1))
                y2 = max(0, min(y2, h_img))
                if x2 > x1 and y2 > y1:
                    search_img = img[y1:y2, x1:x2]

                if self.debug:
                    logger.debug(f"Talk search area usada: [{x1}, {y1}, {x2}, {y2}]")

            res_talk = cv2.matchTemplate(search_img, talk_tpl, cv2.TM_CCOEFF_NORMED)
            _, max_val_talk, _, _ = cv2.minMaxLoc(res_talk)
            # Use configurable threshold (default 0.95) to avoid confusão com chat
            talk_thresh = self.cfg.get('detection', {}).get('talk_threshold', 0.95)
            if self.debug:
                logger.debug(f"Score talk.png: {max_val_talk:.3f} (threshold={talk_thresh})")
            if max_val_talk > talk_thresh:
                logger.info(f"Ícone de diálogo encontrado (score={max_val_talk:.3f}). Avançando conversa com Espaço...")
                self.input.press('space')
                return

        # 2) Se não tem diálogo, tenta seguir missão via Goto
        goto_tpl = cv2.imread(self.cfg['assets']['templates_dir'] + self.cfg['assets']['goto_image'])
        res = cv2.matchTemplate(img, goto_tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        goto_thresh = self.cfg.get('detection', {}).get('goto_threshold', 0.8)

        if self.debug:
            logger.debug(f"Score goto.png: {max_val:.3f} (threshold={goto_thresh})")

        # Antes de clicar em Goto, revalida se não estamos em batalha neste frame
        current_state = self.detector.detect_state(img)
        if current_state == GameState.IN_BATTLE:
            if self.debug:
                logger.debug("Botões de batalha detectados ao tentar clicar em Goto. Cancelando clique.")
            return

        if max_val > goto_thresh:
            logger.info("Botão Goto encontrado. Seguindo missão...")
            # Clica em uma região interna "segura" do botão encontrado (não precisa ser o centro exato)
            h, w = goto_tpl.shape[:2]
            x, y = max_loc

            margin_x = int(0.1 * w)
            margin_y = int(0.1 * h)

            safe_x1 = x + margin_x
            safe_x2 = x + w - margin_x
            safe_y1 = y + margin_y
            safe_y2 = y + h - margin_y

            cx = (safe_x1 + safe_x2) // 2
            cy = (safe_y1 + safe_y2) // 2

            if self.debug:
                logger.debug(f"Clicando em Goto nas coordenadas seguras: ({cx}, {cy}) dentro de [{safe_x1},{safe_y1},{safe_x2},{safe_y2}]")

            self.input.click(cx, cy)
            time.sleep(2) # Espera caminhar
            return

        # 3) Fallback: nenhum talk nem Goto, mantém leve interação
        if self.debug:
            logger.debug("Nenhum talk/goto confiável encontrado. Fallback: pressionando espaço.")
        self.input.press('space')

    def handle_battle(self, img):
        # Proteção: se por algum motivo a HUD de batalha sumiu, não atacar
        if self.detector.detect_state(img) != GameState.IN_BATTLE:
            if self.debug:
                logger.debug("handle_battle chamado mas estado não é IN_BATTLE. Abortando ações de ataque.")
            return

        # 1. Ler Inimigo
        battle_info = self.detector.get_battle_info(img)
        enemy_name = battle_info.get('enemy_name', '').strip()

        if self.debug:
            logger.debug(f"Inimigo detectado: '{enemy_name}'")

        # 2. Garantir que o menu de golpes está aberto: clicar FIGHT primeiro
        try:
            self.input.click_fight_button()
            if self.debug:
                logger.debug("Clique em FIGHT enviado antes de ler os golpes.")
            time.sleep(0.6)  # pequena espera para o menu de golpes aparecer
        except Exception as e:
            logger.error(f"Erro ao clicar em FIGHT: {e}")

        # 3. Ler Meus Golpes (Para aprender) - texto branco nos botões
        my_moves = []
        for i in range(1, 5):
            roi_coords = self.cfg['rois']['moves'][f'slot_{i}']
            x1, y1, x2, y2 = roi_coords
            move_img = img[y1:y2, x1:x2]
            # Apenas letras e espaços nos nomes de golpes
            move_text_raw = self.ocr.extract_text_optimized(
                move_img,
                whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz -",
                invert_for_white_text=True
            )
            move_text = move_text_raw.replace('\n', ' ').strip()
            my_moves.append(move_text)

            if self.debug:
                logger.debug(f"Slot {i}: OCR='{move_text}' ROI={roi_coords}")

        # 4. Salvar o que aprendeu (Placeholder do nome do Pokémon atual)
        my_pokemon_name = "MeuPokemonAtual"
        try:
            self.team_mgr.save_moves(my_pokemon_name, my_moves)
        except Exception as e:
            logger.error(f"Erro ao salvar movimentos: {e}")

        # 5. Decidir Ataque usando estratégia
        try:
            best_slot = self.strategy.get_best_move(my_pokemon_name, enemy_name)
        except Exception as e:
            logger.error(f"Erro na estratégia de batalha: {e}")
            best_slot = 0

        if self.debug:
            logger.debug(f"Estratégia escolheu slot {best_slot} para {my_pokemon_name} vs {enemy_name}")

        # 6. Atacar clicando no slot escolhido
        logger.info(f"Atacando slot {best_slot} contra {enemy_name} | Moves: {my_moves}")
        try:
            self.input.click_in_slot(best_slot)
        except Exception as e:
            logger.error(f"Erro ao clicar no slot de ataque: {e}")

        # Espera animação de ataque/botões reaparecerem
        time.sleep(self.cfg.get('battle', {}).get('action_cooldown', 2.5))