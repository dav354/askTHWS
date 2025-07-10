#!/usr/bin/env bash

set -euo pipefail

DB_NAME="askthws_scraper"
MONGO_CONTAINER_NAME="mongodb-atlas-local"
VECTOR_COLLECTION="vectors" # The collection with the vector index

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
OUTPUT_FILE_NAME_DATA="${DB_NAME}_backup_${TIMESTAMP_FILE}.gz"
OUTPUT_FILE_NAME_INDEX="${DB_NAME}_vector_index_${TIMESTAMP_FILE}.json"
BACKUP_PATH_IN_CONTAINER="/tmp/${OUTPUT_FILE_NAME_DATA}"

log_message INFO "Dumping Vector Search Index definition from collection '$VECTOR_COLLECTION'..."

MONGO_EVAL_COMMAND="JSON.stringify(db.getSiblingDB('$DB_NAME').$VECTOR_COLLECTION.getSearchIndexes())"

if docker exec "$MONGO_CONTAINER_NAME" mongosh \
  --username "$MONGO_USER" \
  --password "$MONGO_PASS" \
  --authenticationDatabase "admin" \
  --quiet \
  --eval "$MONGO_EVAL_COMMAND" > "$OUTPUT_FILE_NAME_INDEX"; then
  log_message SUCCESS "Successfully dumped index definition to ./${OUTPUT_FILE_NAME_INDEX}"
else
  log_message ERROR "Failed to dump vector search index definition."
  exit 1
fi

log_message INFO "Starting MongoDB data dump for database '$DB_NAME'..."

if docker exec "$MONGO_CONTAINER_NAME" mongodump \
  --username "$MONGO_USER" \
  --password "$MONGO_PASS" \
  --authenticationDatabase "admin" \
  --db "$DB_NAME" \
  --archive="$BACKUP_PATH_IN_CONTAINER" \
  --gzip >/dev/null 2>&1; then
  log_message SUCCESS "Successfully created data archive at '$BACKUP_PATH_IN_CONTAINER' inside the container."
else
  log_message ERROR "mongodump command failed. Check docker logs for '$MONGO_CONTAINER_NAME'."
  exit 1
fi

log_message INFO "Copying data dump file to host: ./${OUTPUT_FILE_NAME_DATA}"
if docker cp "${MONGO_CONTAINER_NAME}:${BACKUP_PATH_IN_CONTAINER}" "./${OUTPUT_FILE_NAME_DATA}" >/dev/null 2>&1; then
  log_message SUCCESS "Successfully copied data dump file to ./$OUTPUT_FILE_NAME_DATA on the host."
else
  log_message ERROR "Failed to copy data dump file from container to host."
  docker exec "$MONGO_CONTAINER_NAME" rm "$BACKUP_PATH_IN_CONTAINER" >/dev/null 2>&1 || log_message WARN "Cleanup of archive in container also failed."
  exit 1
fi

log_message INFO "Cleaning up temporary data archive from container..."
if docker exec "$MONGO_CONTAINER_NAME" rm "$BACKUP_PATH_IN_CONTAINER" >/dev/null 2>&1; then
  log_message SUCCESS "Successfully cleaned up temporary data archive from container."
else
  log_message WARN "Failed to clean up temporary data archive from inside the container."
fi

SIZE=$(du -h "$OUTPUT_FILE_NAME_DATA" | awk '{print $1}')
log_message SUCCESS "Backup complete!"
log_message SUCCESS "Data file:   ./${OUTPUT_FILE_NAME_DATA} ($SIZE)"
log_message SUCCESS "Index file:  ./${OUTPUT_FILE_NAME_INDEX}"
exit 0
