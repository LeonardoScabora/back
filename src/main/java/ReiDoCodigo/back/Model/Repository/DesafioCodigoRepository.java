package ReiDoCodigo.back.Model.Repository;

import ReiDoCodigo.back.Model.Entity.DesafioCodigo;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DesafioCodigoRepository extends JpaRepository<DesafioCodigo, Long> {
    List<DesafioCodigo> findAllByInimigoIdAndLinguagem(Long inimigoId, Linguagem linguagem);

    long countByInimigoId(Long inimigoId);
}
