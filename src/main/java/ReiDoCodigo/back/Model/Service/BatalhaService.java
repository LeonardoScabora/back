package ReiDoCodigo.back.Model.Service;

import ReiDoCodigo.back.Exception.RecursoNaoEncontradoException;
import ReiDoCodigo.back.Exception.RegraNegocioException;
import ReiDoCodigo.back.Model.Dto.*;
import ReiDoCodigo.back.Model.Entity.*;
import ReiDoCodigo.back.Model.Enum.StatusBatalha;
import ReiDoCodigo.back.Model.Enum.TipoInimigo;
import ReiDoCodigo.back.Model.Repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ThreadLocalRandom;

@Service
@RequiredArgsConstructor
public class BatalhaService {

    private static final int VIDA_JOGADOR_PADRAO = 3;

    private final BatalhaRepository batalhaRepository;
    private final UsuarioService usuarioService;
    private final InimigoService inimigoService;
    private final PerguntasRepository perguntasRepository;
    private final DesafioCodigoRepository desafioCodigoRepository;
    private final CasoTesteRepository casoTesteRepository;
    private final UsuarioRepository usuarioRepository;
    private final CodeExecutionService codeExecutionService;
    private final InteractiveTerminalService interactiveTerminalService;

    @Transactional
    public BatalhaResponse iniciar(Long usuarioId, Long inimigoId) {
        Usuario usuario = usuarioService.buscarEntidade(usuarioId);
        Inimigo inimigo = inimigoService.buscarEntidade(inimigoId);

        if (!inimigo.getOrdemNoCorredor().equals(usuario.getProgresso())) {
            throw new RegraNegocioException(
                    "Você só pode enfrentar o inimigo da ordem " + usuario.getProgresso() + " no corredor."
            );
        }

        // Verificação desabilitada temporariamente — permite iniciar nova batalha mesmo com uma em andamento.
        // batalhaRepository.findFirstByUsuarioIdAndInimigoIdAndStatusOrderByIniciadaEmDesc(
        //         usuarioId, inimigoId, StatusBatalha.EM_ANDAMENTO
        // ).ifPresent(b -> {
        //     throw new RegraNegocioException("Já existe uma batalha em andamento contra este inimigo.");
        // });

        Batalha batalha = Batalha.builder()
                .usuario(usuario)
                .inimigo(inimigo)
                .vidaJogador(VIDA_JOGADOR_PADRAO)
                .vidaInimigo(inimigo.getVidaMaxima())
                .status(StatusBatalha.EM_ANDAMENTO)
                .perguntaAtual(1)
                .perguntaAtualId(null)
                .ultimaPerguntaId(null)
                .desafioAtualId(null)
                .iniciadaEm(LocalDateTime.now())
                .build();

        return BatalhaResponse.from(batalhaRepository.save(batalha));
    }

    @Transactional(readOnly = true)
    public BatalhaResponse buscar(Long batalhaId) {
        return BatalhaResponse.from(buscarEntidade(batalhaId));
    }

    @Transactional
    public PerguntaResponse proximaPergunta(Long batalhaId) {
        Batalha batalha = buscarEntidade(batalhaId);
        garantirEmAndamento(batalha);
        garantirQuiz(batalha);

        if (batalha.getPerguntaAtualId() != null) {
            Perguntas atual = perguntasRepository.findById(batalha.getPerguntaAtualId())
                    .orElseThrow(() -> new RecursoNaoEncontradoException(
                            "Pergunta atual da batalha não encontrada."
                    ));
            return PerguntaResponse.from(atual);
        }

        Perguntas pergunta = sortearPergunta(batalha);
        batalha.setPerguntaAtualId(pergunta.getId());
        batalhaRepository.save(batalha);
        return PerguntaResponse.from(pergunta);
    }

