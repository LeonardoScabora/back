package ReiDoCodigo.back.Model.Dto;

import ReiDoCodigo.back.Model.Entity.DesafioCodigo;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class DesafioCodigoResponse {
    private Long id;
    private Long inimigoId;
    private Linguagem linguagem;
    private String enunciado;
    private String codigoInicial;
    private String entradaExemplo;
    private String saidaExemplo;

    public static DesafioCodigoResponse from(DesafioCodigo desafio) {
        return DesafioCodigoResponse.builder()
                .id(desafio.getId())
                .inimigoId(desafio.getInimigo().getId())
                .linguagem(desafio.getLinguagem())
                .enunciado(desafio.getEnunciado())
                .codigoInicial(desafio.getCodigoInicial())
                .entradaExemplo(desafio.getEntradaExemplo())
                .saidaExemplo(desafio.getSaidaExemplo())
                .build();
    }
}
