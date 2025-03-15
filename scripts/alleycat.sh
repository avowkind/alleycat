#!/bin/zsh

# Get the path to the virtual environment
VENV_PATH="$HOME/workspace/cursortest/.venv"

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Get input from either argument or stdin
if [ $# -gt 0 ]; then
    query="$1"
else
    query=$(cat)
fi

# Run alleycat with the query and capture output
cd "$HOME/workspace/cursortest"
echo "$query"
echo "$(alleycat "$query" 2>&1)"
