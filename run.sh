#!/usr/bin/env bash

# Check if the bin directory exists
if [ ! -d "bin" ]; then
    # Create the bin directory
    mkdir bin
    if [ $? -ne 0 ]; then
        echo "Failed to create bin directory. Please check your permissions."
        exit 1
    fi
    echo "Created bin directory."
fi

if [ -f "last_build_time.txt" ]; then
    last_build_time=$(cat last_build_time.txt)
    # if last_build_time is older than 1 hour
    if [ $(($(date +%s) - last_build_time)) -gt 3600 ]; then
        echo "Server binary out of date. Rebuilding..."
        # Check if Go is on the PATH
        if ! command -v go &> /dev/null; then
            echo "Go is not installed. Please install Go to run this script."
            exit 1
        fi
        go build -o bin/server src/web_engine/server.go
        echo "Go server built successfully."
        date +%s > last_build_time.txt
    else
        echo "last_build_time.txt is less than 1 hour old. Skipping build."
    fi
else
    echo "last_build_time.txt not found. Building the Go server..."
    # Check if Go is on the PATH
    if ! command -v go &> /dev/null; then
        echo "Go is not installed. Please install Go to run this script."
        exit 1
    fi
    go build -o bin/server src/web_engine/server.go
    echo "Go server built successfully."
    date +%s > last_build_time.txt
fi

# Start the Go server in the background
bin/server & 
GO_PID=$!

# Start Python script in the background
python src/main.py &
PYTHON_PID=$!

# Trap Ctrl+C and kill both processes
trap "kill $GO_PID $PYTHON_PID" SIGINT

# Wait for both processes to finish
wait $GO_PID
wait $PYTHON_PID
