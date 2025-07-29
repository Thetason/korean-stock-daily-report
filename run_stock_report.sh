#!/bin/bash

# Korean Stock Daily Report Runner
# This script runs the stock report and logs the execution

# Set up the environment
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Change to the project directory
cd /Users/seoyeongbin/korean-stock-daily-report/

# Create logs directory if it doesn't exist
mkdir -p logs

# Log start time
echo "=== Stock Report Started at $(date) ===" >> logs/execution.log

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found!" >> logs/execution.log
    exit 1
fi

# Run the stock report in manual mode
python3 main.py manual >> logs/execution.log 2>&1

# Check exit status
if [ $? -eq 0 ]; then
    echo "Stock report completed successfully at $(date)" >> logs/execution.log
    # Send notification (optional)
    osascript -e 'display notification "주식 일일 리포트가 생성되었습니다!" with title "Stock Report"'
else
    echo "Stock report failed at $(date)" >> logs/execution.log
    osascript -e 'display notification "주식 리포트 생성 실패" with title "Stock Report Error"'
fi

echo "=== Stock Report Ended at $(date) ===" >> logs/execution.log
echo "" >> logs/execution.log