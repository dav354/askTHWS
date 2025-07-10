#!/usr/bin/env bash

set -euo pipefail

DB_NAME="askthws_scraper"
MONGO_CONTAINER_NAME="mongodb-atlas-local"

# MongoDB credentials from knowledgeMapper/config.py and docker-compose.yml
MONGO_USER="scraper"
MONGO_PASS="password"

COLOR_OFF='\033[0m'
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'

log_message() {
  local level="$1"
  shift
  local message="$*"
  local color="${COLOR_OFF}"

  case "$level" in
    INFO) color="${COLOR_BLUE}" ;;
    SUCCESS) color="${COLOR_GREEN}" ;;
    WARN|WARNING) color="${COLOR_YELLOW}" ;;
    ERROR) color="${COLOR_RED}" ;;
    *) level="LOG"; color="${COLOR_OFF}" ;;
  esac

  echo -e " [${color}${level}${COLOR_OFF}] ${message}"
}

TIMESTAMP_FILE=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE_NAME="${DB_NAME}_backup_${TIMESTAMP_FILE}.gz"
BACKUP_PATH_IN_CONTAINER="/tmp/${OUTPUT_FILE_NAME}"

log_message INFO "Starting MongoDB dump for database '$DB_NAME' from container '$MONGO_CONTAINER_NAME'..."

if docker exec "$MONGO_CONTAINER_NAME" mongodump \
  --username "$MONGO_USER" \
  --password "$MONGO_PASS" \
  --authenticationDatabase "admin" \
  --db "$DB_NAME" \
  --archive="$BACKUP_PATH_IN_CONTAINER" \
  --gzip >/dev/null 2>&1; then
  log_message SUCCESS "Successfully created dump archive at '$BACKUP_PATH_IN_CONTAINER' inside the container."
else
  log_message ERROR "mongodump command failed inside the container '$MONGO_CONTAINER_NAME'. Check docker logs for '$MONGO_CONTAINER_NAME'."
  exit 1
fi

log_message INFO "Copying dump file to host: ./${OUTPUT_FILE_NAME}"
if docker cp "${MONGO_CONTAINER_NAME}:${BACKUP_PATH_IN_CONTAINER}" "./${OUTPUT_FILE_NAME}" >/dev/null 2>&1; then
  log_message SUCCESS "Successfully copied dump file to ./$OUTPUT_FILE_NAME on the host."
else
  log_message ERROR "Failed to copy dump file from container to host."
  docker exec "$MONGO_CONTAINER_NAME" rm "$BACKUP_PATH_IN_CONTAINER" >/dev/null 2>&1 || log_message WARN "Cleanup of archive in container also failed."
  exit 1
fi

log_message INFO "Cleaning up temporary archive from container..."
if docker exec "$MONGO_CONTAINER_NAME" rm "$BACKUP_PATH_IN_CONTAINER" >/dev/null 2>&1; then
  log_message SUCCESS "Successfully cleaned up temporary archive from container."
else
  log_message WARN "Failed to clean up temporary archive '$BACKUP_PATH_IN_CONTAINER' from inside the container. You may need to remove it manually."
fi

SIZE=$(du -h "$OUTPUT_FILE_NAME" | awk '{print $1}')
log_message SUCCESS "Output file: ./${OUTPUT_FILE_NAME} ($SIZE)"
exit 0
