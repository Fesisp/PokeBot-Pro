import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEX2_PATH = DATA_DIR / "dex2_completo.json"
SAIDA_PATH = DATA_DIR / "dex2_preenchido.json"
LOG_ERROS_PATH = DATA_DIR / "dex2_pokeapi_erros.log"

POKEAPI_BASE = "https://pokeapi.co/api/v2/pokemon"


def get_pokemon_data_from_api(poke_id: int) -> dict | None:
    """Consulta a PokeAPI pública para um Pokémon pelo id."""
    url = f"{POKEAPI_BASE}/{poke_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"[WARN] ID {poke_id}: status {resp.status_code}")
            return None
        return resp.json()
    except Exception as e:
        print(f"[ERRO] ID {poke_id}: {e}")
        return None


def extract_types(api_data: dict) -> list[str]:
    """Extrai tipos em inglês a partir do JSON da API."""
    tipos = []
    for t in api_data.get("types", []):
        type_info = t.get("type") or {}
        name = type_info.get("name")
        if name:
            tipos.append(name.capitalize())
    return tipos


def extract_level_up_moves(api_data: dict) -> dict:
    """
    Extrai movimentos aprendidos por nível.

    Formato de saída:
      {
        "1": [["tackle", None], ["growl", None]],
        "7": [["ember", None]],
        ...
      }

    Usa 'level_learned_at' e filtra apenas métodos de aprendizado por level-up.
    """
    level_moves: dict[str, list[list]] = {}

    for move_entry in api_data.get("moves", []):
        move_name = move_entry.get("move", {}).get("name")
        if not move_name:
            continue

        for detail in move_entry.get("version_group_details", []):
            learn_method = detail.get("move_learn_method", {}).get("name")
            level = detail.get("level_learned_at", 0)

            # só movimentos aprendidos por level-up e com level > 0
            if learn_method != "level-up" or level <= 0:
                continue

            level_str = str(level)
            level_moves.setdefault(level_str, [])
            # usamos None como id do movimento, para manter o formato
            if [move_name, None] not in level_moves[level_str]:
                level_moves[level_str].append([move_name, None])

    return level_moves


def main() -> None:
    if not DEX2_PATH.exists():
        raise FileNotFoundError(f"dex2_completo.json não encontrado em {DEX2_PATH}")

    with DEX2_PATH.open("r", encoding="utf-8") as f:
        dex2 = json.load(f)

    erros: list[str] = []

    total = len(dex2)
    print(f"Encontrados {total} Pokémon em dex2_completo.json")

    for i, (nome, info) in enumerate(dex2.items(), start=1):
        poke_id = info.get("numero")
        if poke_id is None:
            erros.append(f"{nome}: sem campo 'numero'")
            continue

        print(f"[{i}/{total}] Buscando dados para {nome} (id={poke_id})...")
        api_data = get_pokemon_data_from_api(poke_id)
        if not api_data:
            erros.append(f"{nome} (id={poke_id}): falha ao consultar API")
            continue

        tipos = extract_types(api_data)
        moves = extract_level_up_moves(api_data)

        info["tipos"] = tipos
        info["movimentos_por_nivel"] = moves

        # pequena pausa para não bater demais na API
        time.sleep(0.5)

    with SAIDA_PATH.open("w", encoding="utf-8") as f:
        json.dump(dex2, f, ensure_ascii=False, indent=2)

    print(f"\nSalvo dex2 preenchido em: {SAIDA_PATH}")

    if erros:
        with LOG_ERROS_PATH.open("w", encoding="utf-8") as f:
            f.write("\n".join(erros))
        print(f"Foram encontrados {len(erros)} erros. Veja: {LOG_ERROS_PATH}")
    else:
        print("Nenhum erro registrado ao consultar a PokeAPI.")


if __name__ == "__main__":
    main()