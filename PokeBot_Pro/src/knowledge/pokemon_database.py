import json
import os
from loguru import logger

class PokemonDatabase:
    def __init__(self):
        self.data_path = "data/"
        self.dex = self._load_json("dex.json")
        self.types = self._load_json("tipos.json")
        self.moves = self._load_json("movimentos.json")

    def _load_json(self, filename):
        try:
            with open(os.path.join(self.data_path, filename), 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            logger.error(f"Falha ao carregar {filename}")
            return {}

    def get_weaknesses(self, pokemon_name):
        """Retorna lista de tipos que o pokemon tem fraqueza"""
        # Lógica de Fuzzy Match do Projeto B seria ideal aqui
        poke_data = self.dex.get(pokemon_name)
        if not poke_data: return []
        
        weaknesses = set()
        for p_type in poke_data.get('tipos', []):
            type_info = self.types.get(p_type, {})
            weaknesses.update(type_info.get('fraquezas', []))
        return list(weaknesses)

    def get_move_data(self, move_name):
        return self.moves.get(move_name)