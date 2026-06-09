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

leer_env() {
    local nombre="$1"
    local valor
    valor="$(grep -E "^${nombre}=" "${ENV_FILE}" | tail -n 1 | cut -d "=" -f 2- || true)"
    valor="${valor%\"}"
    valor="${valor#\"}"
    valor="${valor%\'}"
    valor="${valor#\'}"
    printf "%s" "${valor}"
}

DB_NAME="${DB_NAME:-$(leer_env DB_NAME)}"
DB_USER="${DB_USER:-$(leer_env DB_USER)}"

: "${DB_NAME:?Falta DB_NAME en .env}"
: "${DB_USER:?Falta DB_USER en .env}"

TARGET_DB="${1:-${DB_NAME}}"
BACKUP_LABEL="${2:-${TARGET_DB}}"
TIMESTAMP="${BACKUP_TIMESTAMP:-$(date +%Y%m%d_%H%M%S)}"
SAFE_LABEL="$(printf '%s' "${BACKUP_LABEL}" | tr -c 'A-Za-z0-9_.-' '_')"
CONTAINER_FILE="/tmp/${SAFE_LABEL}_${TIMESTAMP}.dump"
BACKUP_FILE="${BACKUP_DIR}/${SAFE_LABEL}_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

docker exec "${DB_CONTAINER}" pg_dump \
    --username="${DB_USER}" \
    --dbname="${TARGET_DB}" \
    --format=custom \
    --no-owner \
    --no-privileges \
    --file="${CONTAINER_FILE}"

docker cp "${DB_CONTAINER}:${CONTAINER_FILE}" "${BACKUP_FILE}"
docker exec "${DB_CONTAINER}" rm -f "${CONTAINER_FILE}"

echo "Backup creado: ${BACKUP_FILE} (${TARGET_DB})"
