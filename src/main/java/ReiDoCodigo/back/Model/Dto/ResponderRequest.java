package ReiDoCodigo.back.Model.Dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ResponderRequest {
    private Long perguntaId;
    /** A, B, C ou D */
    private String alternativa;
}
