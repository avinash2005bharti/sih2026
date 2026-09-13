# Sovereign AI Workbench Docker Compose Infrastructure

This Compose stack provides the essential storage, vector database, and caching infrastructure for the Sovereign AI Workbench:

- **MongoDB**: on port `27017`
- **Qdrant Vector Database**: on port `6333`
- **Valkey Memory Cache**: on port `6379`
- **Neo4j Knowledge Graph**: on ports `7474` and `7687`

> [!NOTE]
> **Ollama runs locally on the host machine** (`http://localhost:11434`), NOT inside Docker.
> This allows Ollama to natively access host GPUs (NVIDIA/CUDA) without Docker GPU reservations or NVIDIA Container Toolkit, and gracefully fall back to CPU mode on laptops without dedicated graphics.

## Start Infrastructure

```bash
cd docker-compose
docker compose up -d
```

## Stop Infrastructure

```bash
docker compose down
```

## Status

```bash
docker compose ps
```

## Logs

```bash
docker compose logs -f
```

## Ports exposed on host

- MongoDB: `localhost:27017`
- Qdrant: `http://localhost:6333`
- Valkey: `localhost:6379`
- Neo4j Browser: `http://localhost:7474` / `bolt://localhost:7687`
