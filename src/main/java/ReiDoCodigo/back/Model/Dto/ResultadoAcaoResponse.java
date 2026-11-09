package ReiDoCodigo.back.Model.Dto;

import ReiDoCodigo.back.Model.Enum.StatusBatalha;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class ResultadoAcaoResponse {
    private boolean acertou;
    private Integer vidaJogador;
    private Integer vidaInimigo;
    private StatusBatalha status;
    private String mensagem;
    private String stdout;
    private String stderr;
    /** Alternativa correta da pergunta respondida (apenas em batalhas de múltipla escolha). */
    private String alternativaCorreta;
}
