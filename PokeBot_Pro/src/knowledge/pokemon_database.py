import json
import os
from pathlib import Path
from loguru import logger


class PokemonDatabase:
    """Banco de dados de Pokémon e golpes, usando dados locais do pokeapi.

    - `pokeapi_pokemon.json`: mapeia nome -> lista de type_ids.
    - `pokeapi_moves.json`: mapeia move -> type_id, power, accuracy, category_id.
    """

    def __init__(self, data_path: str = "data"):
        self.data_dir = Path(data_path)
        # Dados antigos (dex/tipos/movimentos) ainda podem existir; carregamos se precisar
        self.dex_legacy = self._load_json("dex.json")
        self.types_legacy = self._load_json("tipos.json")
        self.moves_legacy = self._load_json("movimentos.json")

        # Dados novos gerados a partir do pokeapi
        self.pokeapi_pokemon = self._load_json("pokeapi_pokemon.json")
        self.pokeapi_moves = self._load_json("pokeapi_moves.json")
        self.type_efficacy = self._load_json("type_efficacy.json")

    def _load_json(self, filename):
        path = self.data_dir / filename
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Falha ao carregar {filename}: {e}")
            return {}

    # ---------- Tipos / Fraquezas ----------

    def get_pokemon_types(self, pokemon_name: str):
        """Retorna lista de type_ids do Pokémon usando pokeapi (fallback para dados legados)."""
        if not pokemon_name:
            return []

        key = pokemon_name.strip().lower()
        data = self.pokeapi_pokemon.get(key)
        if data and "types" in data:
            return data["types"]

        # Fallback para dex antigo, se existir
        legacy = self.dex_legacy.get(pokemon_name)
        if legacy:
            return legacy.get("tipos", [])

        return []

    def get_weaknesses(self, pokemon_name: str):
        """Retorna lista de type_ids aos quais o Pokémon é fraco.

        Implementação baseada em `type_efficacy.json` (pokeapi), quando
        disponível. Se não houver dados, faz fallback para base antiga.
        """
        if not pokemon_name:
            return []

        enemy_types = self.get_pokemon_types(pokemon_name)
        if enemy_types and self.type_efficacy:
            weak_to = set()
            for target_type in enemy_types:
                rels = self.type_efficacy.get(str(target_type), {})
                for atk_type, mult in rels.items():
                    # Considera super efetivo se multiplicador >= 2.0
                    try:
                        if float(mult) >= 2.0:
                            weak_to.add(str(atk_type))
                    except (TypeError, ValueError):
                        continue
            return list(weak_to)

        # Fallback para dados legados, se existirem
        legacy = self.dex_legacy.get(pokemon_name)
        if legacy:
            weaknesses = set()
            for p_type in legacy.get("tipos", []):
                type_info = self.types_legacy.get(p_type, {})
                weaknesses.update(type_info.get("fraquezas", []))
            return list(weaknesses)

        return []

    def get_type_multiplier(self, move_type_id, enemy_types):
        """Retorna multiplicador total de tipo (float) para um golpe.

        Usa `type_efficacy.json` quando disponível. enemy_types é uma lista
        de type_ids (strings ou ints).
        """
        if not move_type_id or not enemy_types or not self.type_efficacy:
            return 1.0

        rels = self.type_efficacy.get(str(move_type_id), {})
        if not rels:
            return 1.0

        mult = 1.0
        for t in enemy_types:
            val = rels.get(str(t))
            try:
                if val is not None:
                    mult *= float(val)
            except (TypeError, ValueError):
                continue
        return mult

    # ---------- Golpes ----------

    def get_move_data(self, move_name: str):
        """Retorna dados do golpe, priorizando pokeapi_moves.json."""
        if not move_name:
            return None

        key = move_name.strip().lower()
        data = self.pokeapi_moves.get(key)
        if data:
            return data

        # Fallback para base antiga, que usa chaves em português
        return self.moves_legacy.get(move_name)