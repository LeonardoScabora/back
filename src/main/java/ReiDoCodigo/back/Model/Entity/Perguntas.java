package ReiDoCodigo.back.Model.Entity;

import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Model.Enum.NivelDificuldade;
import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(
        name = "perguntas",
        indexes = {
                @Index(name = "idx_perguntas_linguagem_nivel", columnList = "linguagem, nivel")
        }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Perguntas {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Mantido para compatibilidade/organização; o sorteio do jogo filtra por linguagem + nível do jogador.
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "inimigo_id")
    private Inimigo inimigo;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Linguagem linguagem;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private NivelDificuldade nivel;

    @Column(nullable = false, length = 2000)
    private String enunciado;

    @Column(name = "alternativa_a", nullable = false)
    private String alternativaA;

    @Column(name = "alternativa_b", nullable = false)
    private String alternativaB;

    @Column(name = "alternativa_c", nullable = false)
    private String alternativaC;

    @Column(name = "alternativa_d", nullable = false)
    private String alternativaD;

    /** Valor esperado: A, B, C ou D. */
    @Column(nullable = false, length = 1)
    private String respostaCorreta;

    @Column(nullable = false)
    private Integer ordem;
}
