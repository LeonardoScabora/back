package ReiDoCodigo.back.Config;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

/**
 * Garante colunas novas em bancos já existentes.
 * O Hibernate ddl-auto=update nem sempre altera tabelas antigas de forma confiável.
 */
@Slf4j
@Component
@Order(1)
@RequiredArgsConstructor
public class SchemaMigrator implements CommandLineRunner {

    private final JdbcTemplate jdbcTemplate;

    @Override
    public void run(String... args) {
        garantirColuna("perguntas", "linguagem", "VARCHAR(20)");
        garantirColuna("perguntas", "nivel", "VARCHAR(20)");
        garantirColuna("usuarios", "nivel", "VARCHAR(20)");
        garantirColuna("batalhas", "pergunta_atual_id", "BIGINT");
        garantirColuna("batalhas", "ultima_pergunta_id", "BIGINT");
        garantirColuna("batalhas", "desafio_atual_id", "BIGINT");

        // Usuários antigos sem nível recebem INICIANTE por padrão.
        jdbcTemplate.update("UPDATE usuarios SET nivel = 'INICIANTE' WHERE nivel IS NULL");

        tornarInimigoIdOpcionalEmPerguntas();

        jdbcTemplate.execute("""
                CREATE INDEX IF NOT EXISTS idx_perguntas_linguagem_nivel
                ON perguntas (linguagem, nivel)
                """);

        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS usuario_perguntas_usadas (
                    usuario_id BIGINT NOT NULL,
                    pergunta_id BIGINT NOT NULL,
                    PRIMARY KEY (usuario_id, pergunta_id)
                )
                """);
        jdbcTemplate.execute("""
                CREATE INDEX IF NOT EXISTS idx_usuario_perguntas_usadas_usuario
                ON usuario_perguntas_usadas (usuario_id)
                """);

        log.info("Schema migrado: colunas de linguagem/nível/batalha verificadas.");
    }

    private void garantirColuna(String tabela, String coluna, String tipoSql) {
        Integer existe = jdbcTemplate.queryForObject("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = ?
                  AND column_name = ?
                """, Integer.class, tabela, coluna);

        if (existe != null && existe > 0) {
            return;
        }

        jdbcTemplate.execute("ALTER TABLE " + tabela + " ADD COLUMN " + coluna + " " + tipoSql);
        log.info("Coluna adicionada: {}.{}", tabela, coluna);
    }

    private void tornarInimigoIdOpcionalEmPerguntas() {
        try {
            jdbcTemplate.execute("ALTER TABLE perguntas ALTER COLUMN inimigo_id DROP NOT NULL");
        } catch (Exception ignored) {
            // Já é nullable ou tabela ainda não existe.
        }
    }
}
