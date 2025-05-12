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

# Check if the Go binary exists
if [ ! -f "bin/server" ]; then
    # Check if Go is on the PATH
    if ! command -v go &> /dev/null; then
        echo "Go is not installed. Please install Go to run this script."
        exit 1
    fi
    # Build the Go server
    echo "Building Go server..."
    go build -o bin src/web_engine/server.go
    if [ $? -ne 0 ]; then
        echo "Failed to build Go server. Please check the Go code for errors."
        exit 1
    fi
    echo "Go server built successfully."
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
