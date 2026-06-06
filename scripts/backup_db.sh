#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
BACKUP_DIR="${BACKUP_DIR:-${ROOT_DIR}/backups}"
DB_CONTAINER="${DB_CONTAINER:-sistema_agua_db}"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "No existe ${ENV_FILE}. Cree el archivo .env antes de generar backups." >&2
    exit 1
fi

set -a
source "${ENV_FILE}"
set +a

: "${DB_NAME:?Falta DB_NAME en .env}"
: "${DB_USER:?Falta DB_USER en .env}"

mkdir -p "${BACKUP_DIR}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump"

docker exec "${DB_CONTAINER}" pg_dump \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --format=custom \
    --no-owner \
    --no-privileges \
    --file="/tmp/${DB_NAME}_${TIMESTAMP}.dump"

docker cp "${DB_CONTAINER}:/tmp/${DB_NAME}_${TIMESTAMP}.dump" "${BACKUP_FILE}"
docker exec "${DB_CONTAINER}" rm -f "/tmp/${DB_NAME}_${TIMESTAMP}.dump"

echo "Backup creado: ${BACKUP_FILE}"
