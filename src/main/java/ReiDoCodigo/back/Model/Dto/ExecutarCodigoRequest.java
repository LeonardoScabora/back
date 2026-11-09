package ReiDoCodigo.back.Model.Dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ExecutarCodigoRequest {
    private String codigo;
    private String stdin;
}
