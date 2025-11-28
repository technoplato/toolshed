#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <username> <password>"
    exit 1
fi

USER=$1
PASS=$2
ENV_FILE=".env"

if command -v htpasswd &> /dev/null; then
    # Generate hash (no need to escape $ for .env files)
    HASH=$(htpasswd -nb "$USER" "$PASS")
    ESCAPED_HASH="$HASH"
    
    if [ -f "$ENV_FILE" ]; then
        # Check if BASIC_AUTH_USERS exists
        if grep -q "BASIC_AUTH_USERS=" "$ENV_FILE"; then
            # Replace it
            # Note: This is a simple sed, might be brittle with special chars in existing value
            # but sufficient for this specific key.
            sed -i.bak "s|BASIC_AUTH_USERS=.*|BASIC_AUTH_USERS=$ESCAPED_HASH|" "$ENV_FILE"
            echo "Updated BASIC_AUTH_USERS in $ENV_FILE"
        else
            echo "BASIC_AUTH_USERS=$ESCAPED_HASH" >> "$ENV_FILE"
            echo "Appended BASIC_AUTH_USERS to $ENV_FILE"
        fi
    else
        echo "BASIC_AUTH_USERS=$ESCAPED_HASH" > "$ENV_FILE"
        echo "Created $ENV_FILE with BASIC_AUTH_USERS"
    fi
    
    echo "Auth credentials set for user '$USER'."
else
    echo "Error: 'htpasswd' command not found. Please install apache2-utils or similar."
    exit 1
fi
