#!/bin/bash

# Load variables from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi

# Ensure SS_API_KEY is set
if [ -z "$SS_API_KEY" ]; then
  echo "SS_API_KEY is not set in the .env file!"
  exit 1
fi

# API endpoint and paper ID
PAPER_ID="649def34f8be52c8b66281af98ae884c09aef38b"
URL="https://api.semanticscholar.org/graph/v1/paper/$PAPER_ID"

# Perform the curl request
curl -H "x-api-key: $SS_API_KEY" "$URL"