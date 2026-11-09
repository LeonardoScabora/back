package ReiDoCodigo.back.Model.Repository;

import ReiDoCodigo.back.Model.Entity.Perguntas;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Model.Enum.NivelDificuldade;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PerguntasRepository extends JpaRepository<Perguntas, Long> {

    List<Perguntas> findByLinguagemAndNivelOrderByOrdemAsc(Linguagem linguagem, NivelDificuldade nivel);

    List<Perguntas> findByInimigoIdAndLinguagemOrderByOrdemAsc(Long inimigoId, Linguagem linguagem);

    List<Perguntas> findByInimigoIdOrderByOrdemAsc(Long inimigoId);

    long countByLinguagem(Linguagem linguagem);

    long countByLinguagemAndNivel(Linguagem linguagem, NivelDificuldade nivel);

    long countByInimigoIdAndLinguagem(Long inimigoId, Linguagem linguagem);
}
