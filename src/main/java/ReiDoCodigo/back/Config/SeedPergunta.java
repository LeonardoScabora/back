package ReiDoCodigo.back.Config;

import ReiDoCodigo.back.Model.Enum.Linguagem;

public record SeedPergunta(
        Linguagem linguagem,
        int dificuldade,
        String enunciado,
        String alternativaA,
        String alternativaB,
        String alternativaC,
        String alternativaD,
        String respostaCorreta
) {
}
