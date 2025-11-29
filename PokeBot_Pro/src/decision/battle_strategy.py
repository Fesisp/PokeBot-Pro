from loguru import logger

class BattleStrategy:
    def __init__(self, db, team_manager):
        self.db = db
        self.tm = team_manager

    def get_best_move(self, my_pokemon_name, enemy_name):
        # 1. Descobrir fraquezas do inimigo
        weaknesses = self.db.get_weaknesses(enemy_name)
        logger.info(f"Inimigo: {enemy_name} | Fraquezas: {weaknesses}")

        # 2. Pegar meus movimentos (da memória)
        my_moves = self.tm.get_moves(my_pokemon_name)
        if not my_moves:
            logger.warning("Movimentos desconhecidos. Usando Slot 1.")
            return 0 # Slot 1

        # 3. Escolher o melhor
        best_slot = 0
        best_power = -1

        for i, move_name in enumerate(my_moves):
            move_data = self.db.get_move_data(move_name)
            if not move_data: continue

            power = move_data.get('poder', 0)
            move_type = move_data.get('tipo')

            # Bônus massivo se for super efetivo
            if move_type in weaknesses:
                power *= 2
            
            if power > best_power:
                best_power = power
                best_slot = i
        
        return best_slot # 0, 1, 2 ou 3