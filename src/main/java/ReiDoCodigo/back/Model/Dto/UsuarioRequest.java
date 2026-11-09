package ReiDoCodigo.back.Model.Dto;

import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Model.Enum.NivelDificuldade;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UsuarioRequest {
    private String nome;
    private Linguagem linguagem;
    private NivelDificuldade nivel;
}
