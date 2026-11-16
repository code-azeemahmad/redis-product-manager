#!/usr/bin/env bash
# ==============================================================================
# PostgreSQL Restore Script — Checksum Verification & Disaster Recovery
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"

CONTAINER_NAME="saas-postgres"
DB_NAME="${POSTGRES_DB:-saas_products}"
DB_USER="${POSTGRES_USER:-app_user}"

# Determine backup file: user argument or latest file
if [ $# -ge 1 ]; then
    BACKUP_FILE="$1"
else
    BACKUP_FILE="$(find "${BACKUP_DIR}" -name "backup_${DB_NAME}_*.dump" -type f | sort | tail -n 1 || true)"
fi

if [ -z "${BACKUP_FILE}" ] || [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE:-none available in ${BACKUP_DIR}}" >&2
    exit 1
fi

CHECKSUM_FILE="${BACKUP_FILE}.sha256"

echo "=== Starting PostgreSQL Restore ==="
echo "Target backup: ${BACKUP_FILE}"

# 1. Verify Checksum
if [ -f "${CHECKSUM_FILE}" ]; then
    echo "Verifying SHA-256 checksum..."
    (cd "$(dirname "${BACKUP_FILE}")" && sha256sum -c "$(basename "${CHECKSUM_FILE}")")
    echo "Checksum verification PASSED."
else
    echo "WARNING: Checksum file '${CHECKSUM_FILE}' not found; proceeding with unverified dump."
fi

# 2. Verify PostgreSQL Container is Running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: PostgreSQL container '${CONTAINER_NAME}' is not running." >&2
    exit 1
fi

# 3. Restore via pg_restore
echo "Executing pg_restore into database '${DB_NAME}'..."
cat "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" pg_restore -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists

# 4. Verify Record Count Post-Restore
COUNT=$(docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM products;" | tr -d '[:space:]')
echo "Verification query result: ${COUNT} products present in database."

echo "=== PostgreSQL Restore Completed Successfully ==="
