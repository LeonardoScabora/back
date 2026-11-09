package ReiDoCodigo.back.Model.Entity;

import ReiDoCodigo.back.Model.Enum.TipoInimigo;
import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "inimigos")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Inimigo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String nome;

    @Column(nullable = false, unique = true)
    private Integer ordemNoCorredor;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private TipoInimigo tipo;

    /** Acertos necessários para derrotar (quiz: 2, código: 1, rei: 5). */
    @Column(nullable = false)
    @Builder.Default
    private Integer vidaMaxima = 2;

    @Column(nullable = false)
    @Builder.Default
    private Boolean ehRei = false;

    private String descricao;
}
