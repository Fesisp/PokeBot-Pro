import json
import os
from pathlib import Path

# Caminhos base
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEX2_PATH = DATA_DIR / "dex2.json"
OUTPUT_PATH = DATA_DIR / "dex2_completo.json"

# ATENÇÃO: este script **não** bate na API online.
# Ele só:
# 1) Lê o dex2.json (lista 001 Nome)
# 2) Usa esses nomes/numeração
# 3) Cria um JSON estruturado no formato do Bulbasaur
# Os campos "tipos" e "movimentos_por_nivel" são deixados vazios
# para você complementar depois com dados da PokeAPI como preferir.


def carregar_lista_dex2_crua():
    """Lê o dex2.json atual como texto e extrai pares (numero, nome).

    Formato atual do arquivo:
      - Um bloco JSON inicial com "Bulbasaur" (que ignoramos aqui)
      - Depois, linhas como:
            002	Ivysaur  (ou)
            002 Ivysaur

    Vamos ignorar tudo até encontrar a linha que começa com "002" e,
    a partir daí, aceitar tanto `NNN<TAB>Nome` quanto `NNN Nome`.
    """
    pares = []
    started = False

    with DEX2_PATH.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            strip = line.strip()
            if not strip:
                continue

            # Detecta início da lista numérica
            if not started:
                # Quando chegar na primeira linha que começa com 3 dígitos, começa
                parts = strip.split(maxsplit=1)
                if parts and parts[0].isdigit() and len(parts[0]) <= 3:
                    started = True
                else:
                    continue

            # A partir daqui, tentamos extrair numero + nome
            strip = strip.replace("\t", " ")
            parts = strip.split(maxsplit=1)
            if len(parts) != 2:
                continue
            num_str, nome = parts
            if not num_str.isdigit():
                continue
            numero = int(num_str)
            nome = nome.strip()
            pares.append((numero, nome))

    pares.sort(key=lambda x: x[0])
    return pares


def gerar_dex2_estruturado(pares):
    """Gera dicionário no formato do Bulbasaur, com campo numero.

    Estrutura final:
    {
      "Bulbasaur": {
        "numero": 1,
        "tipos": [],
        "movimentos_por_nivel": {}
      },
      ...
    }

    Os campos "tipos" e "movimentos_por_nivel" são deixados vazios
    propositalmente: você pode preenchê-los depois usando a PokeAPI.
    """
    resultado = {}
    for numero, nome in pares:
        resultado[nome] = {
            "numero": numero,
            "tipos": [],
            "movimentos_por_nivel": {}
        }
    return resultado


def main():
    if not DEX2_PATH.exists():
        raise FileNotFoundError(f"dex2.json não encontrado em {DEX2_PATH}")

    pares = carregar_lista_dex2_crua()
    if not pares:
        raise RuntimeError("Não foi possível extrair nenhum (numero, nome) do dex2.json")

    dex2_completo = gerar_dex2_estruturado(pares)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(dex2_completo, f, ensure_ascii=False, indent=2)

    print(f"Gerado {OUTPUT_PATH} com {len(dex2_completo)} entradas.")


if __name__ == "__main__":
    main()
