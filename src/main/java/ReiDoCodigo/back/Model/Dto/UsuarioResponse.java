package ReiDoCodigo.back.Model.Dto;

import ReiDoCodigo.back.Model.Entity.Usuario;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Model.Enum.NivelDificuldade;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class UsuarioResponse {
    private Long id;
    private String nome;
    private Linguagem linguagem;
    private NivelDificuldade nivel;
    private Integer progresso;
    private Boolean venceuRei;

    public static UsuarioResponse from(Usuario usuario) {
        return UsuarioResponse.builder()
                .id(usuario.getId())
                .nome(usuario.getNome())
                .linguagem(usuario.getLinguagem())
                .nivel(usuario.getNivel())
                .progresso(usuario.getProgresso())
                .venceuRei(usuario.getVenceuRei())
                .build();
    }
}
