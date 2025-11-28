#!/bin/bash
set -e

# Configuration
DEPLOY_USER="deploy"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit 1
fi

# Create user if not exists
if id "$DEPLOY_USER" &>/dev/null; then
    echo "User $DEPLOY_USER already exists"
else
    echo "Creating user $DEPLOY_USER..."
    useradd -m -s /bin/bash "$DEPLOY_USER"
fi

# Add to docker group
echo "Adding $DEPLOY_USER to docker group..."
usermod -aG docker "$DEPLOY_USER"

# Setup SSH directory
echo "Setting up SSH directory..."
mkdir -p /home/$DEPLOY_USER/.ssh
chmod 700 /home/$DEPLOY_USER/.ssh
touch /home/$DEPLOY_USER/.ssh/authorized_keys
chmod 600 /home/$DEPLOY_USER/.ssh/authorized_keys
chown -R $DEPLOY_USER:$DEPLOY_USER /home/$DEPLOY_USER/.ssh

echo "==================================================="
echo "Setup complete!"
echo "Now perform the following steps:"
echo "1. Generate an SSH key pair for GitHub Actions (locally): ssh-keygen -t ed25519 -f gh_deploy_key"
echo "2. Add the PUBLIC key (gh_deploy_key.pub) to: /home/$DEPLOY_USER/.ssh/authorized_keys"
echo "   (You can use: echo 'PUBLIC_KEY_CONTENT' >> /home/$DEPLOY_USER/.ssh/authorized_keys)"
echo "3. Add the PRIVATE key (gh_deploy_key) to GitHub Secrets as VPS_SSH_KEY"
echo "4. Add VPS_HOST (IP) and VPS_USER (deploy) to GitHub Secrets"
echo "==================================================="
