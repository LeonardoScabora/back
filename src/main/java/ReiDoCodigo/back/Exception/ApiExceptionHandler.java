package ReiDoCodigo.back.Exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.LocalDateTime;
import java.util.Map;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(RecursoNaoEncontradoException.class)
    public ResponseEntity<Map<String, Object>> handleNotFound(RecursoNaoEncontradoException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(erro(HttpStatus.NOT_FOUND, ex.getMessage()));
    }

    @ExceptionHandler(RegraNegocioException.class)
    public ResponseEntity<Map<String, Object>> handleBusiness(RegraNegocioException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(erro(HttpStatus.BAD_REQUEST, ex.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGeneric(Exception ex) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(erro(HttpStatus.INTERNAL_SERVER_ERROR, ex.getMessage()));
    }

    private Map<String, Object> erro(HttpStatus status, String mensagem) {
        return Map.of(
                "status", status.value(),
                "erro", status.getReasonPhrase(),
                "mensagem", mensagem == null ? "Erro interno" : mensagem,
                "timestamp", LocalDateTime.now().toString()
        );
    }
}
