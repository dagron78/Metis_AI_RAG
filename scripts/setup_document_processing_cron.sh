#!/bin/bash
# Setup a cron job to process documents periodically

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/process_pending_documents_cron.py"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/document_processing.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check if the script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Script not found at $SCRIPT_PATH"
    exit 1
fi

# Create a temporary file for the crontab
TEMP_CRONTAB=$(mktemp)

# Export current crontab to the temporary file
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "" > "$TEMP_CRONTAB"

# Check if the cron job already exists
if grep -q "process_pending_documents_cron.py" "$TEMP_CRONTAB"; then
    echo "Cron job already exists. Updating..."
    # Remove the existing cron job
    sed -i '/process_pending_documents_cron.py/d' "$TEMP_CRONTAB"
fi

# Add the cron job to run every 3 minutes
echo "# Process pending documents every 3 minutes" >> "$TEMP_CRONTAB"
echo "*/3 * * * * cd $PROJECT_DIR && python $SCRIPT_PATH >> $LOG_FILE 2>&1" >> "$TEMP_CRONTAB"

# Install the new crontab
crontab "$TEMP_CRONTAB"

echo "Cron job installed to run every 3 minutes."
echo "Log file: $LOG_FILE"

# Clean up
rm "$TEMP_CRONTAB"

echo "Done!"