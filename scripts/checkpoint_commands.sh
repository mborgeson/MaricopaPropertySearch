#!/bin/bash
# Checkpoint Generation Commands for Maricopa Property Search GUI

# Set the base directory with proper quoting
BASE_DIR="/home/mattb/MaricopaPropertySearch"

# Function to generate checkpoint manually
generate_checkpoint() {
    python3 "$BASE_DIR/scripts/generate_checkpoint.py" "manual"
}

# Function to test checkpoint generation
test_checkpoint() {
    echo "Testing checkpoint generation..."
    python3 "$BASE_DIR/scripts/generate_checkpoint.py" "test"

    # Show latest checkpoint
    latest=$(ls -t "$BASE_DIR/checkpoints/"*.md 2>/dev/null | grep -v README | head -1)
    echo "Latest checkpoint: $latest"
}

# Cron job setup for automatic daily checkpoints (optional)
setup_daily_checkpoint() {
    # Add to user's crontab - daily at 5 PM
    (crontab -l 2>/dev/null; echo "0 17 * * * python3 '$BASE_DIR/scripts/generate_checkpoint.py' daily") | crontab -
    echo "Daily checkpoint scheduled for 5:00 PM"
}

# View latest checkpoint
view_latest() {
    latest=$(ls -t "$BASE_DIR/checkpoints/"*.md 2>/dev/null | grep -v README | grep -v GUIDE | head -1)
    if [ -f "$latest" ]; then
        cat "$latest"
    else
        echo "No checkpoints found"
    fi
}

# List all checkpoints
list_checkpoints() {
    ls -lht "$BASE_DIR/checkpoints/"*.md 2>/dev/null | grep -v README | grep -v GUIDE
}

# Main menu
case "$1" in
    generate)
        generate_checkpoint
        ;;
    test)
        test_checkpoint
        ;;
    setup-daily)
        setup_daily_checkpoint
        ;;
    view)
        view_latest
        ;;
    list)
        list_checkpoints
        ;;
    *)
        echo "Usage: $0 {generate|test|setup-daily|view|list}"
        echo ""
        echo "Commands:"
        echo "  generate    - Create a new checkpoint now"
        echo "  test        - Test checkpoint generation"
        echo "  setup-daily - Schedule daily automatic checkpoints"
        echo "  view        - View the latest checkpoint"
        echo "  list        - List all checkpoints"
        ;;
esac