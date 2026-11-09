package ReiDoCodigo.back.Model.Dto;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class TerminalSessaoResponse {
    private String sessionId;
    private String stdout;
    private String stderr;
    private boolean aguardandoEntrada;
    private boolean finalizado;
    private boolean sucesso;
    private String mensagem;
}
