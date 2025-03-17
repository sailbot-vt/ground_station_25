#!/bin/bash

# Start Node.js in the background
npm run start &
NODE_PID=$!

# Start Python script in the background
python src/main.py &
PYTHON_PID=$!

# Trap Ctrl+C and kill both processes
trap "kill $NODE_PID $PYTHON_PID" SIGINT

# Wait for both processes to finish
wait $NODE_PID
wait $PYTHON_PID