    @Transactional
    public ResultadoAcaoResponse responder(Long batalhaId, ResponderRequest request) {
        Batalha batalha = buscarEntidade(batalhaId);
        garantirEmAndamento(batalha);
        garantirQuiz(batalha);

        if (request.getPerguntaId() == null || request.getAlternativa() == null) {
            throw new RegraNegocioException("perguntaId e alternativa são obrigatórios.");
        }
        if (batalha.getPerguntaAtualId() == null
                || !batalha.getPerguntaAtualId().equals(request.getPerguntaId())) {
            throw new RegraNegocioException("Responda a pergunta atual sorteada da batalha.");
        }

        Perguntas pergunta = perguntasRepository.findById(request.getPerguntaId())
                .orElseThrow(() -> new RecursoNaoEncontradoException("Pergunta não encontrada."));

        Usuario jogador = batalha.getUsuario();
        if (pergunta.getLinguagem() != jogador.getLinguagem()) {
            throw new RegraNegocioException("Esta pergunta não pertence à linguagem do jogador.");
        }
        if (pergunta.getNivel() != jogador.getNivel()) {
            throw new RegraNegocioException("Esta pergunta não pertence ao nível escolhido pelo jogador.");
        }

        String alternativa = request.getAlternativa().trim().toUpperCase();
        if (!List.of("A", "B", "C", "D").contains(alternativa)) {
            throw new RegraNegocioException("Alternativa inválida. Use A, B, C ou D.");
        }

        boolean acertou = alternativa.equalsIgnoreCase(pergunta.getRespostaCorreta().trim());
        String mensagem = aplicarResultado(batalha, acertou,
                acertou ? "Golpe certeiro! O inimigo perdeu vida." : "Errou! Você perdeu vida.");

        // Libera o sorteio da próxima pergunta aleatória da mesma linguagem.
        batalha.setUltimaPerguntaId(pergunta.getId());
        batalha.setPerguntaAtualId(null);
        if (batalha.getStatus() == StatusBatalha.EM_ANDAMENTO) {
            batalha.setPerguntaAtual(batalha.getPerguntaAtual() + 1);
        }

        batalhaRepository.save(batalha);

        return ResultadoAcaoResponse.builder()
                .acertou(acertou)
                .vidaJogador(batalha.getVidaJogador())
                .vidaInimigo(batalha.getVidaInimigo())
                .status(batalha.getStatus())
                .mensagem(mensagem)
                .alternativaCorreta(pergunta.getRespostaCorreta().trim().toUpperCase())
                .build();
    }

    @Transactional
    public ResultadoAcaoResponse acertarEtapaDev(Long batalhaId) {
        Batalha batalha = buscarEntidade(batalhaId);
        garantirEmAndamento(batalha);

        if (batalha.getInimigo().getTipo() == TipoInimigo.CODIGO || reiEmFaseCodigo(batalha)) {
            garantirCodigo(batalha);
            String mensagem = aplicarResultado(
                    batalha,
                    true,
                    "Algoritmo aprovado pelo DEV mode."
            );
            batalha.setDesafioAtualId(null);
            batalhaRepository.save(batalha);

            return ResultadoAcaoResponse.builder()
                    .acertou(true)
                    .vidaJogador(batalha.getVidaJogador())
                    .vidaInimigo(batalha.getVidaInimigo())
                    .status(batalha.getStatus())
                    .mensagem(mensagem)
                    .stdout("Execução dos testes ignorada pelo DEV mode.")
                    .build();
        }

        garantirQuiz(batalha);

        if (batalha.getPerguntaAtualId() == null) {
            throw new RegraNegocioException("Carregue uma pergunta antes de usar o DEV mode.");
        }

        Perguntas pergunta = perguntasRepository.findById(batalha.getPerguntaAtualId())
                .orElseThrow(() -> new RecursoNaoEncontradoException(
                        "Pergunta atual da batalha não encontrada."
                ));

        String mensagem = aplicarResultado(
                batalha,
                true,
                "Acerto simulado pelo DEV mode."
        );

        batalha.setUltimaPerguntaId(pergunta.getId());
        batalha.setPerguntaAtualId(null);
        if (batalha.getStatus() == StatusBatalha.EM_ANDAMENTO) {
            batalha.setPerguntaAtual(batalha.getPerguntaAtual() + 1);
        }
        batalhaRepository.save(batalha);

        return ResultadoAcaoResponse.builder()
                .acertou(true)
                .vidaJogador(batalha.getVidaJogador())
                .vidaInimigo(batalha.getVidaInimigo())
                .status(batalha.getStatus())
                .mensagem(mensagem)
                .alternativaCorreta(pergunta.getRespostaCorreta().trim().toUpperCase())
                .build();
    }

