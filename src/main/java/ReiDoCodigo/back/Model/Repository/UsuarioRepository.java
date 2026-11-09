package ReiDoCodigo.back.Model.Repository;

import ReiDoCodigo.back.Model.Entity.Usuario;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UsuarioRepository extends JpaRepository<Usuario, Long> {
    Optional<Usuario> findByNome(String nome);
    boolean existsByNome(String nome);
}
