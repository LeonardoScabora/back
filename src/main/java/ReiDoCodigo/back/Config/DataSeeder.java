package ReiDoCodigo.back.Config;

import ReiDoCodigo.back.Model.Entity.*;
import ReiDoCodigo.back.Model.Enum.Linguagem;
import ReiDoCodigo.back.Model.Enum.NivelDificuldade;
import ReiDoCodigo.back.Model.Enum.TipoInimigo;
import ReiDoCodigo.back.Model.Repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Component
@Order(2)
@RequiredArgsConstructor
public class DataSeeder implements CommandLineRunner {

    /** Quantidade de desafios distintos por inimigo de código e linguagem. */
    public static final int DESAFIOS_POR_INIMIGO_LINGUAGEM = 4;

    private final InimigoRepository inimigoRepository;
    private final PerguntasRepository perguntasRepository;
    private final DesafioCodigoRepository desafioCodigoRepository;
    private final CasoTesteRepository casoTesteRepository;
    private final PerguntaSeedLoader perguntaSeedLoader;
    private final JdbcTemplate jdbcTemplate;
    private final PlatformTransactionManager transactionManager;

    @Override
    @Transactional
    public void run(String... args) {
        if (inimigoRepository.count() == 0) {
            seedMundoBase();
        }

        garantirBancoPerguntasPorLinguagem();
        garantirDesafiosDiversos();
        garantirReiDoCodigo();
    }

    private void seedMundoBase() {
        Inimigo goblin = salvarInimigo("Goblin das Variáveis", 1, TipoInimigo.MULTIPLA_ESCOLHA, false,
                "Perguntas da linguagem e do nível escolhidos pelo jogador.");
        Inimigo esqueleto = salvarInimigo("Esqueleto dos Loops", 2, TipoInimigo.CODIGO, false,
                "Desafios de algoritmo sorteados na linguagem escolhida.");
        Inimigo cavaleiro = salvarInimigo("Cavaleiro das Condições", 3, TipoInimigo.MULTIPLA_ESCOLHA, false,
                "Perguntas da linguagem e do nível escolhidos pelo jogador.");
        Inimigo mago = salvarInimigo("Mago dos Vetores", 4, TipoInimigo.CODIGO, false,
                "Desafios de algoritmo sorteados na linguagem escolhida.");
        Inimigo rei = salvarInimigo("Rei do Código", 5, TipoInimigo.MULTIPLA_ESCOLHA, true,
                "Chefe final: 4 perguntas da linguagem e do nível, depois um algoritmo. Vença-o e torne-se o Rei do Código.");

        criarPoolBasico(esqueleto);
        criarPoolIntermediario(mago);
        criarPoolIntermediario(rei);
        log.info("Mundo base criado (inimigos + desafios de código). Goblin id={}", goblin.getId());
    }

    private void garantirDesafiosDiversos() {
        List<Inimigo> inimigosCodigo = inimigoRepository.findAll().stream()
                .filter(i -> i.getTipo() == TipoInimigo.CODIGO)
                .sorted(Comparator.comparing(Inimigo::getOrdemNoCorredor))
                .toList();

        if (inimigosCodigo.isEmpty()) {
            return;
        }

        long esperado = (long) inimigosCodigo.size()
                * Linguagem.values().length
                * DESAFIOS_POR_INIMIGO_LINGUAGEM;

        boolean avisosFeios = desafioCodigoRepository.findAll().stream()
                .anyMatch(d -> d.getEnunciado() != null && d.getEnunciado().contains("Importante:"));

        if (desafioCodigoRepository.count() >= esperado && !avisosFeios) {
            log.info("Banco de desafios OK: {} desafios de código.", desafioCodigoRepository.count());
            return;
        }

        log.info("Recriando pool de desafios de algoritmo (esperado >= {})...", esperado);
        casoTesteRepository.deleteAllInBatch();
        desafioCodigoRepository.deleteAllInBatch();

        for (int i = 0; i < inimigosCodigo.size(); i++) {
            if (i % 2 == 0) {
                criarPoolBasico(inimigosCodigo.get(i));
            } else {
                criarPoolIntermediario(inimigosCodigo.get(i));
            }
        }
        log.info("Desafios de algoritmo recriados: {}", desafioCodigoRepository.count());
    }

