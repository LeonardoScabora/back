# -*- coding: utf-8 -*-
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from editorial_p1 import norm, to_question

path = Path("src/main/resources/seed/perguntas-cpp.json")
data = json.loads(path.read_text(encoding="utf-8"))

keep = []
for p in data:
    e = p["enunciado"]
    if re.search(r"manutenibilidade", e, re.I):
        continue
    if re.search(r"fundamento do nível", e, re.I):
        continue
    keep.append(p)

bank = [
    ("Qual palavra-chave declara uma referência constante a objeto?", ["const T& / const", "var", "let", "immutable"], "A"),
    ("Qual cabeçalho declara sobrecargas de getline para strings?", ["<string>", "<iostream> only", "<cstdio>", "<fstream> only"], "A"),
    ("Qual operador é comum em condição de loop de leitura com cin?", [">>", "<<", "=>", "?:"], "A"),
    ("Qual tipo é adequado para contar elementos sem sinal?", ["size_t", "int sempre", "char", "bool"], "A"),
    ("Qual vantagem principal de raw string literals?", ["reduzir escapes em textos longos", "criar ponteiros", "definir templates", "iniciar threads"], "A"),
    ("O que a palavra-chave auto deduz?", ["tipo da variável a partir do inicializador", "somente ponteiros", "somente templates", "somente retornos void"], "A"),
    ("Qual diferença principal entre struct e class no acesso padrão?", ["struct é public por padrão; class é private", "struct não pode ter métodos", "class não pode ter dados", "não há diferença alguma"], "A"),
    ("Qual cabeçalho traz std::pair?", ["<utility>", "<pair>", "<tuple>", "<map>"], "A"),
    ("Qual função troca dois valores de forma idiomática?", ["std::swap", "std::move only", "std::exchange only", "std::copy"], "A"),
    ("Qual container permite inserção/remoção eficiente nas duas pontas?", ["std::deque", "std::array", "std::set", "std::forward_list only"], "A"),
    ("Qual container é lista simplesmente encadeada?", ["std::forward_list", "std::list", "std::vector", "std::deque"], "A"),
    ("O que static em variável local de função preserva?", ["valor entre chamadas", "escopo global obrigatório", "impedimento de inline", "criação de thread"], "A"),
    ("O que #pragma once ajuda a evitar?", ["inclusão múltipla do mesmo header", "erros de link", "UB", "RTTI"], "A"),
]

by = {1: [], 2: [], 3: []}
used = set()
for p in keep:
    k = norm(p["enunciado"])
    if k in used:
        continue
    used.add(k)
    by[int(p["dificuldade"])].append(p)

for enunciado, alts, corr in bank:
    if len(by[1]) >= 150:
        break
    e = enunciado if enunciado.endswith("?") else enunciado + "?"
    k = norm(e)
    if k in used:
        continue
    used.add(k)
    by[1].append(to_question(e, alts, corr, 1))

assert len(by[1]) >= 150 and len(by[2]) == 100 and len(by[3]) == 250, {d: len(by[d]) for d in by}
by[1] = by[1][:150]
final = by[1] + by[2] + by[3]
path.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(
    "cpp",
    len(final),
    {d: len(by[d]) for d in by},
    "unique",
    len({norm(p["enunciado"]) for p in final}),
    "manut",
    sum(1 for p in final if "manutenibilidade" in p["enunciado"]),
)
