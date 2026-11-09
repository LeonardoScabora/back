package ReiDoCodigo.back.Model.Entity;

import ReiDoCodigo.back.Model.Enum.StatusBatalha;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "batalhas")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Batalha {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "usuario_id", nullable = false)
    private Usuario usuario;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "inimigo_id", nullable = false)
    private Inimigo inimigo;

    /** Erros permitidos até derrota (padrão: 3). */
    @Column(nullable = false)
    @Builder.Default
    private Integer vidaJogador = 3;

    @Column(nullable = false)
    private Integer vidaInimigo;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private StatusBatalha status = StatusBatalha.EM_ANDAMENTO;

    /** Contador da rodada de pergunta (1-based) para inimigos de múltipla escolha. */
    @Column(nullable = false)
    @Builder.Default
    private Integer perguntaAtual = 1;

    /** ID da pergunta atualmente sorteada para esta batalha (null = ainda não sorteada). */
    private Long perguntaAtualId;

    /** Última pergunta respondida nesta batalha. */
    private Long ultimaPerguntaId;

    /** Desafio de código sorteado para esta batalha (fixado até o fim). */
    private Long desafioAtualId;

    @Column(nullable = false)
    @Builder.Default
    private LocalDateTime iniciadaEm = LocalDateTime.now();

    private LocalDateTime finalizadaEm;
}
