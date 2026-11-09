package ReiDoCodigo.back.Controller;

import ReiDoCodigo.back.Model.Dto.InimigoResponse;
import ReiDoCodigo.back.Model.Service.InimigoService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/inimigos")
@RequiredArgsConstructor
public class InimigoController {

    private final InimigoService inimigoService;

    @GetMapping
    public List<InimigoResponse> listarCorredor() {
        return inimigoService.listarCorredor();
    }

    @GetMapping("/{id}")
    public InimigoResponse buscar(@PathVariable Long id) {
        return inimigoService.buscarPorId(id);
    }

    @GetMapping("/ordem/{ordem}")
    public InimigoResponse buscarPorOrdem(@PathVariable Integer ordem) {
        return inimigoService.buscarPorOrdem(ordem);
    }
}
