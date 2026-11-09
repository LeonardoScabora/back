package ReiDoCodigo.back.Model.Enum;

public enum NivelDificuldade {
    INICIANTE,
    INTERMEDIARIO,
    AVANCADO;

    public static NivelDificuldade fromCodigo(int codigo) {
        return switch (codigo) {
            case 1 -> INICIANTE;
            case 2 -> INTERMEDIARIO;
            case 3 -> AVANCADO;
            default -> throw new IllegalArgumentException("Nível inválido: " + codigo);
        };
    }
}
