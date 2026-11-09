package ReiDoCodigo.back.Model.Service;

import ReiDoCodigo.back.Exception.RecursoNaoEncontradoException;
import ReiDoCodigo.back.Exception.RegraNegocioException;
import ReiDoCodigo.back.Model.Dto.NovoJogoRequest;
import ReiDoCodigo.back.Model.Dto.UsuarioRequest;
import ReiDoCodigo.back.Model.Dto.UsuarioResponse;
import ReiDoCodigo.back.Model.Entity.Usuario;
import ReiDoCodigo.back.Model.Repository.BatalhaRepository;
import ReiDoCodigo.back.Model.Repository.UsuarioRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashSet;
import java.util.List;

@Service
@RequiredArgsConstructor
public class UsuarioService {

    private final UsuarioRepository usuarioRepository;
    private final BatalhaRepository batalhaRepository;

    @Transactional
    public UsuarioResponse criar(UsuarioRequest request) {
        if (request.getNome() == null || request.getNome().isBlank()) {
            throw new RegraNegocioException("Nome do usuário é obrigatório.");
        }
        if (request.getLinguagem() == null) {
            throw new RegraNegocioException("Linguagem é obrigatória (JAVA, PYTHON ou CPP).");
        }
        if (request.getNivel() == null) {
            throw new RegraNegocioException("Nível é obrigatório (INICIANTE, INTERMEDIARIO ou AVANCADO).");
        }
        String nome = request.getNome().trim();
        Usuario existente = usuarioRepository.findByNome(nome).orElse(null);
        if (existente != null) {
            // Novo Jogo+: quem já venceu o Rei pode recomeçar com o mesmo usuário.
            if (Boolean.TRUE.equals(existente.getVenceuRei())) {
                batalhaRepository.deleteByUsuarioId(existente.getId());
                existente.setLinguagem(request.getLinguagem());
                existente.setNivel(request.getNivel());
                existente.setProgresso(1);
                existente.setVenceuRei(false);
                limparPerguntasUsadas(existente);
                return UsuarioResponse.from(usuarioRepository.save(existente));
            }
            throw new RegraNegocioException("Já existe um usuário com esse nome.");
        }

        Usuario usuario = Usuario.builder()
                .nome(request.getNome().trim())
                .linguagem(request.getLinguagem())
                .nivel(request.getNivel())
                .progresso(1)
                .venceuRei(false)
                .build();

        return UsuarioResponse.from(usuarioRepository.save(usuario));
    }

    @Transactional(readOnly = true)
    public UsuarioResponse buscarPorId(Long id) {
        return UsuarioResponse.from(buscarEntidade(id));
    }

    @Transactional(readOnly = true)
    public List<UsuarioResponse> listar() {
        return usuarioRepository.findAll().stream().map(UsuarioResponse::from).toList();
    }

    /**
     * Novo Jogo+: recomeça a jornada com o mesmo usuário.
     * Zera o progresso, limpa as batalhas antigas e permite,
     * opcionalmente, trocar linguagem e nível para a nova jornada.
     */
    @Transactional
    public UsuarioResponse novoJogo(Long id, NovoJogoRequest request) {
        Usuario usuario = buscarEntidade(id);

        batalhaRepository.deleteByUsuarioId(usuario.getId());

        if (request != null && request.getLinguagem() != null) {
            usuario.setLinguagem(request.getLinguagem());
        }
        if (request != null && request.getNivel() != null) {
            usuario.setNivel(request.getNivel());
        }

        usuario.setProgresso(1);
        usuario.setVenceuRei(false);
        limparPerguntasUsadas(usuario);

        return UsuarioResponse.from(usuarioRepository.save(usuario));
    }

    private void limparPerguntasUsadas(Usuario usuario) {
        if (usuario.getPerguntasUsadas() == null) {
            usuario.setPerguntasUsadas(new HashSet<>());
            return;
        }
        usuario.getPerguntasUsadas().clear();
    }

    @Transactional
    public void excluir(Long id) {
        Usuario usuario = buscarEntidade(id);
        batalhaRepository.deleteByUsuarioId(usuario.getId());
        usuarioRepository.delete(usuario);
    }

    public Usuario buscarEntidade(Long id) {
        return usuarioRepository.findById(id)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Usuário não encontrado: " + id));
    }
}
