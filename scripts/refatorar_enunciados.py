#!/usr/bin/env python3
"""Torna enunciados intuitivos e remove prefixo de linguagem."""

from __future__ import annotations

import json
import re
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "src" / "main" / "resources" / "seed"

PREFIX_RE = re.compile(
    r"^(Em|No|Na linguagem|Sobre|Considerando)\s+(Java|Python|C\+\+)\s*[,:]?\s*",
    re.IGNORECASE,
)

# "o que <verbo> ..." → "Como <verbo_infinitivo/forma natural> ..."
O_QUE_VERBO = re.compile(
    r"^o que\s+(declara|cria|permite|impede|agrupa|referencia|lança|trata|inicia|"
    r"verifica|concede|compara|atribui|indica|importa|herda|implementa|armazena|"
    r"representa|executa|compila|aloca|libera|inclui|introduz|marca|define|"
    r"produz|aguarda|associa|gera|imprime|converte|ordena|remove|insere|obtém|"
    r"obtem|filtra|aplica|mantém|transforma|combina|captura|propaga)\s+(.+)$",
    re.IGNORECASE,
)

COMO_MAP = {
    "declara": "Como se declara",
    "cria": "Como se cria",
    "permite": "O que permite",
    "impede": "O que impede",
    "agrupa": "O que agrupa",
    "referencia": "O que referencia",
    "lança": "O que lança",
    "trata": "O que trata",
    "inicia": "O que inicia",
    "verifica": "O que verifica",
    "concede": "O que concede",
    "compara": "O que compara",
    "atribui": "O que atribui",
    "indica": "O que indica",
    "importa": "Como se importa",
    "herda": "Como se herda",
    "implementa": "Como se implementa",
    "armazena": "O que armazena",
    "representa": "O que representa",
    "executa": "O que executa",
    "compila": "O que compila",
    "aloca": "O que aloca",
    "libera": "O que libera",
    "inclui": "Como se inclui",
    "introduz": "O que introduz",
    "marca": "O que marca",
    "define": "O que define",
    "produz": "O que produz",
    "aguarda": "O que aguarda",
    "associa": "O que associa",
    "gera": "O que gera",
    "imprime": "O que imprime",
    "converte": "O que converte",
    "ordena": "O que ordena",
    "remove": "O que remove",
    "insere": "O que insere",
    "obtém": "O que obtém",
    "obtem": "O que obtém",
    "filtra": "O que filtra",
    "aplica": "O que aplica",
    "mantém": "O que mantém",
    "transforma": "O que transforma",
    "combina": "O que combina",
    "captura": "O que captura",
    "propaga": "O que propaga",
}


def capitalizar(texto: str) -> str:
    texto = texto.strip()
    if not texto:
        return texto
    return texto[0].upper() + texto[1:]


def garantir_interrogacao(texto: str) -> str:
    texto = texto.rstrip(" .;:")
    if not texto.endswith("?"):
        texto += "?"
    return texto


