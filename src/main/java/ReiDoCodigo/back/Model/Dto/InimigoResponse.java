package ReiDoCodigo.back.Model.Dto;

import ReiDoCodigo.back.Model.Entity.Inimigo;
import ReiDoCodigo.back.Model.Enum.TipoInimigo;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class InimigoResponse {
    private Long id;
    private String nome;
    private Integer ordemNoCorredor;
    private TipoInimigo tipo;
    private Integer vidaMaxima;
    private Boolean ehRei;
    private String descricao;

    public static InimigoResponse from(Inimigo inimigo) {
        return InimigoResponse.builder()
                .id(inimigo.getId())
                .nome(inimigo.getNome())
                .ordemNoCorredor(inimigo.getOrdemNoCorredor())
                .tipo(inimigo.getTipo())
                .vidaMaxima(inimigo.getVidaMaxima())
                .ehRei(inimigo.getEhRei())
                .descricao(inimigo.getDescricao())
                .build();
    }
}
