package ReiDoCodigo.back.Model.Dto;

import ReiDoCodigo.back.Model.Entity.Perguntas;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Model.Enum.NivelDificuldade;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class PerguntaResponse {
    private Long id;
    private Linguagem linguagem;
    private NivelDificuldade nivel;
    private String enunciado;
    private String alternativaA;
    private String alternativaB;
    private String alternativaC;
    private String alternativaD;
    private Integer ordem;

    public static PerguntaResponse from(Perguntas pergunta) {
        return PerguntaResponse.builder()
                .id(pergunta.getId())
                .linguagem(pergunta.getLinguagem())
                .nivel(pergunta.getNivel())
                .enunciado(pergunta.getEnunciado())
                .alternativaA(pergunta.getAlternativaA())
                .alternativaB(pergunta.getAlternativaB())
                .alternativaC(pergunta.getAlternativaC())
                .alternativaD(pergunta.getAlternativaD())
                .ordem(pergunta.getOrdem())
                .build();
    }
}
