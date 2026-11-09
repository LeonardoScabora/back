package ReiDoCodigo.back.Model.Entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "casos_teste")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CasoTeste {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "desafio_id", nullable = false)
    private DesafioCodigo desafio;

    @Column(nullable = false, length = 2000)
    private String entrada;

    @Column(nullable = false, length = 2000)
    private String saidaEsperada;

    /** Se true, o aluno não vê a entrada/saída no feedback detalhado. */
    @Column(nullable = false)
    @Builder.Default
    private Boolean oculto = false;

    @Column(nullable = false)
    private Integer ordem;
}
