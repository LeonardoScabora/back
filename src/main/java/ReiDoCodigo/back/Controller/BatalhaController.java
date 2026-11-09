package ReiDoCodigo.back.Controller;

import ReiDoCodigo.back.Model.Dto.*;
import ReiDoCodigo.back.Model.Service.BatalhaService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/batalhas")
@RequiredArgsConstructor
public class BatalhaController {

    private final BatalhaService batalhaService;

    @PostMapping("/iniciar")
    @ResponseStatus(HttpStatus.CREATED)
    public BatalhaResponse iniciar(@RequestParam Long usuarioId, @RequestParam Long inimigoId) {
        return batalhaService.iniciar(usuarioId, inimigoId);
    }

    @GetMapping("/{id}")
    public BatalhaResponse buscar(@PathVariable Long id) {
        return batalhaService.buscar(id);
    }

    @GetMapping("/{id}/proxima-pergunta")
    public PerguntaResponse proximaPergunta(@PathVariable Long id) {
        return batalhaService.proximaPergunta(id);
    }

    @PostMapping("/{id}/responder")
    public ResultadoAcaoResponse responder(@PathVariable Long id, @RequestBody ResponderRequest request) {
        return batalhaService.responder(id, request);
    }

    @PostMapping("/{id}/dev/acertar")
    public ResultadoAcaoResponse acertarEtapaDev(@PathVariable Long id) {
        return batalhaService.acertarEtapaDev(id);
    }

    @GetMapping("/{id}/desafio")
    public DesafioCodigoResponse obterDesafio(@PathVariable Long id) {
        return batalhaService.obterDesafio(id);
    }

    @PostMapping("/{id}/terminal/iniciar")
    public TerminalSessaoResponse iniciarTerminal(
            @PathVariable Long id,
            @RequestBody ExecutarCodigoRequest request
    ) {
        return batalhaService.iniciarTerminal(id, request);
    }

    @PostMapping("/{id}/terminal/{sessionId}/entrada")
    public TerminalSessaoResponse enviarEntradaTerminal(
            @PathVariable Long id,
            @PathVariable String sessionId,
            @RequestBody TerminalEntradaRequest request
    ) {
        return batalhaService.enviarEntradaTerminal(id, sessionId, request);
    }

    @PostMapping("/{id}/terminal/{sessionId}/encerrar")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void encerrarTerminal(@PathVariable Long id, @PathVariable String sessionId) {
        batalhaService.encerrarTerminal(id, sessionId);
    }

    @PostMapping("/{id}/submeter-codigo")
    public ResultadoAcaoResponse submeterCodigo(@PathVariable Long id, @RequestBody SubmeterCodigoRequest request) {
        return batalhaService.submeterCodigo(id, request);
    }
}