    private DesafioCodigo resolverDesafioDaBatalha(Batalha batalha) {
        if (batalha.getDesafioAtualId() != null) {
            return desafioCodigoRepository.findById(batalha.getDesafioAtualId())
                    .orElseThrow(() -> new RecursoNaoEncontradoException(
                            "Desafio atual da batalha não encontrado."
                    ));
        }

        List<DesafioCodigo> opcoes = desafioCodigoRepository.findAllByInimigoIdAndLinguagem(
                batalha.getInimigo().getId(),
                batalha.getUsuario().getLinguagem()
        );
        if (opcoes.isEmpty()) {
            throw new RecursoNaoEncontradoException(
                    "Não há desafio de código para a linguagem " + batalha.getUsuario().getLinguagem()
            );
        }

        DesafioCodigo escolhido = opcoes.get(ThreadLocalRandom.current().nextInt(opcoes.size()));
        batalha.setDesafioAtualId(escolhido.getId());
        batalhaRepository.save(batalha);
        return escolhido;
    }

    /**
     * Sorteia uma pergunta da linguagem/nível do jogador que ainda não saiu nesta run.
     * Acerto ou erro não devolve a mesma pergunta; o histórico só zera no Novo Jogo+.
     */
    private Perguntas sortearPergunta(Batalha batalha) {
        Usuario jogador = batalha.getUsuario();
        List<Perguntas> pool = perguntasRepository.findByLinguagemAndNivelOrderByOrdemAsc(
                jogador.getLinguagem(),
                jogador.getNivel()
        );
        if (pool.isEmpty()) {
            throw new RecursoNaoEncontradoException(
                    "Não há perguntas de " + jogador.getLinguagem()
                            + " no nível " + jogador.getNivel() + "."
            );
        }

        if (jogador.getPerguntasUsadas() == null) {
            jogador.setPerguntasUsadas(new HashSet<>());
        }
        Set<Long> usadas = jogador.getPerguntasUsadas();

        List<Perguntas> disponiveis = pool.stream()
                .filter(p -> !usadas.contains(p.getId()))
                .toList();

        if (disponiveis.isEmpty()) {
            usadas.clear();
            disponiveis = pool;
        }

        Perguntas escolhida = disponiveis.get(ThreadLocalRandom.current().nextInt(disponiveis.size()));
        usadas.add(escolhida.getId());
        usuarioRepository.save(jogador);
        return escolhida;
    }

    @Transactional
    public DesafioCodigoResponse obterDesafio(Long batalhaId) {
        Batalha batalha = buscarEntidade(batalhaId);
        garantirEmAndamento(batalha);
        garantirCodigo(batalha);

        DesafioCodigo desafio = resolverDesafioDaBatalha(batalha);
        return DesafioCodigoResponse.from(desafio);
    }

    /**
     * Inicia sessão de terminal interativo (processo vivo).
     * Não altera vida nem status da batalha.
     */
    @Transactional
    public TerminalSessaoResponse iniciarTerminal(Long batalhaId, ExecutarCodigoRequest request) {
        Batalha batalha = buscarEntidade(batalhaId);
        garantirEmAndamento(batalha);
        garantirCodigo(batalha);
        resolverDesafioDaBatalha(batalha);

        if (request.getCodigo() == null || request.getCodigo().isBlank()) {
            throw new RegraNegocioException("O código é obrigatório.");
        }

        return interactiveTerminalService.iniciar(
                batalhaId,
                batalha.getUsuario().getLinguagem(),
                request.getCodigo()
        );
    }

    public TerminalSessaoResponse enviarEntradaTerminal(Long batalhaId, String sessionId, TerminalEntradaRequest request) {
        Batalha batalha = buscarEntidade(batalhaId);
        garantirEmAndamento(batalha);
        garantirCodigo(batalha);
        return interactiveTerminalService.enviarLinha(
                sessionId,
                batalhaId,
                request.getLinha() == null ? "" : request.getLinha()
        );
    }

    public void encerrarTerminal(Long batalhaId, String sessionId) {
        Batalha batalha = buscarEntidade(batalhaId);
        garantirCodigo(batalha);
        interactiveTerminalService.encerrar(sessionId, batalhaId);
    }

