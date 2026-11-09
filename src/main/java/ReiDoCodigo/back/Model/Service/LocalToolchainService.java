package ReiDoCodigo.back.Model.Service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;

/**
 * Localiza ferramentas usadas pelo executor local sem depender apenas do PATH
 * herdado pela JVM.
 */
@Service
public class LocalToolchainService {

    private final String cppCompilerConfigurado;
    private volatile boolean cppCompilerResolvido;
    private volatile String cppCompiler;

    public LocalToolchainService(
            @Value("${app.code.cpp-compiler:}") String cppCompilerConfigurado
    ) {
        this.cppCompilerConfigurado = cppCompilerConfigurado == null
                ? ""
                : cppCompilerConfigurado.trim();
    }

    public Optional<String> encontrarCppCompiler() {
        if (!cppCompilerResolvido) {
            synchronized (this) {
                if (!cppCompilerResolvido) {
                    cppCompiler = localizarCppCompiler();
                    cppCompilerResolvido = true;
                }
            }
        }
        return Optional.ofNullable(cppCompiler);
    }

    private String localizarCppCompiler() {
        List<String> candidatos = new ArrayList<>();
        adicionarSePreenchido(candidatos, cppCompilerConfigurado);
        adicionarSePreenchido(candidatos, System.getenv("CXX"));
        candidatos.add("g++");
        candidatos.add("clang++");

        if (isWindows()) {
            candidatos.add("C:\\msys64\\ucrt64\\bin\\g++.exe");
            candidatos.add("C:\\msys64\\mingw64\\bin\\g++.exe");
            candidatos.add("C:\\mingw64\\bin\\g++.exe");
            adicionarWinLibsDoWinget(candidatos);
        }

        return candidatos.stream()
                .distinct()
                .filter(this::comandoVersaoOk)
                .findFirst()
                .orElse(null);
    }

    private void adicionarWinLibsDoWinget(List<String> candidatos) {
        String localAppData = System.getenv("LOCALAPPDATA");
        if (localAppData == null || localAppData.isBlank()) {
            return;
        }

        Path packages = Path.of(localAppData, "Microsoft", "WinGet", "Packages");
        if (!Files.isDirectory(packages)) {
            return;
        }

        try (Stream<Path> diretorios = Files.list(packages)) {
            diretorios
                    .filter(Files::isDirectory)
                    .filter(path -> path.getFileName().toString()
                            .startsWith("BrechtSanders.WinLibs."))
                    .map(path -> path.resolve("mingw64").resolve("bin").resolve("g++.exe"))
                    .filter(Files::isRegularFile)
                    .map(Path::toString)
                    .forEach(candidatos::add);
        } catch (IOException ignored) {
            // Os demais candidatos ainda podem estar disponíveis.
        }
    }

    private void adicionarSePreenchido(List<String> candidatos, String valor) {
        if (valor != null && !valor.isBlank()) {
            candidatos.add(valor.trim());
        }
    }

    private boolean comandoVersaoOk(String comando) {
        try {
            ProcessBuilder pb = new ProcessBuilder(comando, "--version");
            pb.redirectErrorStream(true);
            pb.redirectOutput(ProcessBuilder.Redirect.DISCARD);
            Process processo = pb.start();
            boolean finalizou = processo.waitFor(3, TimeUnit.SECONDS);
            if (!finalizou) {
                processo.destroyForcibly();
            }
            return finalizou && processo.exitValue() == 0;
        } catch (Exception ignored) {
            return false;
        }
    }

    private boolean isWindows() {
        return File.separatorChar == '\\';
    }
}
