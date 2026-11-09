package ReiDoCodigo.back.Config;

import ReiDoCodigo.back.Model.Enum.Linguagem;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

@Component
public class PerguntaSeedLoader {

    /** 20 perguntas por nível (iniciante, intermediário, avançado) em cada linguagem. */
    public static final int PERGUNTAS_POR_NIVEL = 20;
    /** Incremente ao regenerar o banco para forçar reseed. */
    public static final int SEED_REVISION = 6;

    private final ObjectMapper objectMapper = new ObjectMapper();

    public List<SeedPergunta> carregar(Linguagem linguagem) {
        String arquivo = switch (linguagem) {
            case JAVA -> "seed/perguntas-java.json";
            case PYTHON -> "seed/perguntas-python.json";
            case CPP -> "seed/perguntas-cpp.json";
        };

        try (InputStream in = new ClassPathResource(arquivo).getInputStream()) {
            List<Map<String, Object>> raw = objectMapper.readValue(in, new TypeReference<>() {});
            List<SeedPergunta> perguntas = new ArrayList<>(raw.size());
            for (Map<String, Object> item : raw) {
                perguntas.add(new SeedPergunta(
                        linguagem,
                        ((Number) item.get("dificuldade")).intValue(),
                        String.valueOf(item.get("enunciado")),
                        String.valueOf(item.get("alternativaA")),
                        String.valueOf(item.get("alternativaB")),
                        String.valueOf(item.get("alternativaC")),
                        String.valueOf(item.get("alternativaD")),
                        String.valueOf(item.get("respostaCorreta"))
                ));
            }
            if (perguntas.isEmpty()) {
                throw new IllegalStateException("Arquivo " + arquivo + " não contém perguntas.");
            }
            validarBancoReformulado(arquivo, perguntas);
            return List.copyOf(perguntas);
        } catch (IllegalStateException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("Falha ao carregar perguntas de " + linguagem + ": " + e.getMessage(), e);
        }
    }

    private void validarBancoReformulado(String arquivo, List<SeedPergunta> perguntas) {
        int n1 = 0, n2 = 0, n3 = 0;
        Set<String> enunciados = new HashSet<>();
        for (SeedPergunta p : perguntas) {
            switch (p.dificuldade()) {
                case 1 -> n1++;
                case 2 -> n2++;
                case 3 -> n3++;
                default -> throw new IllegalStateException(
                        arquivo + ": dificuldade inválida (" + p.dificuldade() + ") em: " + p.enunciado());
            }
            if (!enunciados.add(p.enunciado().strip().toLowerCase(Locale.ROOT))) {
                throw new IllegalStateException(arquivo + ": enunciado duplicado: " + p.enunciado());
            }
            validarAlternativas(arquivo, p);
        }
        if (n1 != PERGUNTAS_POR_NIVEL || n2 != PERGUNTAS_POR_NIVEL || n3 != PERGUNTAS_POR_NIVEL) {
            throw new IllegalStateException(
                    arquivo + " deve ter exatamente " + PERGUNTAS_POR_NIVEL
                            + " perguntas por nível (iniciante/intermediário/avançado); veio "
                            + n1 + "/" + n2 + "/" + n3);
        }
    }

    private void validarAlternativas(String arquivo, SeedPergunta p) {
        String resposta = p.respostaCorreta() == null ? "" : p.respostaCorreta().strip().toUpperCase(Locale.ROOT);
        if (!Set.of("A", "B", "C", "D").contains(resposta)) {
            throw new IllegalStateException(arquivo + ": respostaCorreta inválida em: " + p.enunciado());
        }
        List<String> alts = List.of(p.alternativaA(), p.alternativaB(), p.alternativaC(), p.alternativaD());
        Set<String> unicas = new HashSet<>();
        for (String alt : alts) {
            if (alt == null || alt.isBlank()) {
                throw new IllegalStateException(arquivo + ": alternativa vazia em: " + p.enunciado());
            }
            if (!unicas.add(alt.strip().toLowerCase(Locale.ROOT))) {
                throw new IllegalStateException(arquivo + ": alternativas duplicadas em: " + p.enunciado());
            }
        }
    }
}