    private void garantirBancoPerguntasPorLinguagem() {
        Map<Linguagem, List<SeedPergunta>> seeds = new EnumMap<>(Linguagem.class);
        for (Linguagem linguagem : Linguagem.values()) {
            seeds.put(linguagem, perguntaSeedLoader.carregar(linguagem));
        }

        // Banco vazio: reseed direto (evita SQL de checagem em tabela recém-criada).
        boolean precisaReseed = perguntasRepository.count() == 0;
        if (!precisaReseed) {
            precisaReseed = possuiPerguntasInvalidas();
        }
        for (Linguagem linguagem : Linguagem.values()) {
            if (precisaReseed) {
                break;
            }
            List<SeedPergunta> seed = seeds.get(linguagem);
            if (perguntasRepository.countByLinguagem(linguagem) != seed.size()) {
                precisaReseed = true;
                break;
            }
            Map<NivelDificuldade, Integer> esperado = contarPorNivel(seed);
            for (Map.Entry<NivelDificuldade, Integer> entry : esperado.entrySet()) {
                long porNivel = perguntasRepository.countByLinguagemAndNivel(linguagem, entry.getKey());
                if (porNivel != entry.getValue()) {
                    precisaReseed = true;
                    break;
                }
            }
        }

        if (!precisaReseed) {
            log.info("Banco de perguntas OK: {}", resumoSeeds(seeds));
            return;
        }

        log.info("Recriando banco de perguntas {}...", resumoSeeds(seeds));
        perguntasRepository.deleteAllInBatch();

        Map<Linguagem, Integer> contadores = new EnumMap<>(Linguagem.class);
        for (Linguagem linguagem : Linguagem.values()) {
            List<SeedPergunta> seed = seeds.get(linguagem);
            List<Perguntas> lote = new ArrayList<>(seed.size());
            Map<NivelDificuldade, Integer> ordemPorNivel = new EnumMap<>(NivelDificuldade.class);
            Map<NivelDificuldade, Integer> porNivel = new EnumMap<>(NivelDificuldade.class);

            for (SeedPergunta sp : seed) {
                NivelDificuldade nivel = NivelDificuldade.fromCodigo(sp.dificuldade());
                int ordem = ordemPorNivel.merge(nivel, 1, Integer::sum);
                porNivel.merge(nivel, 1, Integer::sum);

                lote.add(Perguntas.builder()
                        .inimigo(null)
                        .linguagem(linguagem)
                        .nivel(nivel)
                        .ordem(ordem)
                        .enunciado(sp.enunciado())
                        .alternativaA(sp.alternativaA())
                        .alternativaB(sp.alternativaB())
                        .alternativaC(sp.alternativaC())
                        .alternativaD(sp.alternativaD())
                        .respostaCorreta(sp.respostaCorreta())
                        .build());
            }

            for (NivelDificuldade nivel : NivelDificuldade.values()) {
                if (porNivel.getOrDefault(nivel, 0) == 0) {
                    throw new IllegalStateException(
                            "Seed inválido para " + linguagem + ": nenhuma pergunta de " + nivel + ". Distribuição: " + porNivel
                    );
                }
            }

            perguntasRepository.saveAll(lote);
            contadores.put(linguagem, lote.size());
        }

        log.info("Perguntas inseridas por linguagem: {}", contadores);
    }

