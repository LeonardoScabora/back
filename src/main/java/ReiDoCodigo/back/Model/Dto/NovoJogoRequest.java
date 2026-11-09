package ReiDoCodigo.back.Model.Dto;

import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Model.Enum.NivelDificuldade;
import lombok.Getter;
import lombok.Setter;

/**
 * Dados opcionais para recomeçar a jornada (Novo Jogo+).
 * Se linguagem/nivel não forem informados, mantém os atuais do usuário.
 */
@Getter
@Setter
public class NovoJogoRequest {
    private Linguagem linguagem;
    private NivelDificuldade nivel;
}
