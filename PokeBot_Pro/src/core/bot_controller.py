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
        # Novo: processador de imagem para texto branco em fundo colorido
        self.img_proc = components.get('processor')
        
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

        # Sempre garantir que o menu de batalha está focado em FIGHT primeiro
        try:
            self.input.click_fight_button()
            if self.debug:
                logger.debug("Clique inicial em FIGHT enviado ao entrar em handle_battle.")
            time.sleep(self.cfg.get('battle', {}).get('fight_to_moves_delay', 1.2))
        except Exception as e:
            logger.error(f"Erro ao clicar no FIGHT inicial: {e}")

        # 1. Ler Inimigo
        battle_info = self.detector.get_battle_info(img)
        enemy_name = battle_info.get('enemy_name', '').strip()
        my_pokemon_name = battle_info.get('player_name', '').strip() or "MeuPokemonAtual"

        if self.debug:
            logger.debug(f"Inimigo detectado: '{enemy_name}' | Meu Pokémon: '{my_pokemon_name}'")

        # 2. Decidir se deve fugir ANTES de abrir menu de golpes
        try:
            if self.strategy.should_flee(my_pokemon_name, enemy_name):
                logger.info(f"Decisão de FUGIR da batalha contra {enemy_name}.")
                # Usa o botão RUN via template (run.png)
                try:
                    self.input.click_run_button()
                    time.sleep(self.cfg.get('battle', {}).get('action_cooldown', 2.5))
                    return
                except Exception as e_click:
                    logger.error(f"Erro ao clicar em RUN via template: {e_click}")
        except Exception as e:
            logger.error(f"Erro ao decidir fuga: {e}")

        # 3. (opcional) Tentar trocar de Pokémon se houver alguém claramente vantajoso
        try:
            switch_idx = self.strategy.choose_switch_target(enemy_name)
        except Exception as e:
            logger.error(f"Erro ao decidir troca de Pokémon: {e}")
            switch_idx = None

        if switch_idx is not None:
            logger.info(f"Decisão de TROCAR para o slot {switch_idx} da equipe contra {enemy_name}.")
            try:
                # Abre menu de POKEMON pelo botão com ROI/template existente
                self.input.click_pokemon_button()
                time.sleep(0.6)

                # Usa menu de troca configurado em rois.switch_menu e OCR especializado
                switch_cfg = self.cfg.get('rois', {}).get('switch_menu', {})
                container = switch_cfg.get('container')
                slot_h = int(switch_cfg.get('slot_height', 30))

                if container and len(container) == 4:
                    x1, y1, x2, y2 = container
                    if x2 <= x1 or y2 <= y1:
                        x, y, w, h = container
                        x1, y1, x2, y2 = int(x), int(y), int(x + w), int(y + h)
                    h_img, w_img = img.shape[:2]
                    x1 = max(0, min(int(x1), w_img - 1))
                    x2 = max(0, min(int(x2), w_img))
                    y1 = max(0, min(int(y1), h_img - 1))
                    y2 = max(0, min(int(y2), h_img))

                    # OCR da lista inteira com método especializado
                    menu_img = img[y1:y2, x1:x2]
                    detected_names = self.ocr.ocr_party_list(menu_img)

                    # Atualiza equipe atual com o que foi lido
                    self.team_mgr.update_team_from_hud(detected_names)

                    # Clica aproximadamente na linha correspondente ao índice sugerido
                    idx = max(0, min(int(switch_idx), max(len(detected_names) - 1, 0)))
                    cy = y1 + idx * slot_h + slot_h // 2
                    cx = x1 + (x2 - x1) // 2
                    if self.debug:
                        logger.debug(f"Clicando no slot de equipe {idx} em ({cx}, {cy}) para trocar Pokémon. Nomes detectados: {detected_names}")
                    self.input.click(cx, cy)

                    # Pequena espera para animação de troca
                    time.sleep(self.cfg.get('battle', {}).get('action_cooldown', 2.5))

                    # Depois da troca, não ataca neste tick; deixa próxima iteração decidir
                    return
                else:
                    logger.warning("ROI de menu de troca (switch_menu.container) não configurada; não foi possível trocar.")
            except Exception as e:
                logger.error(f"Erro ao executar troca de Pokémon: {e}")

        # 4. Neste ponto o menu de golpes já deve estar aberto pelo clique inicial em FIGHT

        # 5. Ler Meus Golpes (Para aprender) - texto branco nos botões
        my_moves = []
        for i in range(1, 5):
            roi_coords = self.cfg['rois']['moves'][f'slot_{i}']
            x1, y1, x2, y2 = roi_coords
            move_img = img[y1:y2, x1:x2]

            # Pré-processa texto branco em fundo dinâmico (botão de golpe)
            if self.img_proc is not None:
                processed = self.img_proc.process_dynamic_background_text(move_img)
            else:
                processed = self.ocr.preprocess_dynamic_background_text(move_img)

            # Apenas letras e espaços nos nomes de golpes
            move_text_raw = self.ocr.extract_text_optimized(
                processed,
                whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
                invert_for_white_text=False
            )
            move_text = move_text_raw.replace('\n', ' ').strip()
            move_name = self.ocr.clean_move_name(move_text)
            my_moves.append(move_name)

            if self.debug:
                logger.debug(f"Slot {i}: OCR_bruto='{move_text}' | nome_limpo='{move_name}' ROI={roi_coords}")

        # 6. Salvar o que aprendeu (nome real do Pokémon atual)
        try:
            self.team_mgr.save_moves(my_pokemon_name, my_moves)
            if self.debug:
                logger.debug(f"Golpes salvos para '{my_pokemon_name}': {my_moves}")
        except Exception as e:
            logger.error(f"Erro ao salvar movimentos: {e}")

        # 7. Decidir Ataque usando estratégia
        try:
            best_slot = self.strategy.get_best_move(my_pokemon_name, enemy_name)
        except Exception as e:
            logger.error(f"Erro na estratégia de batalha: {e}")
            best_slot = 0

        if self.debug:
            logger.debug(f"Estratégia escolheu slot {best_slot} para {my_pokemon_name} vs {enemy_name}")

        # 8. Atacar clicando no slot escolhido
        logger.info(f"Atacando slot {best_slot} contra {enemy_name} | Moves: {my_moves}")
        try:
            self.input.click_in_slot(best_slot)
        except Exception as e:
            logger.error(f"Erro ao clicar no slot de ataque: {e}")

        # Espera animação de ataque/botões reaparecerem (mais paciente)
        time.sleep(self.cfg.get('battle', {}).get('action_cooldown', 4.0))