    @Transactional
    public ResultadoAcaoResponse submeterCodigo(Long batalhaId, SubmeterCodigoRequest request) {
        Batalha batalha = buscarEntidade(batalhaId);
        garantirEmAndamento(batalha);
        garantirCodigo(batalha);

        if (request.getCodigo() == null || request.getCodigo().isBlank()) {
            throw new RegraNegocioException("O código é obrigatório.");
        }

        DesafioCodigo desafio = resolverDesafioDaBatalha(batalha);

        List<CasoTeste> casos = casoTesteRepository.findByDesafioIdOrderByOrdemAsc(desafio.getId());
        if (casos.isEmpty()) {
            throw new RegraNegocioException("Este desafio não possui casos de teste.");
        }

        List<String> logsPublicos = new ArrayList<>();
        StringBuilder stderr = new StringBuilder();
        boolean passouTodos = true;

        for (CasoTeste caso : casos) {
            ExecucaoCodigoResultado execucao = codeExecutionService.executar(
                    batalha.getUsuario().getLinguagem(),
                    request.getCodigo(),
                    caso.getEntrada()
            );
            if (execucao.isErroInfraestrutura()) {
                throw new RegraNegocioException(execucao.getMensagem());
            }

            String saidaObtida = normalizar(execucao.getStdout());
            String saidaEsperada = normalizar(caso.getSaidaEsperada());
            boolean casoOk = execucao.isSucesso() && saidaCorresponde(saidaObtida, saidaEsperada);

            if (!Boolean.TRUE.equals(caso.getOculto())) {
                String obtidoExibido = formatarSaidaComEco(saidaObtida, caso.getEntrada());
                logsPublicos.add(
                        "Caso " + caso.getOrdem()
                                + " | entrada: " + caso.getEntrada().replace("\n", "\\n")
                                + " | esperado: " + saidaEsperada
                                + " | obtido:\n" + obtidoExibido
                                + "\n| " + (casoOk ? "OK" : "FALHOU")
                );
            }

            if (execucao.getStderr() != null && !execucao.getStderr().isBlank()) {
                stderr.append(execucao.getStderr()).append("\n");
            }

            if (!casoOk) {
                passouTodos = false;
                break;
            }
        }

        String mensagemBase = passouTodos
                ? "Seu algoritmo passou nos testes! Revise a saída abaixo e avance quando estiver pronto."
                : "Seu algoritmo falhou nos testes. Você perdeu vida.";

        String mensagem = aplicarResultado(batalha, passouTodos, mensagemBase);
        batalhaRepository.save(batalha);

        return ResultadoAcaoResponse.builder()
                .acertou(passouTodos)
                .vidaJogador(batalha.getVidaJogador())
                .vidaInimigo(batalha.getVidaInimigo())
                .status(batalha.getStatus())
                .mensagem(mensagem)
                .stdout(String.join("\n", logsPublicos))
                .stderr(stderr.toString().trim())
                .build();
    }

    private String aplicarResultado(Batalha batalha, boolean acertou, String mensagemBase) {
        if (acertou) {
            batalha.setVidaInimigo(batalha.getVidaInimigo() - 1);
        } else {
            batalha.setVidaJogador(batalha.getVidaJogador() - 1);
        }

        if (batalha.getVidaInimigo() <= 0) {
            batalha.setVidaInimigo(0);
            batalha.setStatus(StatusBatalha.VITORIA);
            batalha.setFinalizadaEm(LocalDateTime.now());
            avancarProgresso(batalha);
            return mensagemBase + " Vitória!";
        }

        if (batalha.getVidaJogador() <= 0) {
            batalha.setVidaJogador(0);
            batalha.setStatus(StatusBatalha.DERROTA);
            batalha.setFinalizadaEm(LocalDateTime.now());
            return mensagemBase + " Você foi derrotado.";
        }

        return mensagemBase;
    }

    private void avancarProgresso(Batalha batalha) {
        Usuario usuario = batalha.getUsuario();
        Inimigo inimigo = batalha.getInimigo();

        if (Boolean.TRUE.equals(inimigo.getEhRei())) {
            usuario.setVenceuRei(true);
        } else {
            usuario.setProgresso(usuario.getProgresso() + 1);
        }
        usuarioRepository.save(usuario);
    }

    private Batalha buscarEntidade(Long id) {
        return batalhaRepository.findById(id)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Batalha não encontrada: " + id));
    }

    private void garantirEmAndamento(Batalha batalha) {
        if (batalha.getStatus() != StatusBatalha.EM_ANDAMENTO) {
            throw new RegraNegocioException("Esta batalha já foi finalizada com status: " + batalha.getStatus());
        }
    }

    private boolean ehRei(Batalha batalha) {
        return Boolean.TRUE.equals(batalha.getInimigo().getEhRei());
    }