    private static Map<NivelDificuldade, Integer> contarPorNivel(List<SeedPergunta> seed) {
        Map<NivelDificuldade, Integer> porNivel = new EnumMap<>(NivelDificuldade.class);
        for (SeedPergunta sp : seed) {
            porNivel.merge(NivelDificuldade.fromCodigo(sp.dificuldade()), 1, Integer::sum);
        }
        return porNivel;
    }

    private static Map<Linguagem, String> resumoSeeds(Map<Linguagem, List<SeedPergunta>> seeds) {
        Map<Linguagem, String> resumo = new EnumMap<>(Linguagem.class);
        for (Map.Entry<Linguagem, List<SeedPergunta>> entry : seeds.entrySet()) {
            Map<NivelDificuldade, Integer> porNivel = contarPorNivel(entry.getValue());
            resumo.put(entry.getKey(), entry.getValue().size() + " ("
                    + porNivel.getOrDefault(NivelDificuldade.INICIANTE, 0) + "/"
                    + porNivel.getOrDefault(NivelDificuldade.INTERMEDIARIO, 0) + "/"
                    + porNivel.getOrDefault(NivelDificuldade.AVANCADO, 0) + ")");
        }
        return resumo;
    }

    /**
     * Roda em transação NOVA para não abortar o seed se o SQL de checagem falhar.
     */
    private boolean possuiPerguntasInvalidas() {
        TransactionTemplate tx = new TransactionTemplate(transactionManager);
        tx.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRES_NEW);
        try {
            return Boolean.TRUE.equals(tx.execute(status -> {
                try {
                    Boolean existe = jdbcTemplate.queryForObject("""
                            SELECT EXISTS(
                                SELECT 1 FROM perguntas
                                WHERE enunciado ILIKE '%(iniciante #%'
                                   OR enunciado ILIKE '%(intermediário #%'
                                   OR enunciado ILIKE '%(intermediario #%'
                                   OR enunciado ILIKE '%(avançado #%'
                                   OR enunciado ILIKE '%(avancado #%'
                                   OR enunciado ILIKE '%qual opção corresponde a%'
                                   OR enunciado ILIKE '%o que melhor descreve%'
                                   OR enunciado ILIKE '%Assinale a correta:%'
                                   OR enunciado ILIKE '%responsável por importa%'
                                   OR enunciado ILIKE 'Em Java,%'
                                   OR enunciado ILIKE 'Em Python,%'
                                   OR enunciado ILIKE 'Em C++,%'
                                   OR enunciado ILIKE 'o que declara%'
                                   OR enunciado ILIKE '%o que declara%'
                                   OR enunciado ILIKE 'Como se faz para%'
                                   OR enunciado ILIKE 'O comando %'
                                   OR enunciado ILIKE 'Um %?'
                                   OR enunciado ILIKE 'Uma %?'
                                   OR enunciado ILIKE 'Break em um laço%'
                                   OR enunciado ILIKE 'Continue em um laço%'
                                   OR enunciado ILIKE '% ocorre ao?'
                                   OR enunciado ~* '^[A-Za-z_:<>()/=+.-]+\\?$'
                                   OR enunciado ILIKE 'Qual a função de%'
                                   OR enunciado ILIKE 'Qual a funcao de%'
                                   OR enunciado ILIKE 'Sobre %, qual alternativa está correta%'
                                   OR enunciado ILIKE 'Sobre o conceito%'
                                   OR enunciado ILIKE '% resulta em?'
                                   OR enunciado ILIKE '%(caso %'
                                   OR enunciado ILIKE 'Qual opção completa corretamente a ideia:%'
                                   OR enunciado ILIKE '%manutenibilidade (série%'
                                   OR enunciado ILIKE '%fundamento do nível%'
                                   OR enunciado ~* '^O que [A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ]+ (permite|usa|é|significa|fornece|faz)\\?'
                                   OR enunciado ~* '`Int '
                                   OR enunciado ~* '`Boolean '
                                   OR LOWER(alternativa_a) = LOWER(alternativa_b)
                                   OR LOWER(alternativa_a) = LOWER(alternativa_c)
                                   OR LOWER(alternativa_a) = LOWER(alternativa_d)
                                   OR LOWER(alternativa_b) = LOWER(alternativa_c)
                                   OR LOWER(alternativa_b) = LOWER(alternativa_d)
                                   OR LOWER(alternativa_c) = LOWER(alternativa_d)
                            )
                            """, Boolean.class);
                    return Boolean.TRUE.equals(existe);
                } catch (Exception ex) {
                    // Fallback: naming antigo do Hibernate (alternativaa...)
                    try {
                        Boolean existe = jdbcTemplate.queryForObject("""
                                SELECT EXISTS(
                                    SELECT 1 FROM perguntas
                                    WHERE enunciado ILIKE '%qual opção corresponde a%'
                                       OR enunciado ILIKE '%o que melhor descreve%'
                                       OR LOWER(alternativaa) = LOWER(alternativab)
                                       OR LOWER(alternativaa) = LOWER(alternativac)
                                       OR LOWER(alternativaa) = LOWER(alternativad)
                                       OR LOWER(alternativab) = LOWER(alternativac)
                                       OR LOWER(alternativab) = LOWER(alternativad)
                                       OR LOWER(alternativac) = LOWER(alternativad)
                                )
                                """, Boolean.class);
                        return Boolean.TRUE.equals(existe);
                    } catch (Exception ignored) {
                        status.setRollbackOnly();
                        return false;
                    }
                }
            }));
        } catch (Exception e) {
            log.warn("Não foi possível validar qualidade das perguntas: {}", e.getMessage());
            return false;
        }
    }

    /** Rei: 5 vidas (4 quizzes + 1 algoritmo), mesmo em banco já seedado. */
    private void garantirReiDoCodigo() {
        Inimigo rei = inimigoRepository.findByOrdemNoCorredor(5).orElse(null);
        if (rei == null || !Boolean.TRUE.equals(rei.getEhRei())) {
            return;
        }

        if (rei.getVidaMaxima() == null || rei.getVidaMaxima() != 5) {
            rei.setVidaMaxima(5);
            rei.setDescricao(
                    "Chefe final: 4 perguntas da linguagem e do nível, depois um algoritmo. Vença-o e torne-se o Rei do Código."
            );
            inimigoRepository.save(rei);
            log.info("Rei do Código atualizado para 5 vidas (4 quizzes + 1 algoritmo).");
        }

        if (desafioCodigoRepository.countByInimigoId(rei.getId()) == 0) {
            criarPoolIntermediario(rei);
            log.info("Desafios de algoritmo do Rei criados.");
        }
    }

    private Inimigo salvarInimigo(String nome, int ordem, TipoInimigo tipo, boolean ehRei, String descricao) {
        return inimigoRepository.save(Inimigo.builder()
                .nome(nome)
                .ordemNoCorredor(ordem)
                .tipo(tipo)
                .vidaMaxima(ehRei ? 5 : (tipo == TipoInimigo.CODIGO ? 1 : 2))
                .ehRei(ehRei)
                .descricao(descricao)
                .build());
    }

    private void criarPoolBasico(Inimigo inimigo) {
        criarDesafioSoma(inimigo);
        criarDesafioParImpar(inimigo);
        criarDesafioProduto(inimigo);
        criarDesafioAbsoluto(inimigo);
    }

    private void criarPoolIntermediario(Inimigo inimigo) {
        criarDesafioMaior(inimigo);
        criarDesafioSomaLista(inimigo);
        criarDesafioContarPares(inimigo);
        criarDesafioFatorial(inimigo);
    }

    private void criarDesafioSoma(Inimigo inimigo) {
        String enunciado = "Leia dois inteiros e imprima a soma deles.";
        DesafioCodigo java = salvarDesafio(inimigo, Linguagem.JAVA, enunciado,
                javaMain("// leia dois inteiros e imprima a soma"),
                "2 3", "5");
        DesafioCodigo python = salvarDesafio(inimigo, Linguagem.PYTHON, enunciado,
                "# leia dois inteiros e imprima a soma\na, b = map(int, input().split())\n",
                "2 3", "5");
        DesafioCodigo cpp = salvarDesafio(inimigo, Linguagem.CPP, enunciado,
                cppMain("// leia dois inteiros e imprima a soma"),
                "2 3", "5");
        criarCasos(java, List.of(
                caso("2 3", "5", false),
                caso("10 20", "30", false),
                caso("-1 1", "0", true)
        ));
        criarCasos(python, List.of(
                caso("2 3", "5", false),
                caso("10 20", "30", false),
                caso("-1 1", "0", true)
        ));
        criarCasos(cpp, List.of(
                caso("2 3", "5", false),
                caso("10 20", "30", false),
                caso("-1 1", "0", true)
        ));
    }

    private void criarDesafioParImpar(Inimigo inimigo) {
        String enunciado = "Leia um inteiro e imprima \"par\" se for par, ou \"impar\" se for ímpar.";
        DesafioCodigo java = salvarDesafio(inimigo, Linguagem.JAVA, enunciado,
                javaMain("// leia um inteiro e imprima par ou impar"),
                "4", "par");
        DesafioCodigo python = salvarDesafio(inimigo, Linguagem.PYTHON, enunciado,
                "# leia um inteiro e imprima par ou impar\nn = int(input())\n",
                "4", "par");
        DesafioCodigo cpp = salvarDesafio(inimigo, Linguagem.CPP, enunciado,
                cppMain("// leia um inteiro e imprima par ou impar"),
                "4", "par");
        criarCasos(java, List.of(
                caso("4", "par", false),
                caso("7", "impar", false),
                caso("0", "par", true)
        ));
        criarCasos(python, List.of(
                caso("4", "par", false),
                caso("7", "impar", false),
                caso("0", "par", true)
        ));
        criarCasos(cpp, List.of(
                caso("4", "par", false),
                caso("7", "impar", false),
                caso("0", "par", true)
        ));
    }

    private void criarDesafioProduto(Inimigo inimigo) {
        String enunciado = "Leia dois inteiros e imprima o produto deles.";
        DesafioCodigo java = salvarDesafio(inimigo, Linguagem.JAVA, enunciado,
                javaMain("// leia dois inteiros e imprima o produto"),
                "3 4", "12");
        DesafioCodigo python = salvarDesafio(inimigo, Linguagem.PYTHON, enunciado,
                "# leia dois inteiros e imprima o produto\na, b = map(int, input().split())\n",
                "3 4", "12");
        DesafioCodigo cpp = salvarDesafio(inimigo, Linguagem.CPP, enunciado,
                cppMain("// leia dois inteiros e imprima o produto"),
                "3 4", "12");
        criarCasos(java, List.of(
                caso("3 4", "12", false),
                caso("5 0", "0", false),
                caso("-2 6", "-12", true)
        ));
        criarCasos(python, List.of(
                caso("3 4", "12", false),
                caso("5 0", "0", false),
                caso("-2 6", "-12", true)
        ));
        criarCasos(cpp, List.of(
                caso("3 4", "12", false),
                caso("5 0", "0", false),
                caso("-2 6", "-12", true)
        ));
    }

    private void criarDesafioAbsoluto(Inimigo inimigo) {
        String enunciado = "Leia um inteiro e imprima o seu valor absoluto.";
        DesafioCodigo java = salvarDesafio(inimigo, Linguagem.JAVA, enunciado,
                javaMain("// leia um inteiro e imprima o valor absoluto"),
                "-8", "8");
        DesafioCodigo python = salvarDesafio(inimigo, Linguagem.PYTHON, enunciado,
                "# leia um inteiro e imprima o valor absoluto\nn = int(input())\n",
                "-8", "8");
        DesafioCodigo cpp = salvarDesafio(inimigo, Linguagem.CPP, enunciado,
                cppMain("// leia um inteiro e imprima o valor absoluto"),
                "-8", "8");
        criarCasos(java, List.of(
                caso("-8", "8", false),
                caso("5", "5", false),
                caso("0", "0", true)
        ));
        criarCasos(python, List.of(
                caso("-8", "8", false),
                caso("5", "5", false),
                caso("0", "0", true)
        ));
        criarCasos(cpp, List.of(
                caso("-8", "8", false),
                caso("5", "5", false),
                caso("0", "0", true)
        ));
    }

    private void criarDesafioMaior(Inimigo inimigo) {
        String enunciado = "Leia três inteiros e imprima o maior deles.";
        DesafioCodigo java = salvarDesafio(inimigo, Linguagem.JAVA, enunciado,
                javaMain("// leia três inteiros e imprima o maior"),
                "1 5 3", "5");
        DesafioCodigo python = salvarDesafio(inimigo, Linguagem.PYTHON, enunciado,
                "# leia três inteiros e imprima o maior\nnums = list(map(int, input().split()))\n",
                "1 5 3", "5");
        DesafioCodigo cpp = salvarDesafio(inimigo, Linguagem.CPP, enunciado,
                cppMain("// leia três inteiros e imprima o maior"),
                "1 5 3", "5");
        criarCasos(java, List.of(
                caso("1 5 3", "5", false),
                caso("9 2 7", "9", false),
                caso("4 4 4", "4", true)
        ));
        criarCasos(python, List.of(
                caso("1 5 3", "5", false),
                caso("9 2 7", "9", false),
                caso("4 4 4", "4", true)
        ));
        criarCasos(cpp, List.of(
                caso("1 5 3", "5", false),
                caso("9 2 7", "9", false),
                caso("4 4 4", "4", true)
        ));
    }

    private void criarDesafioSomaLista(Inimigo inimigo) {
        String enunciado = "Na primeira linha leia N. Na segunda linha leia N inteiros e imprima a soma deles.";
        DesafioCodigo java = salvarDesafio(inimigo, Linguagem.JAVA, enunciado,
                javaMain("// leia N e depois N inteiros; imprima a soma"),
                "3\n1 2 3", "6");
        DesafioCodigo python = salvarDesafio(inimigo, Linguagem.PYTHON, enunciado,
                """
                # leia N e depois N inteiros; imprima a soma
                n = int(input())
                nums = list(map(int, input().split()))
                """,
                "3\n1 2 3", "6");
        DesafioCodigo cpp = salvarDesafio(inimigo, Linguagem.CPP, enunciado,
                cppMain("// leia N e depois N inteiros; imprima a soma"),
                "3\n1 2 3", "6");
        criarCasos(java, List.of(
                caso("3\n1 2 3", "6", false),
                caso("4\n10 0 -2 5", "13", false),
                caso("1\n42", "42", true)
        ));
        criarCasos(python, List.of(
                caso("3\n1 2 3", "6", false),
                caso("4\n10 0 -2 5", "13", false),
                caso("1\n42", "42", true)
        ));
        criarCasos(cpp, List.of(
                caso("3\n1 2 3", "6", false),
                caso("4\n10 0 -2 5", "13", false),
                caso("1\n42", "42", true)
        ));
    }

    private void criarDesafioContarPares(Inimigo inimigo) {
        String enunciado = "Na primeira linha leia N. Na segunda linha leia N inteiros e imprima quantos são pares.";
        DesafioCodigo java = salvarDesafio(inimigo, Linguagem.JAVA, enunciado,
                javaMain("// leia N e N inteiros; imprima quantos sao pares"),
                "5\n1 2 3 4 5", "2");
        DesafioCodigo python = salvarDesafio(inimigo, Linguagem.PYTHON, enunciado,
                """
                # leia N e N inteiros; imprima quantos sao pares
                n = int(input())
                nums = list(map(int, input().split()))
                """,
                "5\n1 2 3 4 5", "2");
        DesafioCodigo cpp = salvarDesafio(inimigo, Linguagem.CPP, enunciado,
                cppMain("// leia N e N inteiros; imprima quantos sao pares"),
                "5\n1 2 3 4 5", "2");
        criarCasos(java, List.of(
                caso("5\n1 2 3 4 5", "2", false),
                caso("3\n2 4 6", "3", false),
                caso("2\n1 3", "0", true)
        ));
        criarCasos(python, List.of(
                caso("5\n1 2 3 4 5", "2", false),
                caso("3\n2 4 6", "3", false),
                caso("2\n1 3", "0", true)
        ));
        criarCasos(cpp, List.of(
                caso("5\n1 2 3 4 5", "2", false),
                caso("3\n2 4 6", "3", false),
                caso("2\n1 3", "0", true)
        ));
    }

    private void criarDesafioFatorial(Inimigo inimigo) {
        String enunciado = "Leia um inteiro N (0 <= N <= 12) e imprima o fatorial de N.";
        DesafioCodigo java = salvarDesafio(inimigo, Linguagem.JAVA, enunciado,
                javaMain("// leia N e imprima N!"),
                "5", "120");
        DesafioCodigo python = salvarDesafio(inimigo, Linguagem.PYTHON, enunciado,
                "# leia N e imprima N!\nn = int(input())\n",
                "5", "120");
        DesafioCodigo cpp = salvarDesafio(inimigo, Linguagem.CPP, enunciado,
                cppMain("// leia N e imprima N!"),
                "5", "120");
        criarCasos(java, List.of(
                caso("5", "120", false),
                caso("0", "1", false),
                caso("7", "5040", true)
        ));
        criarCasos(python, List.of(
                caso("5", "120", false),
                caso("0", "1", false),
                caso("7", "5040", true)
        ));
        criarCasos(cpp, List.of(
                caso("5", "120", false),
                caso("0", "1", false),
                caso("7", "5040", true)
        ));
    }

    private String javaMain(String comentario) {
        return """
                import java.util.Scanner;

                public class Main {
                    public static void main(String[] args) {
                        Scanner sc = new Scanner(System.in);
                        %s
                    }
                }
                """.formatted(comentario);
    }

    private String cppMain(String comentario) {
        return """
                #include <iostream>
                using namespace std;

                int main() {
                    %s
                    return 0;
                }
                """.formatted(comentario);
    }

    private record CasoSeed(String entrada, String saida, boolean oculto) {}

    private CasoSeed caso(String entrada, String saida, boolean oculto) {
        return new CasoSeed(entrada, saida, oculto);
    }

    private void criarCasos(DesafioCodigo desafio, List<CasoSeed> casos) {
        int ordem = 1;
        for (CasoSeed c : casos) {
            salvarCaso(desafio, ordem++, c.entrada(), c.saida(), c.oculto());
        }
    }

    private DesafioCodigo salvarDesafio(Inimigo inimigo, Linguagem linguagem, String enunciado,
                                        String codigoInicial, String entradaExemplo, String saidaExemplo) {
        return desafioCodigoRepository.save(DesafioCodigo.builder()
                .inimigo(inimigo)
                .linguagem(linguagem)
                .enunciado(enunciado)
                .codigoInicial(codigoInicial)
                .entradaExemplo(entradaExemplo)
                .saidaExemplo(saidaExemplo)
                .build());
    }

    private void salvarCaso(DesafioCodigo desafio, int ordem, String entrada, String saida, boolean oculto) {
        casoTesteRepository.save(CasoTeste.builder()
                .desafio(desafio)
                .ordem(ordem)
                .entrada(entrada)
                .saidaEsperada(saida)
                .oculto(oculto)
                .build());
    }
}
