package ReiDoCodigo.back.Model.Service;

import ReiDoCodigo.back.Exception.RecursoNaoEncontradoException;
import ReiDoCodigo.back.Exception.RegraNegocioException;
import ReiDoCodigo.back.Model.Dto.ExecucaoCodigoResultado;
import ReiDoCodigo.back.Model.Dto.TerminalSessaoResponse;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import jakarta.annotation.PreDestroy;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;

/**
 * Mantém processos vivos para o terminal interativo (print aparece antes do input).
 * Funciona no executor local; Judge0 não suporta stdin passo a passo.
 */
@Service
public class InteractiveTerminalService {

    private static final long DRAIN_QUIET_MS = 180;
    private static final long DRAIN_MAX_MS = 2500;
    private static final long SESSION_TTL_MS = 120_000;

    private final boolean judge0Enabled;
    private final long timeoutSeconds;
    private final LocalToolchainService localToolchainService;
    private final Map<String, Sessao> sessoes = new ConcurrentHashMap<>();

    public InteractiveTerminalService(
            @Value("${app.judge0.enabled:false}") boolean judge0Enabled,
            @Value("${app.code.timeout-seconds:5}") long timeoutSeconds,
            LocalToolchainService localToolchainService
    ) {
        this.judge0Enabled = judge0Enabled;
        this.timeoutSeconds = timeoutSeconds;
        this.localToolchainService = localToolchainService;
    }

    public TerminalSessaoResponse iniciar(Long batalhaId, Linguagem linguagem, String codigo) {
        limparExpiradas();

        if (judge0Enabled) {
            throw new RegraNegocioException(
                    "Terminal interativo exige executor local (app.judge0.enabled=false)."
            );
        }
        if (codigo == null || codigo.isBlank()) {
            throw new RegraNegocioException("O código é obrigatório.");
        }

        Path tempDir = null;
        try {
            tempDir = Files.createTempDirectory("reidocodigo-term-");
            PreparedProcess prepared = preparar(linguagem, tempDir, codigo);
            if (prepared.compileError() != null) {
                limparDiretorio(tempDir);
                return TerminalSessaoResponse.builder()
                        .sessionId(null)
                        .stdout(prepared.compileError().getStdout())
                        .stderr(prepared.compileError().getStderr())
                        .aguardandoEntrada(false)
                        .finalizado(true)
                        .sucesso(false)
                        .mensagem(prepared.compileError().getMensagem())
                        .build();
            }

            ProcessBuilder pb = new ProcessBuilder(prepared.command());
            pb.directory(tempDir.toFile());
            pb.redirectErrorStream(false);
            pb.environment().put("PYTHONUNBUFFERED", "1");
            Process process = pb.start();

            String sessionId = UUID.randomUUID().toString();
            Sessao sessao = new Sessao(sessionId, batalhaId, process, tempDir, process.getOutputStream());
            sessoes.put(sessionId, sessao);

            DrainResult drain = drenar(process);
            return montarResposta(sessao, drain, true);
        } catch (IOException e) {
            if (tempDir != null) {
                limparDiretorio(tempDir);
            }
            throw new RegraNegocioException(
                    "Falha ao iniciar o terminal. Verifique se o interpretador/compilador está instalado."
            );
        }
    }

    public TerminalSessaoResponse enviarLinha(String sessionId, Long batalhaId, String linha) {
        Sessao sessao = obterSessao(sessionId, batalhaId);
        if (!sessao.process.isAlive()) {
            DrainResult drain = drenar(sessao.process);
            return finalizar(sessao, drain);
        }

        try {
            String payload = (linha == null ? "" : linha) + "\n";
            sessao.stdin.write(payload.getBytes(StandardCharsets.UTF_8));
            sessao.stdin.flush();
        } catch (IOException e) {
            return encerrarComErro(sessao, "Não foi possível enviar a entrada ao programa.");
        }

        DrainResult drain = drenar(sessao.process);
        if (!sessao.process.isAlive()) {
            return finalizar(sessao, drain);
        }
        return montarResposta(sessao, drain, false);
    }

    public void encerrar(String sessionId, Long batalhaId) {
        Sessao sessao = sessoes.remove(sessionId);
        if (sessao == null) {
            return;
        }
        if (!sessao.batalhaId.equals(batalhaId)) {
            sessoes.put(sessionId, sessao);
            throw new RegraNegocioException("Sessão não pertence a esta batalha.");
        }
        destruir(sessao);
    }

    @PreDestroy
    public void shutdown() {
        sessoes.keySet().forEach(id -> {
            Sessao s = sessoes.remove(id);
            if (s != null) {
                destruir(s);
            }
        });
    }

