# VPS Setup & Docker Stack Deployment Guide (Secure Edition)

This guide provides precise instructions to set up a VPS (specifically tailored for Hetzner) and deploy applications using Docker Stack with **secure authentication**.

**Video Reference:** [Watch on YouTube](https://youtu.be/fuZoxuBiL9o)

---

## 1. Provisioning the VPS (Hetzner)

1.  **Create an Account** on [Hetzner Cloud](https://console.hetzner.cloud/).
2.  **Create a Project** (e.g., "Toolshed").
3.  **Add Server**:
    *   **Image**: **Ubuntu 24.04**.
    *   **Type**: **CPX11** (approx €4/mo).
    *   **SSH Key**: **Crucial**. Add your local machine's public key.
    *   **Name**: `vps-01`.
4.  **Create & Buy**.

---

## 2. Initial Server Setup

SSH into your new server:
```bash
ssh root@<YOUR_VPS_IP>
```

### Secure the Server
1.  **Update**: `apt update && apt upgrade -y`
2.  **Firewall**:
    ```bash
    ufw allow OpenSSH
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw enable
    ```

---

## 3. Installing Docker Engine

**Video Timestamp:** [08:31](https://youtu.be/fuZoxuBiL9o?t=511)

Run on VPS:
```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add repo:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker:
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

---

## 4. Remote Management (Docker Context)

**Video Timestamp:** [09:41](https://youtu.be/fuZoxuBiL9o?t=581)

Run on **LOCAL** machine:
1.  **Create Context**:
    ```bash
    docker context create vps-01 --docker "host=ssh://root@<YOUR_VPS_IP>"
    ```
2.  **Use Context**:
    ```bash
    docker context use vps-01
    ```

---

## 5. Enable Docker Swarm

**Video Timestamp:** [10:43](https://youtu.be/fuZoxuBiL9o?t=643)

Run on **VPS** (or via context):
```bash
docker swarm init
```

---

## 6. Secure Deployment

We use a `.env` file to store credentials so they are not hardcoded in the stack file.

### Step 6.1: Generate Secure Auth
Run this on your **local machine**. Replace `<user>` and `<password>` with your desired credentials.
**IMPORTANT**: Choose a strong password. This is the gatekeeper for your services.

```bash
./generate_auth.sh myuser mysecretpassword
```
This will create (or update) a `.env` file with the hashed password.

### Step 6.2: Deploy
Run the deployment script from your **local machine** (with `vps-01` context active):

```bash
./deploy.sh
```
This script loads the `.env` variables and runs `docker stack deploy`.

---

## 7. Verification

1.  **Check Services**:
    ```bash
    docker service ls
    ```
2.  **Test Access**:
    Open `http://<YOUR_VPS_IP>` in your browser.
    *   You should be prompted for credentials.
    *   Enter the user/password you generated in Step 6.1.
    *   You should see the "whoami" container details.
    *   **Note**: The Traefik dashboard is also available at `http://<YOUR_VPS_IP>/dashboard/` and is protected by the same credentials.

---

## 8. Using Templates

I have included templates for **Python FastAPI** and **Bun Express** in the `templates/` directory.

### To use a template:
1.  **Build & Push**: You need a container registry (Docker Hub, GHCR, etc.).
    ```bash
    cd templates/python-fastapi
    docker build -t your-username/fastapi-app:latest .
    docker push your-username/fastapi-app:latest
    ```
2.  **Add to Stack**:
    Copy the service definition from `templates/README.md` into `docker-stack.yml`.
3.  **Redeploy**:
    ```bash
    ./deploy.sh
    ```
