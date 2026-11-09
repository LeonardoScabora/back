package ReiDoCodigo.back.Model.Service;

import ReiDoCodigo.back.Exception.RecursoNaoEncontradoException;
import ReiDoCodigo.back.Exception.RegraNegocioException;
import ReiDoCodigo.back.Model.Dto.PerguntaResponse;
import ReiDoCodigo.back.Model.Entity.Perguntas;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Model.Enum.NivelDificuldade;
import ReiDoCodigo.back.Model.Repository.PerguntasRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class PerguntasService {

    private final PerguntasRepository perguntasRepository;

    @Transactional(readOnly = true)
    public List<PerguntaResponse> listar(Linguagem linguagem, NivelDificuldade nivel, Long inimigoId) {
        if (linguagem != null && nivel != null) {
            return perguntasRepository.findByLinguagemAndNivelOrderByOrdemAsc(linguagem, nivel)
                    .stream()
                    .map(PerguntaResponse::from)
                    .toList();
        }
        if (inimigoId != null && linguagem != null) {
            return perguntasRepository.findByInimigoIdAndLinguagemOrderByOrdemAsc(inimigoId, linguagem)
                    .stream()
                    .map(PerguntaResponse::from)
                    .toList();
        }
        if (inimigoId != null) {
            return perguntasRepository.findByInimigoIdOrderByOrdemAsc(inimigoId)
                    .stream()
                    .map(PerguntaResponse::from)
                    .toList();
        }
        throw new RegraNegocioException("Informe linguagem+nivel, ou inimigoId.");
    }

    public Perguntas buscarEntidade(Long id) {
        return perguntasRepository.findById(id)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Pergunta não encontrada: " + id));
    }
}
