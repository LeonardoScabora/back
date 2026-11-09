package ReiDoCodigo.back.Model.Repository;

import ReiDoCodigo.back.Model.Entity.CasoTeste;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CasoTesteRepository extends JpaRepository<CasoTeste, Long> {
    List<CasoTeste> findByDesafioIdOrderByOrdemAsc(Long desafioId);
}
