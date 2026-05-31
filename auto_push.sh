#!/bin/bash
# Move to the project directory
cd /Users/apple/crypto_sniper

while true; do
    # Add all changes except those in .gitignore
    git add .
    
    # Check if there are changes to commit
    if ! git diff-index --quiet HEAD; then
        git commit -m "Automated Update: PnL and findings - $(date)"
        git push origin main
        echo "🚀 GitHub Updated: $(date)"
    fi
    
    # Wait for 1 hour
    sleep 3600
done
