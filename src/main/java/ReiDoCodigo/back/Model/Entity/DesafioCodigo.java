package ReiDoCodigo.back.Model.Entity;

import ReiDoCodigo.back.Model.Enum.Linguagem;
import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "desafios_codigo")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DesafioCodigo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "inimigo_id", nullable = false)
    private Inimigo inimigo;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Linguagem linguagem;

    @Column(nullable = false, length = 4000)
    private String enunciado;

    @Column(length = 2000)
    private String codigoInicial;

    @Column(length = 1000)
    private String entradaExemplo;

    @Column(length = 1000)
    private String saidaExemplo;
}