    private TerminalSessaoResponse montarResposta(Sessao sessao, DrainResult drain, boolean inicio) {
        boolean vivo = sessao.process.isAlive();
        if (!vivo) {
            return finalizar(sessao, drain);
        }

        // Timeout absoluto da sessão
        if (System.currentTimeMillis() - sessao.criadaEm > timeoutSeconds * 1000L * 4) {
            return encerrarComErro(sessao, "Tempo limite da sessão do terminal excedido.");
        }

        return TerminalSessaoResponse.builder()
                .sessionId(sessao.id)
                .stdout(drain.stdout())
                .stderr(drain.stderr())
                .aguardandoEntrada(true)
                .finalizado(false)
                .sucesso(true)
                .mensagem(inicio
                        ? "Programa em execução. Digite a entrada e pressione Enter."
                        : null)
                .build();
    }

    private TerminalSessaoResponse finalizar(Sessao sessao, DrainResult drain) {
        sessoes.remove(sessao.id);
        int exit = -1;
        try {
            exit = sessao.process.exitValue();
        } catch (IllegalThreadStateException ignored) {
            sessao.process.destroyForcibly();
        }
        destruir(sessao);
        boolean ok = exit == 0;
        return TerminalSessaoResponse.builder()
                .sessionId(null)
                .stdout(drain.stdout())
                .stderr(drain.stderr())
                .aguardandoEntrada(false)
                .finalizado(true)
                .sucesso(ok)
                .mensagem(ok
                        ? "Execução concluída. Use Submeter para validar nos testes oficiais."
                        : "Programa finalizou com erro.")
                .build();
    }

    private TerminalSessaoResponse encerrarComErro(Sessao sessao, String mensagem) {
        sessoes.remove(sessao.id);
        DrainResult drain = drenar(sessao.process);
        destruir(sessao);
        return TerminalSessaoResponse.builder()
                .sessionId(null)
                .stdout(drain.stdout())
                .stderr(drain.stderr().isBlank() ? mensagem : drain.stderr())
                .aguardandoEntrada(false)
                .finalizado(true)
                .sucesso(false)
                .mensagem(mensagem)
                .build();
    }

    private Sessao obterSessao(String sessionId, Long batalhaId) {
        limparExpiradas();
        if (sessionId == null || sessionId.isBlank()) {
            throw new RegraNegocioException("Sessão do terminal inválida.");
        }
        Sessao sessao = sessoes.get(sessionId);
        if (sessao == null) {
            throw new RecursoNaoEncontradoException("Sessão do terminal não encontrada ou já encerrada.");
        }
        if (!sessao.batalhaId.equals(batalhaId)) {
            throw new RegraNegocioException("Sessão não pertence a esta batalha.");
        }
        return sessao;
    }

    private void limparExpiradas() {
        long agora = System.currentTimeMillis();
        for (Map.Entry<String, Sessao> entry : sessoes.entrySet()) {
            if (agora - entry.getValue().criadaEm > SESSION_TTL_MS) {
                Sessao antiga = sessoes.remove(entry.getKey());
                if (antiga != null) {
                    destruir(antiga);
                }
            }
        }
    }

