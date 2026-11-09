#!/usr/bin/env python3
"""Segunda passada: corrige 'Como se faz para...' e deixa enunciados naturais."""

from __future__ import annotations

import json
import re
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "src" / "main" / "resources" / "seed"


def capitalizar(texto: str) -> str:
    texto = texto.strip()
    if not texto:
        return texto
    return texto[0].upper() + texto[1:]


def q(texto: str) -> str:
    texto = capitalizar(texto.rstrip(" .;:?"))
    return texto + "?"


def corrigir(enunciado: str) -> str:
    e = " ".join(enunciado.split()).strip()

    # Remove qualquer prefixo de linguagem restante
    e = re.sub(
        r"^(Em|No|Na linguagem|Sobre|Considerando)\s+(Java|Python|C\+\+)\s*[,:]?\s*",
        "",
        e,
        flags=re.I,
    ).strip()

    # "Como se faz para qual X?" → "Qual X?"
    m = re.match(r"^Como se faz para\s+qual\s+(.+)$", e, flags=re.I)
    if m:
        return q(f"Qual {m.group(1)}")

    # "Como se faz para <sujeito> <verbo>?" → "O que <sujeito> <verbo>?"
    m = re.match(
        r"^Como se faz para\s+(.+?)\s+(faz|serve para|representa|significa|indica|cria|"
        r"usa|usa sintaxe|combina|conta|tipa|simplifica|impacta|libera|organiza|"
        r"permite|reduz|possui|melhora|restringem|gera automaticamente|é usado para|"
        r"relaciona-se a|ocorre tipicamente em|é voltada a|é preferido para|"
        r"não pode tipar|não recebe|recebe tipicamente|atua na|pode|junta|compõem|"
        r"só pode ser usado em|difere de .+ porque|ajuda a|avaliam?|obtém|concede|"
        r"ajudam em|exige|melhora|importa para|é)\s*(.*)$",
        e,
        flags=re.I,
    )
    if m:
        sujeito = m.group(1).strip()
        verbo = m.group(2).strip()
        resto = (m.group(3) or "").strip().rstrip("?")
        # Normaliza capitalização do sujeito técnico
        if sujeito and sujeito[0].islower() and not sujeito.startswith(("std::", "@", "__")):
            # mantém como veio se for palavra comum
            pass
        frase = f"O que {sujeito} {verbo}"
        if resto:
            frase = f"{frase} {resto}"
        return q(frase)

    # "Como se faz para X?" genérico (substantivo/definição)
    m = re.match(r"^Como se faz para\s+(.+)$", e, flags=re.I)
    if m:
        resto = m.group(1).rstrip("?").strip()
        # Se parece pergunta já completa com verbo no final
        if re.search(r"\b(vale|resulta em|contém|traz|começam em|faz)\s*$", resto, re.I):
            return q(resto if resto[0].isupper() else capitalizar(resto))
        # Definições / conceitos
        if resto.lower().startswith(("operador ", "função ", "bloco ", "laço ", "estrutura ",
                                     "condição ", "ausência ", "negação ", "enumeração ",
                                     "alias ", "macro ", "ponteiro ", "duração ", "tamanho ",
                                     "agregado ", "caractere", "saída ", "entrada ",
                                     "sugestão ", "no-op", "interrompe ", "vai ", "devolve ",
                                     "gerencia ", "classe/", "campo ", "método ", "ramo ",
                                     "valor ", "tipo ", "acesso ")):
            return q(f"O que é {resto}")
        # Termos técnicos curtos / nomes
        if len(resto.split()) <= 8:
            return q(f"O que é {resto}")
        return q(f"O que significa {resto}")

    # "O que declara/cria..." que ainda restou
    m = re.match(r"^O que\s+(declara|cria|importa)\s+(.+)$", e, flags=re.I)
    if m:
        return q(f"Como se {m.group(1).lower()} {m.group(2)}")

    # match/case %? residual
    e = e.replace("match/case %?", "O que o match/case realiza?")
    e = e.replace("Match/case %?", "O que o match/case realiza?")

    # Capitalização final
    e = capitalizar(e)
    if not e.endswith("?"):
        e += "?"
    return e


def main() -> None:
    total_bad_before = 0
    total_bad_after = 0
    for path in sorted(SEED.glob("perguntas-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        before = sum(1 for p in data if p["enunciado"].lower().startswith("como se faz para"))
        total_bad_before += before
        for item in data:
            item["enunciado"] = corrigir(item["enunciado"])
        after = sum(1 for p in data if p["enunciado"].lower().startswith("como se faz para"))
        total_bad_after += after
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{path.name}: como_se_faz {before}->{after}")
        for p in data:
            if "declara uma classe" in p["enunciado"].lower():
                print("  ", p["enunciado"])
        for p in data[:3]:
            print("  sample:", p["enunciado"])
    print(f"TOTAL como_se_faz {total_bad_before}->{total_bad_after}")


if __name__ == "__main__":
    main()
