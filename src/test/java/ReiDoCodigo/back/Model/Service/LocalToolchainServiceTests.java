package ReiDoCodigo.back.Model.Service;

import ReiDoCodigo.back.Model.Dto.ExecucaoCodigoResultado;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import org.junit.jupiter.api.Test;

import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

class LocalToolchainServiceTests {

    @Test
    void devePriorizarCompiladorConfiguradoQuandoComandoForValido() {
        String executavelJava = Path.of(
                System.getProperty("java.home"),
                "bin",
                isWindows() ? "java.exe" : "java"
        ).toString();

        LocalToolchainService service = new LocalToolchainService(executavelJava);

        assertEquals(executavelJava, service.encontrarCppCompiler().orElseThrow());
    }

    @Test
    void deveCompilarEExecutarCppQuandoToolchainEstiverDisponivel() {
        LocalToolchainService toolchain = new LocalToolchainService("");
        assumeTrue(toolchain.encontrarCppCompiler().isPresent());
        CodeExecutionService executor = new CodeExecutionService(
                false,
                "http://localhost:2358",
                10,
                toolchain
        );

        ExecucaoCodigoResultado resultado = executor.executar(
                Linguagem.CPP,
                "#include <iostream>\nint main() { std::cout << \"OK\"; }",
                ""
        );

        assertTrue(resultado.isSucesso(), resultado.getStderr());
        assertEquals("OK", resultado.getStdout());
    }

    private boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }
}
