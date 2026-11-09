package ReiDoCodigo.back.Model.Service;

import ReiDoCodigo.back.Model.Dto.ExecucaoCodigoResultado;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Exception.RegraNegocioException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;

/**
 * Executa código do aluno.
 * - judge0.enabled=true → usa API Judge0
 * - caso contrário → executor local com timeout (útil no desenvolvimento do TCC)
 */
@Service
public class CodeExecutionService {

    private final RestClient restClient;
    private final boolean judge0Enabled;
    private final String judge0Url;
    private final long timeoutSeconds;
    private final LocalToolchainService localToolchainService;

    public CodeExecutionService(
            @Value("${app.judge0.enabled:false}") boolean judge0Enabled,
            @Value("${app.judge0.url:http://localhost:2358}") String judge0Url,
            @Value("${app.code.timeout-seconds:5}") long timeoutSeconds,
            LocalToolchainService localToolchainService
    ) {
        this.restClient = RestClient.create();
        this.judge0Enabled = judge0Enabled;
        this.judge0Url = judge0Url.endsWith("/") ? judge0Url.substring(0, judge0Url.length() - 1) : judge0Url;
        this.timeoutSeconds = timeoutSeconds;
        this.localToolchainService = localToolchainService;
    }

    public ExecucaoCodigoResultado executar(Linguagem linguagem, String codigo, String stdin) {
        if (codigo == null || codigo.isBlank()) {
            throw new RegraNegocioException("O código não pode estar vazio.");
        }
        if (judge0Enabled) {
            return executarJudge0(linguagem, codigo, stdin == null ? "" : stdin);
        }
        return executarLocal(linguagem, codigo, stdin == null ? "" : stdin);
    }

    private ExecucaoCodigoResultado executarJudge0(Linguagem linguagem, String codigo, String stdin) {
        Map<String, Object> body = Map.of(
                "source_code", codigo,
                "language_id", languageId(linguagem),
                "stdin", stdin
        );

        @SuppressWarnings("unchecked")
        Map<String, Object> submission = restClient.post()
                .uri(judge0Url + "/submissions?base64_encoded=false&wait=true")
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .body(Map.class);

        if (submission == null) {
            return ExecucaoCodigoResultado.builder()
                    .sucesso(false)
                    .stderr("Judge0 não retornou resposta.")
                    .mensagem("Falha ao executar no Judge0.")
                    .build();
        }

        String stdout = stringOrEmpty(submission.get("stdout"));
        String stderr = stringOrEmpty(submission.get("stderr"));
        String compileOutput = stringOrEmpty(submission.get("compile_output"));
        String message = stringOrEmpty(submission.get("message"));

        boolean ok = compileOutput.isBlank() && stderr.isBlank() && message.isBlank();
        String erro = Stream.of(compileOutput, stderr, message)
                .filter(s -> !s.isBlank())
                .findFirst()
                .orElse("");

        return ExecucaoCodigoResultado.builder()
                .sucesso(ok)
                .stdout(stdout)
                .stderr(erro)
                .mensagem(ok ? "Execução concluída." : "Erro na execução.")
                .build();
    }

    private ExecucaoCodigoResultado executarLocal(Linguagem linguagem, String codigo, String stdin) {
        Path tempDir = null;
        try {
            tempDir = Files.createTempDirectory("reidocodigo-");
            return switch (linguagem) {
                case PYTHON -> executarPythonLocal(tempDir, codigo, stdin);
                case JAVA -> executarJavaLocal(tempDir, codigo, stdin);
                case CPP -> executarCppLocal(tempDir, codigo, stdin);
            };
        } catch (IOException e) {
            return ExecucaoCodigoResultado.builder()
                    .sucesso(false)
                    .stderr(e.getMessage())
                    .mensagem("Falha ao preparar execução local.")
                    .build();
        } finally {
            if (tempDir != null) {
                limparDiretorio(tempDir);
            }
        }
    }

    private ExecucaoCodigoResultado executarPythonLocal(Path tempDir, String codigo, String stdin) throws IOException {
        Path script = writeFile(tempDir, "main.py", codigo);
        ExecucaoCodigoResultado comPython = runProcess(tempDir, List.of("python", script.toString()), stdin);
        if (comandoNaoEncontrado(comPython)) {
            return runProcess(tempDir, List.of("py", script.toString()), stdin);
        }
        return comPython;
    }

    private boolean comandoNaoEncontrado(ExecucaoCodigoResultado resultado) {
        String stderr = resultado.getStderr() == null ? "" : resultado.getStderr().toLowerCase();
        String mensagem = resultado.getMensagem() == null ? "" : resultado.getMensagem().toLowerCase();
        return stderr.contains("createprocess")
                || stderr.contains("cannot run program")
                || mensagem.contains("falha ao executar processo");
    }

