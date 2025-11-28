#!/bin/bash

# Load environment variables from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "Error: .env file not found. Run ./generate_auth.sh first."
  exit 1
fi

if [ -z "$BASIC_AUTH_USERS" ]; then
  echo "Error: BASIC_AUTH_USERS is not set in .env."
  exit 1
fi

echo "Deploying stack 'my-stack'..."
docker stack deploy -c docker-stack.yml my-stack
