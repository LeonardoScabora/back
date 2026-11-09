package ReiDoCodigo.back.Model.Service;

import ReiDoCodigo.back.Exception.RecursoNaoEncontradoException;
import ReiDoCodigo.back.Model.Dto.InimigoResponse;
import ReiDoCodigo.back.Model.Entity.Inimigo;
import ReiDoCodigo.back.Model.Repository.InimigoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class InimigoService {

    private final InimigoRepository inimigoRepository;

    @Transactional(readOnly = true)
    public List<InimigoResponse> listarCorredor() {
        return inimigoRepository.findAllByOrderByOrdemNoCorredorAsc()
                .stream()
                .map(InimigoResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public InimigoResponse buscarPorId(Long id) {
        return InimigoResponse.from(buscarEntidade(id));
    }

    @Transactional(readOnly = true)
    public InimigoResponse buscarPorOrdem(Integer ordem) {
        Inimigo inimigo = inimigoRepository.findByOrdemNoCorredor(ordem)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Inimigo não encontrado na ordem: " + ordem));
        return InimigoResponse.from(inimigo);
    }

    public Inimigo buscarEntidade(Long id) {
        return inimigoRepository.findById(id)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Inimigo não encontrado: " + id));
    }
}
