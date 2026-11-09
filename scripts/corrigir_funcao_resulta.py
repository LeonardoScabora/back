#!/usr/bin/env python3
"""Corrige enunciados quebrados do tipo 'Qual a função de X resulta?'."""

from __future__ import annotations

import json
import re
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "src" / "main" / "resources" / "seed"


def q(texto: str) -> str:
    texto = " ".join(texto.split()).strip().rstrip(" .;:?")
    if not texto:
        return "?"
    return texto[0].upper() + texto[1:] + "?"


def corrigir(e: str) -> str:
    e = " ".join(e.split()).strip()

    # Casos específicos primeiro
    if re.search(r"(?i)fun[cç][aã]o de\s+Divis[aã]o inteira\s+(\d+)\s*/\s*(\d+)", e):
        m = re.search(r"(?i)(\d+)\s*/\s*(\d+)", e)
        return q(f"Qual o resultado de {m.group(1)}/{m.group(2)} na divisão inteira")

    if re.search(r"(?i)fun[cç][aã]o de\s+Arrays possuem", e):
        return q("A partir de qual número começam os índices de um array")

    if re.search(r"(?i)fun[cç][aã]o de\s+StringBuilder", e):
        return q("Para que o StringBuilder é usado principalmente")

    if re.search(r"(?i)fun[cç][aã]o de\s+Await", e):
        return q("Em qual contexto a palavra await só pode ser usada")

    # Qual a função de <expressão> resulta?
    m = re.match(r"(?i)^Qual a fun[cç][aã]o de\s+(.+?)\s+resulta\??$", e)
    if m:
        expr = m.group(1).strip()
        return q(f"Qual o resultado da expressão {expr}")

    # Genérico restante: Qual a função de X?
    m = re.match(r"(?i)^Qual a fun[cç][aã]o de\s+(.+?)\??$", e)
    if m:
        resto = m.group(1).strip()
        if re.search(r"[+\-*/%]|==|!=|&&|\|\||'|\"", resto):
            return q(f"Qual o resultado da expressão {resto}")
        if re.search(r"(?i)\bresulta\b", resto):
            resto = re.sub(r"(?i)\s*resulta$", "", resto).strip()
            return q(f"Qual o resultado de {resto}")
        return q(f"Para que serve {resto}")

    return e


def main() -> None:
    mudou = 0
    for path in sorted(SEED.glob("perguntas-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            antigo = item["enunciado"]
            novo = corrigir(antigo)
            if novo != antigo:
                mudou += 1
                item["enunciado"] = novo
                print(f"{path.name}:\n  - {antigo}\n  + {novo}")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    leftovers = []
    for path in sorted(SEED.glob("perguntas-*.json")):
        for item in json.loads(path.read_text(encoding="utf-8")):
            e = item["enunciado"]
            if re.search(r"(?i)qual a fun[cç][aã]o de", e):
                leftovers.append(e)
    print(f"Alteradas: {mudou} | leftovers: {len(leftovers)}")
    for x in leftovers:
        print(" leftover:", x)


if __name__ == "__main__":
    main()
