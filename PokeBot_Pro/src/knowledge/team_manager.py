import json
import os

class TeamManager:
    def __init__(self):
        self.db_file = "data/known_moves.json"
        self.known_moves = self._load()

    def _load(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r', encoding='utf-8') as f: return json.load(f)
        return {}

    def save_moves(self, pokemon_name, moves):
        if not pokemon_name: return
        self.known_moves[pokemon_name] = moves
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.known_moves, f, indent=2)

    def get_moves(self, pokemon_name):
        return self.known_moves.get(pokemon_name, [])