    private void destruir(Sessao sessao) {
        try {
            sessao.stdin.close();
        } catch (Exception ignored) {
            // best effort
        }
        if (sessao.process.isAlive()) {
            sessao.process.destroyForcibly();
            try {
                sessao.process.waitFor(1, TimeUnit.SECONDS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        limparDiretorio(sessao.tempDir);
    }

    private DrainResult drenar(Process process) {
        try {
            String stdout = lerDisponivel(process.getInputStream());
            String stderr = lerDisponivel(process.getErrorStream());
            // Se o processo morreu, esvazia o que restou.
            if (!process.isAlive()) {
                stdout += new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
                stderr += new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8);
            }
            return new DrainResult(stdout, stderr);
        } catch (IOException e) {
            return new DrainResult("", e.getMessage() == null ? "" : e.getMessage());
        }
    }

    private String lerDisponivel(InputStream in) throws IOException {
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        long inicio = System.currentTimeMillis();
        long ultimoDado = inicio;
        byte[] chunk = new byte[1024];

        while (System.currentTimeMillis() - inicio < DRAIN_MAX_MS) {
            int available = in.available();
            if (available > 0) {
                int lidos = in.read(chunk, 0, Math.min(chunk.length, available));
                if (lidos > 0) {
                    buf.write(chunk, 0, lidos);
                    ultimoDado = System.currentTimeMillis();
                    continue;
                }
            }

            long quieto = System.currentTimeMillis() - ultimoDado;
            if (quieto >= DRAIN_QUIET_MS) {
                break;
            }
            try {
                Thread.sleep(15);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        return buf.toString(StandardCharsets.UTF_8);
    }

    private PreparedProcess preparar(Linguagem linguagem, Path tempDir, String codigo) throws IOException {
        return switch (linguagem) {
            case PYTHON -> prepararPython(tempDir, codigo);
            case JAVA -> prepararJava(tempDir, codigo);
            case CPP -> prepararCpp(tempDir, codigo);
        };
    }

    private PreparedProcess prepararPython(Path tempDir, String codigo) throws IOException {
        Path script = tempDir.resolve("main.py");
        Files.writeString(script, codigo, StandardCharsets.UTF_8);
        String launcher = resolverPythonLauncher();
        return new PreparedProcess(List.of(launcher, "-u", script.toString()), null);
    }

    private String resolverPythonLauncher() {
        if (comandoVersaoOk("python")) {
            return "python";
        }
        if (comandoVersaoOk("py")) {
            return "py";
        }
        return "python";
    }

    private boolean comandoVersaoOk(String comando) {
        try {
            Process p = new ProcessBuilder(comando, "--version").start();
            boolean ok = p.waitFor(2, TimeUnit.SECONDS);
            return ok && p.exitValue() == 0;
        } catch (Exception e) {
            return false;
        }
    }

    private PreparedProcess prepararJava(Path tempDir, String codigo) throws IOException {
        Path source = tempDir.resolve("Main.java");
        Files.writeString(source, codigo, StandardCharsets.UTF_8);
        ExecucaoCodigoResultado compile = runSync(tempDir, List.of("javac", "Main.java"));
        if (!compile.isSucesso()) {
            return new PreparedProcess(List.of(), compile);
        }
        return new PreparedProcess(List.of("java", "-cp", tempDir.toString(), "Main"), null);
    }

    private PreparedProcess prepararCpp(Path tempDir, String codigo) throws IOException {
        Path source = tempDir.resolve("main.cpp");
        Files.writeString(source, codigo, StandardCharsets.UTF_8);
        String binName = isWindows() ? "main.exe" : "main";
        String compiler = localToolchainService.encontrarCppCompiler().orElse(null);
        if (compiler == null) {
            ExecucaoCodigoResultado erro = ExecucaoCodigoResultado.builder()
                    .sucesso(false)
                    .erroInfraestrutura(true)
                    .stderr("Nenhum compilador C++ compatível foi localizado no servidor.")
                    .mensagem(
                            "Compilador C++ indisponível. Instale o g++/clang++ ou configure "
                                    + "app.code.cpp-compiler."
                    )
                    .build();
            return new PreparedProcess(List.of(), erro);
        }
        ExecucaoCodigoResultado compile = runSync(
                tempDir,
                List.of(compiler, "main.cpp", "-o", binName)
        );
        if (!compile.isSucesso()) {
            return new PreparedProcess(List.of(), compile);
        }
        Path binary = tempDir.resolve(binName);
        return new PreparedProcess(List.of(binary.toString()), null);
    }

    private ExecucaoCodigoResultado runSync(Path workDir, List<String> command) {
        try {
            ProcessBuilder pb = new ProcessBuilder(command);
            pb.directory(workDir.toFile());
            Process process = pb.start();
            boolean finished = process.waitFor(timeoutSeconds, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                return ExecucaoCodigoResultado.builder()
                        .sucesso(false)
                        .stderr("Tempo limite excedido na compilação.")
                        .mensagem("Timeout na compilação.")
                        .build();
            }
            String stdout = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            String stderr = new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8);
            boolean ok = process.exitValue() == 0;
            return ExecucaoCodigoResultado.builder()
                    .sucesso(ok)
                    .stdout(stdout)
                    .stderr(stderr)
                    .mensagem(ok ? "OK" : "Erro de compilação.")
                    .build();
        } catch (Exception e) {
            return ExecucaoCodigoResultado.builder()
                    .sucesso(false)
                    .stderr(e.getMessage())
                    .mensagem("Falha ao compilar.")
                    .build();
        }
    }

    private void limparDiretorio(Path dir) {
        if (dir == null) {
            return;
        }
        try (Stream<Path> walk = Files.walk(dir)) {
            walk.sorted(Comparator.reverseOrder()).forEach(path -> {
                try {
                    Files.deleteIfExists(path);
                } catch (IOException ignored) {
                    // best effort
                }
            });
        } catch (IOException ignored) {
            // best effort
        }
    }

    private boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }

    private record PreparedProcess(List<String> command, ExecucaoCodigoResultado compileError) {}

    private record DrainResult(String stdout, String stderr) {}

    private static final class Sessao {
        private final String id;
        private final Long batalhaId;
        private final Process process;
        private final Path tempDir;
        private final OutputStream stdin;
        private final long criadaEm = System.currentTimeMillis();

        private Sessao(String id, Long batalhaId, Process process, Path tempDir, OutputStream stdin) {
            this.id = id;
            this.batalhaId = batalhaId;
            this.process = process;
            this.tempDir = tempDir;
            this.stdin = stdin;
        }
    }
}
