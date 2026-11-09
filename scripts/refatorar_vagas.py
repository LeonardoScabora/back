#!/usr/bin/env python3
"""Reescreve perguntas vagas/fragmentadas em enunciados completos e intuitivos."""

from __future__ import annotations

import json
import re
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "src" / "main" / "resources" / "seed"


def cap(texto: str) -> str:
    texto = " ".join(texto.split()).strip()
    if not texto:
        return texto
    return texto[0].upper() + texto[1:]


def q(texto: str) -> str:
    texto = cap(texto).rstrip(" .;:?")
    return texto + "?"


def correta_texto(item: dict) -> str:
    letra = item.get("respostaCorreta", "A").strip().upper()
    return {
        "A": item["alternativaA"],
        "B": item["alternativaB"],
        "C": item["alternativaC"],
        "D": item["alternativaD"],
    }.get(letra, item["alternativaA"])


def refatorar(e: str, item: dict) -> str:
    e = " ".join(e.split()).strip()
    e = re.sub(
        r"^(Em|No|Na linguagem|Sobre|Considerando)\s+(Java|Python|C\+\+)\s*[,:]?\s*",
        "",
        e,
        flags=re.I,
    ).strip()
    original = e
    baixa = e.lower().rstrip("?")

    # --- padrões do usuário / incompletos ---
    if re.search(r"\bocorre ao$", baixa):
        sujeito = re.sub(r"\s*ocorre ao\??$", "", e, flags=re.I).strip()
        return q(f"Em qual situação ocorre {sujeito}")

    if re.search(r"\b(serve|usado|comum) para$", baixa):
        sujeito = re.sub(r"\s*(serve|é comum|é usado|comum|usado)\s+para\??$", "", e, flags=re.I).strip()
        if "comum" in baixa:
            return q(f"Para que é comum usar {sujeito}")
        return q(f"Para que serve {sujeito}")

    # O comando X?
    m = re.match(r"^O comando\s+(.+?)\??$", e, flags=re.I)
    if m:
        return q(f"Para que serve o comando {m.group(1).rstrip('?')}")

    # Um/Uma X?
    m = re.match(r"^(Um|Uma)\s+(.+?)\??$", e, flags=re.I)
    if m:
        artigo = m.group(1).lower()
        nome = m.group(2).rstrip("?")
        return q(f"O que é {artigo} {nome}")

    # Break/Continue em um laço?
    m = re.match(r"^(Break|Continue)\s+em um la[cç]o\??$", e, flags=re.I)
    if m:
        return q(f"O que o {m.group(1).lower()} faz em um laço")

    # Termo técnico sozinho: Vector::push_back? / Std::endl?
    m = re.match(r"^([A-Za-z_:<>(\)./=+\-]+)\??$", e)
    if m and len(e) < 40:
        return q(f"Para que serve {m.group(1).rstrip('?')}")

    # X faz? / X é? / X tem? / X traz? / X retorna? / X armazena? etc.
    m = re.match(
        r"^(.+?)\s+(faz|é|tem|traz|retorna|armazena|guarda|permite|exige|evitam|evita|"
        r"resolve|melhora|significa|indica|libera|trata|chama|imprime|infere|"
        r"diferem|difere|ajuda|ajudam|avalia|obtém|concede|exige|organiza|libera)\??$",
        e,
        flags=re.I,
    )
    if m and not re.match(r"^(Qual|Como|Para|O que)\b", e, re.I):
        sujeito = m.group(1).strip()
        verbo = m.group(2).lower()
        if verbo == "faz":
            return q(f"O que {sujeito} faz")
        if verbo in {"é", "significa"}:
            return q(f"O que significa {sujeito}")
        if verbo == "tem":
            return q(f"O que {sujeito} possui")
        if verbo == "traz":
            return q(f"O que {sujeito} disponibiliza")
        if verbo == "retorna":
            return q(f"O que {sujeito} retorna")
        if verbo in {"armazena", "guarda"}:
            return q(f"O que {sujeito} armazena")
        if verbo == "permite":
            return q(f"O que {sujeito} permite")
        if verbo in {"exige", "evita", "evitam", "resolve", "melhora", "indica",
                     "libera", "trata", "chama", "imprime", "infere", "ajuda",
                     "ajudam", "avalia", "obtém", "concede", "organiza"}:
            return q(f"O que {sujeito} {verbo}")
        if verbo.startswith("difer"):
            return q(f"Qual a diferença em {sujeito}")
        return q(f"O que {sujeito} {verbo}")

    # Código + expressão curta no final
    # Int a = 5, b = 2; a / b ?
    m = re.match(r"^(.+;)\s*([A-Za-z_][\w]*)\s*([/%+\-*|&^]+)\s*([A-Za-z_][\w]*)\s*\?$", e)
    if m:
        return q(f"Dado o código `{m.group(1).strip()}`, qual o resultado de {m.group(2)} {m.group(3)} {m.group(4)}")

    # Boolean r = ...; r ?
    m = re.match(r"^(.+;)\s*([A-Za-z_][\w]*)\s*\?$", e)
    if m:
        return q(f"Dado o código `{m.group(1).strip()}`, qual o valor final de {m.group(2)}")

    # Int x = 5; x++; Qual valor final de x?  (já quase bom, padroniza)
    m = re.match(r"^(.+;)\s*Qual valor final de (.+)\??$", e, flags=re.I)
    if m:
        return q(f"Dado o código `{m.group(1).strip()}`, qual o valor final de {m.group(2).rstrip('?')}")

    # Int x = 5; ++x; Qual valor final...
    m = re.match(r"^(.+)\s+Qual valor final de (.+)\??$", e, flags=re.I)
    if m and ";" in m.group(1):
        return q(f"Dado o código `{m.group(1).strip()}`, qual o valor final de {m.group(2).rstrip('?')}")

    # Bool true && false ?
    m = re.match(r"^(Bool(?:ean)?)\s+(.+)\s*\?$", e, flags=re.I)
    if m and re.search(r"(&&|\|\||!)", m.group(2)):
        return q(f"Qual o resultado da expressão {m.group(2).strip()}")

    # Expressões soltas: 5/2 com ints ? / 5%2 ?
    m = re.match(r"^(\d+\s*[/%]\s*\d+)(.*)\?$", e)
    if m:
        extra = m.group(2).strip(" ,")
        if extra:
            return q(f"Qual o resultado de {m.group(1)} {extra}")
        return q(f"Qual o resultado de {m.group(1)}")

    # "X vs Y ?" / "X vs Y: ..."
    m = re.match(r"^(.+?)\s+vs\s+(.+?)(?::\s*(.+))?\??$", e, flags=re.I)
    if m and not re.match(r"^(Qual|Como|Para|O que)\b", e, re.I):
        if m.group(3):
            return q(f"Sobre {m.group(1).strip()} versus {m.group(2).strip()}, {m.group(3).strip()}")
        return q(f"Qual a diferença entre {m.group(1).strip()} e {m.group(2).strip()}")

    # Frases muito curtas terminando só com nome + ?
    # "Construtor tem?" já tratado. "Comentário de linha usa?"
    m = re.match(r"^(.+?)\s+(usa|usa tipicamente|gera|significa tipicamente)\??$", e, flags=re.I)
    if m and not re.match(r"^(Qual|Como|Para|O que)\b", e, re.I):
        return q(f"O que {m.group(1).strip()} {m.group(2).lower()}")

    # "Ponto de entrada padrão é?" / "O ponto de entrada padrão é?"
    m = re.match(r"^(O\s+)?(.+?)\s+é\??$", e, flags=re.I)
    if m and not re.match(r"^(Qual|Como|Para|O que)\b", e, re.I) and len(e.split()) <= 8:
        sujeito = m.group(2).strip()
        # evita transformar "Qual tipo ... é" etc.
        if not sujeito.lower().startswith(("qual ", "como ", "para ")):
            return q(f"Qual é {sujeito}")

    # "índices?" / "Array C int a[3] índices?"
    if re.search(r"\bíndices\??$", e, re.I) and not re.match(r"^(Qual|Como|Para|O que)\b", e, re.I):
        base = re.sub(r"\s*índices\??$", "", e, flags=re.I).strip()
        return q(f"Quais são os índices válidos de {base}")

    # "Std::cout << \"Hi\"; imprime?"
    m = re.match(r"^(.+;)\s*imprime\??$", e, flags=re.I)
    if m:
        return q(f"O que o código `{m.group(1).strip()}` imprime")

    # Auto x = 1; infere?
    m = re.match(r"^(.+;)\s*infere\??$", e, flags=re.I)
    if m:
        return q(f"Dado o código `{m.group(1).strip()}`, qual tipo é inferido")

    # Nullptr == nullptr ?
    if re.search(r"==|!=|&&|\|\|", e) and e.rstrip().endswith("?") and not re.match(
        r"^(Qual|Como|Para|O que|Dado)\b", e, re.I
    ):
        expr = e.rstrip("?").strip()
        if len(expr.split()) <= 6 and ";" not in expr:
            return q(f"Qual o resultado da expressão {expr}")

    # Já está bom (Qual/Como/Para que/O que/Dado)
    if re.match(r"^(Qual|Como|Para que|O que|Dado|Quais|Quando|Em qual)\b", e, re.I):
        return q(e)

    # Fallback: se ainda parece fragmento curto, completa com base na resposta
    if len(e.rstrip("?").split()) <= 4:
        resp = correta_texto(item)
        # "X?" genérico
        termo = e.rstrip("?")
        if resp and len(resp.split()) >= 2:
            return q(f"Sobre {termo}, qual alternativa está correta")
        return q(f"O que significa {termo}")

    return q(e)


