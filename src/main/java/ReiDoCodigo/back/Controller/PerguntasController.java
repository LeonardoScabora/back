package ReiDoCodigo.back.Controller;

import ReiDoCodigo.back.Model.Dto.PerguntaResponse;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Model.Enum.NivelDificuldade;
import ReiDoCodigo.back.Model.Service.PerguntasService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/perguntas")
@RequiredArgsConstructor
public class PerguntasController {

    private final PerguntasService perguntasService;

    @GetMapping
    public List<PerguntaResponse> listar(
            @RequestParam(required = false) Linguagem linguagem,
            @RequestParam(required = false) NivelDificuldade nivel,
            @RequestParam(required = false) Long inimigoId
    ) {
        return perguntasService.listar(linguagem, nivel, inimigoId);
    }

    @GetMapping("/inimigo/{inimigoId}")
    public List<PerguntaResponse> listarPorInimigo(
            @PathVariable Long inimigoId,
            @RequestParam(required = false) Linguagem linguagem
    ) {
        return perguntasService.listar(linguagem, null, inimigoId);
    }
}
