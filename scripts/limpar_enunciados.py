#!/usr/bin/env python3
"""Reescreve enunciados mal formulados nos JSONs de seed."""

from __future__ import annotations

import json
import re
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "src" / "main" / "resources" / "seed"

_VERBOS = {
    "indica", "declara", "cria", "permite", "impede", "agrupa", "referencia", "lança",
    "trata", "inicia", "verifica", "concede", "compara", "atribui", "retornar", "retorna",
    "remover", "remove", "extrair", "extrai", "inserir", "insere", "obter", "obtem",
    "associar", "associa", "gerar", "gera", "imprimir", "imprime", "converter", "converte",
    "ordenar", "ordena", "definir", "define", "produzir", "produz", "aguardar", "aguarda",
    "aloca", "libera", "inclui", "introduz", "marca", "sugere", "nomeia", "obtém",
    "importa", "herda", "implementa", "armazena", "representa", "executa", "compila",
    "desloca", "nega", "incrementa", "decrementa", "captura", "propaga", "envolve",
    "mantém", "transforma", "materializa", "inspeciona", "combina", "filtra", "aplica",
}


def conceito(linguagem: str, significado: str) -> str:
    s = " ".join(significado.strip().rstrip(".?").split())
    if not s:
        return f"Em {linguagem}, qual é a alternativa correta?"
    lower = s[0].lower() + s[1:]
    primeiro = lower.split()[0]
    if primeiro in _VERBOS:
        return f"Em {linguagem}, o que {lower}?"
    if lower.startswith("tipo "):
        return f"Em {linguagem}, qual {lower}?"
    if lower.startswith("acesso "):
        return f"Em {linguagem}, qual modificador garante {lower}?"
    if lower.startswith(("um ", "uma ", "o ", "a ", "os ", "as ")):
        return f"Em {linguagem}, o que é {lower}?"
    if lower.startswith((
        "valor ", "ramo ", "campo ", "método ", "controle ", "visibilidade ",
        "verificação ", "precisão ", "inferência ", "programação ",
        "expressão ", "ponto ", "array ", "string ", "sem ",
    )):
        return f"Em {linguagem}, o que representa {lower}?"
    return f"Em {linguagem}, o que é responsável por {lower}?"


def lang_from_text(texto: str) -> str:
    t = texto.lower()
    if "python" in t:
        return "Python"
    if "c++" in t:
        return "C++"
    return "Java"


