#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
BACKUP_ROOT="${BACKUP_DIR:-${ROOT_DIR}/backups}"
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
MASTER_DB_NAME="${MASTER_DB_NAME:-$(leer_env MASTER_DB_NAME)}"

: "${DB_NAME:?Falta DB_NAME en .env}"
: "${DB_USER:?Falta DB_USER en .env}"

MASTER_DB_NAME="${MASTER_DB_NAME:-${DB_NAME}}"
TIMESTAMP="${BACKUP_TIMESTAMP:-$(date +%Y%m%d_%H%M%S)}"
RUN_DIR="${BACKUP_ROOT}/$(date +%Y%m%d)"

mkdir -p "${RUN_DIR}"

echo "Generando backups en: ${RUN_DIR}"

BACKUP_DIR="${RUN_DIR}" BACKUP_TIMESTAMP="${TIMESTAMP}" \
    bash "${ROOT_DIR}/scripts/backup_db.sh" "${MASTER_DB_NAME}" "master"

if [[ "${DB_NAME}" != "${MASTER_DB_NAME}" ]]; then
    BACKUP_DIR="${RUN_DIR}" BACKUP_TIMESTAMP="${TIMESTAMP}" \
        bash "${ROOT_DIR}/scripts/backup_db.sh" "${DB_NAME}" "default"
fi

TENANTS="$(
    docker exec "${DB_CONTAINER}" psql \
        --username="${DB_USER}" \
        --dbname="${MASTER_DB_NAME}" \
        --tuples-only \
        --no-align \
        --field-separator="|" \
        --command="SELECT slug, db_name FROM tenants_tenant WHERE activo = true ORDER BY slug;"
)"

if [[ -z "${TENANTS}" ]]; then
    echo "No hay tenants activos registrados en ${MASTER_DB_NAME}."
    exit 0
fi

while IFS="|" read -r SLUG TENANT_DB; do
    [[ -z "${SLUG}" || -z "${TENANT_DB}" ]] && continue

    BACKUP_DIR="${RUN_DIR}" BACKUP_TIMESTAMP="${TIMESTAMP}" \
        bash "${ROOT_DIR}/scripts/backup_db.sh" "${TENANT_DB}" "tenant_${SLUG}"
done <<< "${TENANTS}"

echo "Backups finalizados: ${RUN_DIR}"
