#!/bin/bash

# Format all Markdown files in the project using Prettier

# Check if Prettier is installed
if ! command -v prettier &> /dev/null
then
    echo "Prettier is not installed. Installing..."
    npm install -g prettier
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Format all .md files
find . -name "*.md" -exec prettier --write {} \;

echo "Markdown files formatted successfully."