def limpar(enunciado: str) -> str:
    e = " ".join(enunciado.split())

    # Remove prefixos confusos de variação
    e = re.sub(r"^(Assinale a correta:\s*)", "", e, flags=re.I)
    e = re.sub(r"^(Escolha a opção correta\.\s*)", "", e, flags=re.I)
    e = re.sub(r"^(Indique a resposta\.\s*)", "", e, flags=re.I)
    e = re.sub(r"^(Marque a alternativa certa\.\s*)", "", e, flags=re.I)
    e = re.sub(r"^(Selecione a melhor opção\.\s*)", "", e, flags=re.I)
    e = re.sub(r"^(Com base na linguagem:\s*)", "", e, flags=re.I)
    e = re.sub(r"^(Sobre Java:\s*)", "Em Java, ", e, flags=re.I)
    e = re.sub(r"^(Sobre Python:\s*)", "Em Python, ", e, flags=re.I)
    e = re.sub(r"^(Sobre C\+\+:\s*)", "Em C++, ", e, flags=re.I)
    e = re.sub(r"^(Considerando Java,\s*)", "Em Java, ", e, flags=re.I)
    e = re.sub(r"^(Considerando Python,\s*)", "Em Python, ", e, flags=re.I)
    e = re.sub(r"^(Considerando C\+\+,\s*)", "Em C++, ", e, flags=re.I)
    e = re.sub(r"^(No Java,\s*)", "Em Java, ", e, flags=re.I)
    e = re.sub(r"^(No Python,\s*)", "Em Python, ", e, flags=re.I)
    e = re.sub(r"^(No C\+\+,\s*)", "Em C++, ", e, flags=re.I)
    e = re.sub(r"^(Na linguagem Java,\s*)", "Em Java, ", e, flags=re.I)
    e = re.sub(r"^(Na linguagem Python,\s*)", "Em Python, ", e, flags=re.I)
    e = re.sub(r"^(Na linguagem C\+\+,\s*)", "Em C++, ", e, flags=re.I)

    # Remove sufixos meta
    e = re.sub(
        r"\s*(Qual alternativa melhor responde|Qual opção é a adequada|Qual resposta está certa|"
        r"Qual item é o correto|Qual escolha é válida|Qual alternativa procede|"
        r"Qual opção corresponde|Qual resposta se aplica)\??\s*$",
        "",
        e,
        flags=re.I,
    )
    e = re.sub(r",\s*entre as opções abaixo\?", "?", e, flags=re.I)
    e = re.sub(r"\s+Selecione a alternativa correta\.?\s*$", "", e, flags=re.I)
    e = re.sub(r"\s+Assinale a opção correta\.?\s*$", "", e, flags=re.I)
    e = re.sub(r"\s+Indique a melhor resposta\.?\s*$", "", e, flags=re.I)
    e = re.sub(r"\s+Escolha a alternativa adequada\.?\s*$", "", e, flags=re.I)
    e = re.sub(r"\s+Marque a resposta certa\.?\s*$", "", e, flags=re.I)
    e = re.sub(r"\s+Qual das opções se aplica\??\s*$", "", e, flags=re.I)
    e = re.sub(r"\s+Escolha entre as alternativas\.?\s*$", "", e, flags=re.I)

    lang = lang_from_text(e)

    # Corrige formulação ruim já gravada
    m = re.match(
        r"Em (Java|Python|C\+\+),\s*o que é responsável por (.+)$",
        e,
        flags=re.I,
    )
    if m:
        return conceito(m.group(1), m.group(2))

    m = re.match(
        r"Em (Java|Python|C\+\+),\s*qual opção corresponde a:\s*(.+)$",
        e,
        flags=re.I,
    )
    if m:
        return conceito(m.group(1), m.group(2))

    # Caso o prefixo tenha sido removido e sobrou só o significado
    if not re.match(r"^(Em |No )", e, flags=re.I):
        if e.endswith("?"):
            return conceito(lang, e)
        return conceito(lang, e)

    m = re.match(
        r"Em (Java|Python|C\+\+),\s*o que melhor descreve '([^']+)'\??$",
        e,
        flags=re.I,
    )
    if m:
        return f"Em {m.group(1)}, para que serve '{m.group(2)}'?"

    m = re.match(
        r"Em (Java|Python|C\+\+),\s*o operador '([^']+)' serve para:\s*(.+)$",
        e,
        flags=re.I,
    )
    if m:
        return f"Em {m.group(1)}, para que serve o operador '{m.group(2)}'?"

    m = re.match(
        r"Em (Java|Python|C\+\+),\s*o que o método/API '([^']+)' de (.+) faz\??$",
        e,
        flags=re.I,
    )
    if m:
        return f"Em {m.group(1)}, para que serve '{m.group(2)}' em {m.group(3)}?"

    m = re.match(
        r"Em (Java|Python|C\+\+),\s*o que '([^']+)' (faz/representa|representa/faz)\??$",
        e,
        flags=re.I,
    )
    if m:
        return f"Em {m.group(1)}, para que serve '{m.group(2)}'?"

    # "indique/assinale qual" -> "qual"
    e = re.sub(r"\bindique qual\b", "qual", e, flags=re.I)
    e = re.sub(r"\bassinale qual\b", "qual", e, flags=re.I)

    if not e.endswith("?"):
        e = e.rstrip(".:") + "?"
    return e


def main() -> None:
    total = 0
    mudou = 0
    for path in sorted(SEED.glob("perguntas-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            total += 1
            novo = limpar(item["enunciado"])
            if novo != item["enunciado"]:
                mudou += 1
                item["enunciado"] = novo
        # Dedupa por enunciado mantendo a primeira ocorrência
        vistos = set()
        limpos = []
        for item in data:
            key = item["enunciado"].strip().lower()
            if key in vistos:
                continue
            vistos.add(key)
            limpos.append(item)

        # Se perdeu itens na dedupe, não truncar níveis — apenas avisar
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{path.name}: {len(data)} perguntas | reescritas nesta passada (antes dedupe check)")

        # Mostra exemplos do caso do usuário
        exemplos = [p["enunciado"] for p in data if "outro pacote" in p["enunciado"].lower() or "import" in p["enunciado"].lower()]
        for ex in exemplos[:3]:
            print("  ex:", ex)

    print(f"Total enunciados alterados: {mudou}/{total}")


if __name__ == "__main__":
    main()
