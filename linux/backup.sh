#!/bin/bash

# Set the directory to monitor for new checkpoints
MONITOR_DIR="/path/to/your/checkpoint/folder"

# Set the target directory to copy new checkpoints to
TARGET_DIR="/path/to/your/target/folder"

# Set the interval (in seconds) to check for new checkpoints
CHECK_INTERVAL=10

# Initialize the list of existing checkpoints
LAST_CHECKPOINTS=$(ls $MONITOR_DIR 2>/dev/null)

while true; do
    # Get the current list of checkpoints
    CURRENT_CHECKPOINTS=$(ls $MONITOR_DIR 2>/dev/null)

    # Compare the current list with the last list to find new checkpoints
    NEW_CHECKPOINTS=$(comm -13 <(echo "$LAST_CHECKPOINTS" | sort) <(echo "$CURRENT_CHECKPOINTS" | sort))

    # If new checkpoints are detected, copy them to the target directory
    if [ ! -z "$NEW_CHECKPOINTS" ]; then
        for CHECKPOINT in $NEW_CHECKPOINTS; do
            echo "New checkpoint detected: $CHECKPOINT"
            cp "$MONITOR_DIR/$CHECKPOINT" "$TARGET_DIR/"
        done
    fi

    # Update the list of existing checkpoints
    LAST_CHECKPOINTS=$CURRENT_CHECKPOINTS

    # Wait for the specified interval before checking again
    sleep $CHECK_INTERVAL
done
