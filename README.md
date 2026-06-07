# Sistema de Agua

## Entornos Docker

El proyecto usa Compose por capas:

- `docker-compose.yml`: base comun para servicios `web` y `db`.
- `docker-compose.dev.yml`: desarrollo local con codigo montado y `runserver`.
- `docker-compose.prod.yml`: VPS/produccion con `gunicorn`, `collectstatic` y puerto publicado solo en `127.0.0.1`.

Crear el archivo real de variables:

```bash
cp .env.example .env
```

Levantar desarrollo:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Levantar produccion/VPS:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

El archivo `.env` no se versiona. `.env.example` es el contrato de variables.

## Preparacion multi-tenant

La Fase 1 solo prepara Docker y variables. El sistema aun usa una sola base activa mediante `DB_NAME`.

Contrato futuro:

- `MASTER_DB_NAME`: base master.
- `TENANT_SLUGS`: juntas disponibles, por ejemplo `carabuela,esperanza,pesillo`.
- `TENANT_DB_PREFIX`: prefijo para bases por junta.
- `TENANT_ROUTE_MODE=path`: deteccion futura por rutas como `/carabuela/`, `/esperanza/`, `/pesillo/`.

## Backups de base de datos

Crear un backup de PostgreSQL:

```bash
bash scripts/backup_db.sh
```

Los archivos se guardan en `backups/` y no se suben a git.

Restaurar un backup:

```bash
bash scripts/restore_db.sh backups/nombre_del_backup.dump
```

La restauración pide escribir `RESTAURAR` antes de reemplazar la base de datos.
