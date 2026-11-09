package ReiDoCodigo.back.Model.Repository;

import ReiDoCodigo.back.Model.Entity.Inimigo;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface InimigoRepository extends JpaRepository<Inimigo, Long> {
    List<Inimigo> findAllByOrderByOrdemNoCorredorAsc();
    Optional<Inimigo> findByOrdemNoCorredor(Integer ordemNoCorredor);
}
