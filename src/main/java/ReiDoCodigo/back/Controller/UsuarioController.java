package ReiDoCodigo.back.Controller;

import ReiDoCodigo.back.Model.Dto.NovoJogoRequest;
import ReiDoCodigo.back.Model.Dto.UsuarioRequest;
import ReiDoCodigo.back.Model.Dto.UsuarioResponse;
import ReiDoCodigo.back.Model.Service.UsuarioService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/usuarios")
@RequiredArgsConstructor
public class UsuarioController {

    private final UsuarioService usuarioService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UsuarioResponse criar(@RequestBody UsuarioRequest request) {
        return usuarioService.criar(request);
    }

    @GetMapping
    public List<UsuarioResponse> listar() {
        return usuarioService.listar();
    }

    @GetMapping("/{id}")
    public UsuarioResponse buscar(@PathVariable Long id) {
        return usuarioService.buscarPorId(id);
    }

    /** Novo Jogo+: reinicia a jornada do usuário (progresso e batalhas). */
    @PostMapping("/{id}/novo-jogo")
    public UsuarioResponse novoJogo(@PathVariable Long id,
                                    @RequestBody(required = false) NovoJogoRequest request) {
        return usuarioService.novoJogo(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void excluir(@PathVariable Long id) {
        usuarioService.excluir(id);
    }
}
