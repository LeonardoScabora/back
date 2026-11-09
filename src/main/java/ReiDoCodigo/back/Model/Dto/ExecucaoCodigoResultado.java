package ReiDoCodigo.back.Model.Dto;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class ExecucaoCodigoResultado {
    private boolean sucesso;
    private boolean erroInfraestrutura;
    private String stdout;
    private String stderr;
    private String mensagem;
}