    /** Rei: as 4 primeiras vidas são quiz; a última é algoritmo. */
    private boolean reiEmFaseCodigo(Batalha batalha) {
        return ehRei(batalha) && batalha.getVidaInimigo() != null && batalha.getVidaInimigo() <= 1;
    }

    private void garantirQuiz(Batalha batalha) {
        if (ehRei(batalha)) {
            if (reiEmFaseCodigo(batalha)) {
                throw new RegraNegocioException("O Rei agora exige um algoritmo. Submeta o código.");
            }
            return;
        }
        garantirTipo(batalha, TipoInimigo.MULTIPLA_ESCOLHA);
    }

    private void garantirCodigo(Batalha batalha) {
        if (ehRei(batalha)) {
            if (!reiEmFaseCodigo(batalha)) {
                throw new RegraNegocioException("Derrote primeiro as perguntas do Rei.");
            }
            return;
        }
        garantirTipo(batalha, TipoInimigo.CODIGO);
    }

    private void garantirTipo(Batalha batalha, TipoInimigo tipoEsperado) {
        if (batalha.getInimigo().getTipo() != tipoEsperado) {
            throw new RegraNegocioException(
                    "Esta ação é inválida para inimigo do tipo " + batalha.getInimigo().getTipo()
            );
        }
    }

    private String normalizar(String valor) {
        if (valor == null) {
            return "";
        }
        return valor.replace("\r\n", "\n").trim();
    }

    /**
     * Reconstrói a saída como no terminal interativo: após cada prompt,
     * ecoa o próximo valor que foi lido da entrada do teste.
     */
    private String formatarSaidaComEco(String stdout, String stdin) {
        String saida = normalizar(stdout);
        if (saida.isEmpty()) {
            return saida;
        }

        List<String> entradas = tokenizarEntrada(stdin);
        if (entradas.isEmpty()) {
            return saida;
        }

        String[] linhas = saida.split("\n", -1);
        StringBuilder sb = new StringBuilder();
        int idx = 0;

        for (int i = 0; i < linhas.length; i++) {
            if (i > 0) {
                sb.append('\n');
            }
            sb.append(linhas[i]);

            String linha = linhas[i].trim();
            if (idx < entradas.size() && parecePrompt(linha)) {
                sb.append('\n').append(entradas.get(idx++));
            }
        }

        return sb.toString();
    }

    private List<String> tokenizarEntrada(String stdin) {
        List<String> tokens = new ArrayList<>();
        if (stdin == null || stdin.isBlank()) {
            return tokens;
        }
        String normalizado = stdin.replace("\r\n", "\n");
        // Se a entrada tem várias linhas, respeita linha a linha; senão, separa por espaço.
        if (normalizado.contains("\n")) {
            for (String linha : normalizado.split("\n", -1)) {
                if (!linha.isBlank()) {
                    tokens.add(linha.trim());
                }
            }
        } else {
            for (String token : normalizado.trim().split("\\s+")) {
                if (!token.isBlank()) {
                    tokens.add(token);
                }
            }
        }
        return tokens;
    }

    private boolean parecePrompt(String linha) {
        if (linha == null || linha.isBlank()) {
            return false;
        }
        return linha.endsWith(":") || linha.endsWith("?");
    }

    /**
     * Aceita saída exata ou o resultado final impresso (último valor),
     * ignorando prompts/mensagens auxiliares do aluno.
     */
    private boolean saidaCorresponde(String obtido, String esperado) {
        String o = normalizar(obtido);
        String e = normalizar(esperado);
        if (o.equals(e)) {
            return true;
        }
        if (e.isEmpty()) {
            return o.isEmpty();
        }
        return extrairResultadoFinal(o).equals(e);
    }

    /** Último token útil da última linha não vazia (ex.: "Produto: 12" → "12"). */
    private String extrairResultadoFinal(String saida) {
        if (saida == null || saida.isBlank()) {
            return "";
        }
        String[] linhas = saida.replace("\r\n", "\n").split("\n");
        for (int i = linhas.length - 1; i >= 0; i--) {
            String linha = linhas[i].trim();
            if (linha.isEmpty()) {
                continue;
            }
            String[] tokens = linha.split("[\\s:=]+");
            for (int j = tokens.length - 1; j >= 0; j--) {
                String token = tokens[j].trim();
                if (!token.isEmpty()) {
                    return token;
                }
            }
        }
        return saida.trim();
    }
}