    private ExecucaoCodigoResultado executarJavaLocal(Path tempDir, String codigo, String stdin) throws IOException {
        Path source = writeFile(tempDir, "Main.java", codigo);
        ExecucaoCodigoResultado compile = runProcess(tempDir, List.of("javac", source.getFileName().toString()), "");
        if (!compile.isSucesso()) {
            return ExecucaoCodigoResultado.builder()
                    .sucesso(false)
                    .stdout(compile.getStdout())
                    .stderr(compile.getStderr())
                    .mensagem("Erro de compilação Java.")
                    .build();
        }
        return runProcess(tempDir, List.of("java", "-cp", tempDir.toString(), "Main"), stdin);
    }

    private ExecucaoCodigoResultado executarCppLocal(Path tempDir, String codigo, String stdin) throws IOException {
        Path source = writeFile(tempDir, "main.cpp", codigo);
        Path binary = tempDir.resolve(isWindows() ? "main.exe" : "main");
        String compiler = localToolchainService.encontrarCppCompiler().orElse(null);
        if (compiler == null) {
            return falhaCompiladorCppIndisponivel();
        }
        ExecucaoCodigoResultado compile = runProcess(
                tempDir,
                List.of(compiler, source.getFileName().toString(), "-o", binary.getFileName().toString()),
                ""
        );
        if (!compile.isSucesso()) {
            return ExecucaoCodigoResultado.builder()
                    .sucesso(false)
                    .erroInfraestrutura(compile.isErroInfraestrutura())
                    .stdout(compile.getStdout())
                    .stderr(compile.getStderr())
                    .mensagem(compile.isErroInfraestrutura()
                            ? compile.getMensagem()
                            : "Erro de compilação C++.")
                    .build();
        }
        return runProcess(tempDir, List.of(binary.toString()), stdin);
    }

    private ExecucaoCodigoResultado falhaCompiladorCppIndisponivel() {
        return ExecucaoCodigoResultado.builder()
                .sucesso(false)
                .erroInfraestrutura(true)
                .stderr("Nenhum compilador C++ compatível foi localizado no servidor.")
                .mensagem(
                        "Compilador C++ indisponível. Instale o g++/clang++ ou configure "
                                + "app.code.cpp-compiler. Nenhuma vida foi perdida."
                )
                .build();
    }

    private ExecucaoCodigoResultado runProcess(Path workDir, List<String> command, String stdin) {
        try {
            ProcessBuilder pb = new ProcessBuilder(command);
            pb.directory(workDir.toFile());
            pb.redirectErrorStream(false);
            Process process = pb.start();

            if (stdin != null && !stdin.isEmpty()) {
                process.getOutputStream().write(stdin.getBytes(StandardCharsets.UTF_8));
            }
            process.getOutputStream().close();

            boolean finished = process.waitFor(timeoutSeconds, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                return ExecucaoCodigoResultado.builder()
                        .sucesso(false)
                        .stderr("Tempo limite excedido.")
                        .mensagem("Timeout na execução.")
                        .build();
            }

            String stdout = readStream(process.getInputStream());
            String stderr = readStream(process.getErrorStream());
            boolean ok = process.exitValue() == 0;

            return ExecucaoCodigoResultado.builder()
                    .sucesso(ok)
                    .stdout(stdout)
                    .stderr(stderr)
                    .mensagem(ok ? "Execução concluída." : "Processo finalizou com erro.")
                    .build();
        } catch (IOException e) {
            return ExecucaoCodigoResultado.builder()
                    .sucesso(false)
                    .erroInfraestrutura(true)
                    .stderr(e.getMessage())
                    .mensagem("Falha ao iniciar o processo de execução no servidor.")
                    .build();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return ExecucaoCodigoResultado.builder()
                    .sucesso(false)
                    .stderr(e.getMessage())
                    .mensagem("Falha ao executar processo. Verifique se o interpretador/compilador está instalado.")
                    .build();
        }
    }

    private Path writeFile(Path dir, String name, String content) throws IOException {
        Path file = dir.resolve(name);
        Files.writeString(file, content, StandardCharsets.UTF_8);
        return file;
    }

    private String readStream(InputStream stream) throws IOException {
        return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
    }

    private void limparDiretorio(Path dir) {
        try (Stream<Path> walk = Files.walk(dir)) {
            walk.sorted(Comparator.reverseOrder()).forEach(path -> {
                try {
                    Files.deleteIfExists(path);
                } catch (IOException ignored) {
                    // best effort cleanup
                }
            });
        } catch (IOException ignored) {
            // best effort cleanup
        }
    }

    private int languageId(Linguagem linguagem) {
        return switch (linguagem) {
            case PYTHON -> 71;
            case JAVA -> 62;
            case CPP -> 54;
        };
    }

    private String stringOrEmpty(Object value) {
        return value == null ? "" : value.toString();
    }

    private boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }
}
