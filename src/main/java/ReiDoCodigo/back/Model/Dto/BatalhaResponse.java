package ReiDoCodigo.back.Model.Dto;

import ReiDoCodigo.back.Model.Entity.Batalha;
import ReiDoCodigo.back.Model.Enum.StatusBatalha;
import ReiDoCodigo.back.Model.Enum.TipoInimigo;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class BatalhaResponse {
    private Long id;
    private Long usuarioId;
    private Long inimigoId;
    private String nomeInimigo;
    private TipoInimigo tipoInimigo;
    private Integer vidaJogador;
    private Integer vidaInimigo;
    private StatusBatalha status;
    private Integer perguntaAtual;
    private Boolean ehRei;
    /** Rei: última vida é desafio de algoritmo. */
    private Boolean faseCodigo;

    public static BatalhaResponse from(Batalha batalha) {
        boolean rei = Boolean.TRUE.equals(batalha.getInimigo().getEhRei());
        boolean faseCodigo = rei && batalha.getVidaInimigo() != null && batalha.getVidaInimigo() <= 1;
        return BatalhaResponse.builder()
                .id(batalha.getId())
                .usuarioId(batalha.getUsuario().getId())
                .inimigoId(batalha.getInimigo().getId())
                .nomeInimigo(batalha.getInimigo().getNome())
                .tipoInimigo(batalha.getInimigo().getTipo())
                .vidaJogador(batalha.getVidaJogador())
                .vidaInimigo(batalha.getVidaInimigo())
                .status(batalha.getStatus())
                .perguntaAtual(batalha.getPerguntaAtual())
                .ehRei(rei)
                .faseCodigo(faseCodigo)
                .build();
    }
}
