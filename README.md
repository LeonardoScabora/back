# Backend Rei do Codigo

API Spring Boot (Java 21) com PostgreSQL.

## Executar com Docker (recomendado)

Requisito: Docker Desktop em execucao.

Se voce ainda tiver um container PostgreSQL antigo (`backreidocodigo` criado manualmente), pare e remova antes para evitar conflito de porta e nome:

```powershell
docker stop backreidocodigo
docker rm backreidocodigo
```

Na pasta deste backend:

```powershell
cd C:\Users\leonardo.scabora\FEMA\TCC\DESENVOLVIMENTO\BACK\back
docker compose up --build -d
```

Containers:

| Nome | Servico | Porta |
|------|---------|-------|
| `dbreidocodigo` | PostgreSQL | `5432` |
| `backreidocodigo` | API Spring Boot | `8080` |

API: `http://localhost:8080`

Parar:

```powershell
docker compose down
```

Parar e apagar dados do banco:

```powershell
docker compose down -v
```

## Executar localmente (sem Docker na API)

Requisitos:

- Java 21
- PostgreSQL na porta `5432` (pode ser o container `dbreidocodigo` do compose)

Banco esperado (ver `src/main/resources/application.properties`):

- banco: `reidocodigo`
- usuario: `postgres`
- senha: `1234`

```powershell
.\mvnw.cmd spring-boot:run
```

## Executar os testes

```powershell
.\mvnw.cmd test
```
