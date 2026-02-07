#!/bin/bash
# Auto-restart script for Dodge the Lasers
# If the game crashes, it relaunches automatically after 3 seconds.
# Press Ctrl+C to stop the restart loop.

echo "============================================"
echo "  DODGE THE LASERS - Auto-Restart Mode"
echo "  Press Ctrl+C to stop the restart loop"
echo "============================================"

while true; do
    echo ""
    echo "[$(date)] Starting game..."
    python main.py
    EXIT_CODE=$?
    echo ""
    echo "[$(date)] Game exited with code $EXIT_CODE."
    echo "Restarting in 3 seconds..."
    sleep 3
done
