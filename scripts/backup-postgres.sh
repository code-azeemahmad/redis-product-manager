#!/usr/bin/env bash
# ==============================================================================
# PostgreSQL Backup Script — Automated Compressed Dump & Checksum
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"

mkdir -p "${BACKUP_DIR}"

TIMESTAMP="$(date -u +"%Y%m%d_%H%M%S")"
CONTAINER_NAME="saas-postgres"
DB_NAME="${POSTGRES_DB:-saas_products}"
DB_USER="${POSTGRES_USER:-app_user}"
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.dump"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

echo "=== Starting PostgreSQL Backup: ${DB_NAME} at ${TIMESTAMP} ==="

# Verify container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: PostgreSQL container '${CONTAINER_NAME}' is not running." >&2
    exit 1
fi

# Execute pg_dump with custom compression format
echo "Creating compressed pg_dump artifact..."
docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" -F c > "${BACKUP_FILE}"

# Verify file was generated and non-empty
if [ ! -s "${BACKUP_FILE}" ]; then
    echo "ERROR: Generated backup file is empty or missing." >&2
    rm -f "${BACKUP_FILE}"
    exit 1
fi

FILESIZE="$(du -h "${BACKUP_FILE}" | cut -f1)"
echo "Backup created successfully: ${BACKUP_FILE} (${FILESIZE})"

# Generate SHA-256 Checksum
(cd "${BACKUP_DIR}" && sha256sum "$(basename "${BACKUP_FILE}")" > "${CHECKSUM_FILE}")
echo "SHA-256 checksum generated: ${CHECKSUM_FILE}"

# Retention Cleanup: prune backups older than 7 days
echo "Pruning backups older than 7 days..."
find "${BACKUP_DIR}" -name "backup_${DB_NAME}_*.dump*" -type f -mtime +7 -delete

echo "=== PostgreSQL Backup Completed Successfully ==="