def parece_vaga(e: str) -> bool:
    e = e.strip()
    baixa = e.lower()
    if re.match(r"^(Em|No)\s+(Java|Python|C\+\+)", e, re.I):
        return True
    if re.search(r"\bocorre ao\??$", e, re.I):
        return True
    if re.search(r"\b(serve|usado|comum) para\??$", e, re.I):
        return True
    if re.match(r"^(O comando|Um |Uma |Break |Continue )\b", e, re.I) and len(e.split()) <= 6:
        return True
    if re.match(r"^[A-Za-z_:<>(\)./=+\-]+\??$", e):
        return True
    if ";" in e and re.search(r"\b[A-Za-z_]\w*\s*\?$", e) and not re.match(r"^Dado\b", e, re.I):
        return True
    if not re.match(r"^(Qual|Como|Para que|O que|Dado|Quais|Quando|Em qual)\b", e, re.I):
        if len(e.split()) <= 6:
            return True
        if re.search(r"\b(faz|é|tem|traz|retorna|armazena|guarda|imprime|infere)\??$", baixa):
            return True
    return False


def main() -> None:
    total = 0
    mudou = 0
    ainda = 0
    exemplos = []

    for path in sorted(SEED.glob("perguntas-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            total += 1
            antigo = item["enunciado"]
            novo = refatorar(antigo, item)
            if novo != antigo:
                mudou += 1
                item["enunciado"] = novo
            if parece_vaga(item["enunciado"]):
                ainda += 1
                if len(exemplos) < 25:
                    exemplos.append(item["enunciado"])

        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{path.name}: {len(data)} perguntas")
        for p in data[:3]:
            print(" ", p["enunciado"])

    print(f"Alteradas: {mudou}/{total} | ainda suspeitas: {ainda}")
    for ex in exemplos:
        print(" ainda:", ex)


if __name__ == "__main__":
    main()
