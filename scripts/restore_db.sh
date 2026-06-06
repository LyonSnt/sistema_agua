#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
DB_CONTAINER="${DB_CONTAINER:-sistema_agua_db}"

if [[ $# -ne 1 ]]; then
    echo "Uso: $0 ruta/al/backup.dump" >&2
    exit 1
fi

BACKUP_FILE="$1"

if [[ ! -f "${BACKUP_FILE}" ]]; then
    echo "No existe el archivo de backup: ${BACKUP_FILE}" >&2
    exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "No existe ${ENV_FILE}. Cree el archivo .env antes de restaurar." >&2
    exit 1
fi

set -a
source "${ENV_FILE}"
set +a

: "${DB_NAME:?Falta DB_NAME en .env}"
: "${DB_USER:?Falta DB_USER en .env}"

echo "ATENCION: esto reemplazara el contenido de la base '${DB_NAME}'."
read -r -p "Escriba RESTAURAR para continuar: " CONFIRMACION

if [[ "${CONFIRMACION}" != "RESTAURAR" ]]; then
    echo "Restauracion cancelada."
    exit 1
fi

BACKUP_BASENAME="$(basename "${BACKUP_FILE}")"
docker cp "${BACKUP_FILE}" "${DB_CONTAINER}:/tmp/${BACKUP_BASENAME}"

docker exec "${DB_CONTAINER}" sh -c "
set -e
psql --username='${DB_USER}' --dbname='postgres' --command=\"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();\"
dropdb --username='${DB_USER}' --if-exists '${DB_NAME}'
createdb --username='${DB_USER}' '${DB_NAME}'
pg_restore --username='${DB_USER}' --dbname='${DB_NAME}' --clean --if-exists --no-owner --no-privileges '/tmp/${BACKUP_BASENAME}'
rm -f '/tmp/${BACKUP_BASENAME}'
"

echo "Base restaurada desde: ${BACKUP_FILE}"