def refatorar(enunciado: str) -> str:
    e = " ".join(enunciado.split()).strip()
    e = PREFIX_RE.sub("", e).strip()
    e = capitalizar(e)

    # para que serve 'X'? → Para que serve 'X'?
    m = re.match(r"^para que serve\s+(.+)$", e, flags=re.IGNORECASE)
    if m:
        return garantir_interrogacao(f"Para que serve {m.group(1).rstrip('?')}")

    # o que melhor descreve / o que é responsável por
    e = re.sub(r"^o que é responsável por\s+", "Como se faz para ", e, flags=re.IGNORECASE)
    e = re.sub(r"^o que melhor descreve\s+", "O que significa ", e, flags=re.IGNORECASE)

    # o que representa X?
    m = re.match(r"^o que representa\s+(.+)$", e, flags=re.IGNORECASE)
    if m:
        resto = m.group(1).rstrip("?")
        return garantir_interrogacao(f"O que representa {resto}")

    # o que <verbo> ...
    m = O_QUE_VERBO.match(e.rstrip("?"))
    if m:
        verbo = m.group(1).lower()
        resto = m.group(2).rstrip("?")
        prefixo = COMO_MAP.get(verbo, f"O que {verbo}")
        # Casos especiais mais naturais
        if verbo == "declara":
            return garantir_interrogacao(f"Como se declara {resto}")
        if verbo == "cria":
            return garantir_interrogacao(f"Como se cria {resto}")
        if verbo == "importa":
            return garantir_interrogacao(f"Como se importa {resto}")
        if verbo == "permite":
            return garantir_interrogacao(f"O que permite {resto}")
        return garantir_interrogacao(f"{prefixo} {resto}")

    # qual tipo ... → Qual tipo ...
    m = re.match(r"^qual tipo\s+(.+)$", e, flags=re.IGNORECASE)
    if m:
        resto = m.group(1).rstrip("?")
        # "primitivo para números" → "primitivo armazena números"
        resto2 = re.sub(r"^primitivo para\s+", "primitivo armazena ", resto, flags=re.IGNORECASE)
        resto2 = re.sub(r"^inteiro de\s+", "inteiro de ", resto2, flags=re.IGNORECASE)
        if resto2.lower().startswith("primitivo verdadeiro"):
            return "Qual tipo primitivo representa verdadeiro ou falso?"
        if "números inteiros" in resto2.lower() or "numeros inteiros" in resto2.lower():
            return "Qual tipo primitivo armazena números inteiros?"
        return garantir_interrogacao(f"Qual tipo {resto2}")

    # qual palavra-chave ...
    m = re.match(r"^qual palavra-chave\s+(.+)$", e, flags=re.IGNORECASE)
    if m:
        resto = m.group(1).rstrip("?")
        if resto.lower().startswith("importa "):
            return garantir_interrogacao(f"Qual palavra-chave {resto}")
        return garantir_interrogacao(f"Qual palavra-chave {resto}")

    # qual modificador ...
    m = re.match(r"^qual modificador\s+(.+)$", e, flags=re.IGNORECASE)
    if m:
        return garantir_interrogacao(f"Qual modificador {m.group(1).rstrip('?')}")

    # qual estrutura/coleção / qual operador / qual ...
    m = re.match(r"^qual\s+(.+)$", e, flags=re.IGNORECASE)
    if m:
        return garantir_interrogacao(f"Qual {m.group(1).rstrip('?')}")

    # o operador 'X' serve para: Y → Para que serve o operador 'X'?
    m = re.match(r"^o operador\s+'([^']+)'\s+serve para:\s*(.+)$", e, flags=re.IGNORECASE)
    if m:
        return garantir_interrogacao(f"Para que serve o operador '{m.group(1)}'")

    # método/API
    m = re.match(r"^o que o método/API\s+'([^']+)'\s+de\s+(.+)\s+faz\??$", e, flags=re.IGNORECASE)
    if m:
        return garantir_interrogacao(f"Para que serve '{m.group(1)}' em {m.group(2)}")

    # Limpa restos de "Com base na linguagem:" etc.
    e = re.sub(r"^Com base na linguagem:\s*", "", e, flags=re.IGNORECASE)
    e = re.sub(r"^Assinale a correta:\s*", "", e, flags=re.IGNORECASE)
    e = re.sub(r"^Escolha a opção correta\.\s*", "", e, flags=re.IGNORECASE)
    e = capitalizar(e)
    return garantir_interrogacao(e)


def main() -> None:
    total = 0
    mudou = 0
    ainda_prefixo = 0
    exemplos = []

    for path in sorted(SEED.glob("perguntas-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            total += 1
            antigo = item["enunciado"]
            novo = refatorar(antigo)
            if novo != antigo:
                mudou += 1
                item["enunciado"] = novo
            if re.match(r"^(Em|No)\s+(Java|Python|C\+\+)", novo, re.I):
                ainda_prefixo += 1
            if "declara uma classe" in novo.lower() or "declara uma função" in novo.lower():
                exemplos.append(novo)

        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{path.name}: ok ({len(data)} perguntas)")
        for p in data[:3]:
            print("  ", p["enunciado"])

    print(f"Alteradas: {mudou}/{total} | ainda com prefixo: {ainda_prefixo}")
    for ex in exemplos[:8]:
        print(" ex classe/função:", ex)


if __name__ == "__main__":
    main()
