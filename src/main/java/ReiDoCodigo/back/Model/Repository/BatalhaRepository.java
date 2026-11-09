package ReiDoCodigo.back.Model.Repository;

import ReiDoCodigo.back.Model.Entity.Batalha;
import ReiDoCodigo.back.Model.Enum.StatusBatalha;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface BatalhaRepository extends JpaRepository<Batalha, Long> {
    Optional<Batalha> findFirstByUsuarioIdAndInimigoIdAndStatusOrderByIniciadaEmDesc(
            Long usuarioId,
            Long inimigoId,
            StatusBatalha status
    );

    void deleteByUsuarioId(Long usuarioId);
}
