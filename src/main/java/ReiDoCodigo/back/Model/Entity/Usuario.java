package ReiDoCodigo.back.Model.Entity;

import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Model.Enum.NivelDificuldade;
import jakarta.persistence.*;
import lombok.*;

import java.util.HashSet;
import java.util.Set;

@Entity
@Table(name = "usuarios")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Usuario {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String nome;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Linguagem linguagem;

    /** Nível escolhido no início: o jogador só recebe perguntas deste grau. */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private NivelDificuldade nivel;

    /** Progresso no corredor: ordem do próximo inimigo a enfrentar. */
    @Column(nullable = false)
    @Builder.Default
    private Integer progresso = 1;

    @Column(nullable = false)
    @Builder.Default
    private Boolean venceuRei = false;

    /**
     * IDs das perguntas já vistas nesta run (acerto ou erro).
     * Zera no Novo Jogo+ para a jornada recomeçar do zero.
     */
    @Builder.Default
    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(
            name = "usuario_perguntas_usadas",
            joinColumns = @JoinColumn(name = "usuario_id")
    )
    @Column(name = "pergunta_id", nullable = false)
    private Set<Long> perguntasUsadas = new HashSet<>();
}
