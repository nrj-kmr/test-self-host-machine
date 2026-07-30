# GitHub Actions Self-Hosted Runner Setup Guide

## 🛠️ Detailed Step-by-Step Implementation

### Step 1: Generate Authentication Tokens (GitHub UI)

1. Navigate to your GitHub Repository -> **Settings** -> **Actions** -> **Runners**.
2. Click on **New self-hosted runner** and select **Linux** as the Runner Image.
3. Keep the browser tab open to copy the uniquely generated token script.

---

### Step 2: Provision the Runner Agent (Remote Server)

SSH into your target deployment machine and execute the configuration sequence inside a clean directory:

```bash
# Create and enter the runner directory
mkdir actions-runner && cd actions-runner

# Download the runner package (URL obtained from Step 1 - GitHub Page)
curl -o actions-runner-linux-x64-2.335.1.tar.gz -L https://github.com/actions/runner/releases/download/v2.335.1/actions-runner-linux-x64-2.335.1.tar.gz

# Extract the package
tar xzf ./actions-runner-linux-x64-2.335.1.tar.gz

# Initialize configuration and connect to GitHub
./config.sh --url https://github.com/<owner>/<repo> --token <YOUR_REGISTRATION_TOKEN>
```

---

### Step 3: Establish a Persistent Background Service (Remote Server)

To ensure the runner survives shell disconnections, terminal closures, or system reboots, install it as a system service:

```Bash
# Github will say to run
./run.sh # run this command if you run the service in foreground only

# else run these if you want to run it indefinitely as background sercice👇

# Install the systemd configuration hooks
sudo ./svc.sh install

# Trigger the service execution
sudo ./svc.sh start
```

---

### 🔍 Monitoring & Health Checks (Service Status)

To audit whether your self-hosted instance is actively listening for automated triggers or if it has crashed (dead), connect to the server and execute the standard service management commands:

Check Status

```Bash
# Inspect the runner service health on Linux server
sudo systemctl status actions.runner.*
```

- Expected Active State: Look for Active: active (running) highlighted in green.

- Expected Dead State: If you notice Active: inactive (dead), the service requires manual intervention.

---

### Lifecycle Recovery Management

```Bash
# To start the runner service if it is stopped/dead
sudo ./svc.sh start

# To stop the runner service
sudo ./svc.sh stop

# To restart the runner process after environment changes
sudo ./svc.sh restart
```

### 🚀 Routing Pipelines to the Custom Infrastructure (Local Repo)

Modify your pipeline workflow definition file located inside your local repository path (.github/workflows/your-pipeline.yml). Change the target executor constraint by updating the runs-on parameters:

```YAML
name: CI CD Production Pipeline

on:
  push:
    branches: [ "main" ]

jobs:
  deploy:
    # Route job execution away from default hosted machines to your registered runner
    runs-on: [self-hosted, Linux] 

    steps:
      - name: Fetch Codebase
        uses: actions/checkout@v4

      - name: Deploy Application Steps
        run: |
          echo "Executing native builds directly inside custom instance infrastructure..."
          npm run build
```

---

### ⚠️ Essential Prerequisites

Unlike GitHub-hosted infrastructure, Self-Hosted environments do not come pre-packaged with language runtimes.

- Ensure necessary binaries (Node.js, Docker, Python, Java, etc.) are pre-installed globally on the host server.

- Ensure the system user running the runner agent has explicit permissions to execute target automation actions (e.g., Docker group socket permissions).

---

### Guide: Where to run specific commands

Here is a quick reference for where each command needs to be executed and what it accomplishes:

| Environment / Location | Command / Action | Purpose |
| :--- | :--- | :--- |
| **GitHub Browser UI** | Settings -> Actions -> Runners -> New self-hosted runner | Generates the unique registration token and downloads URLs. |
| **Remote Server (EC2 via SSH)** | `mkdir actions-runner && cd actions-runner` | Creates a dedicated workspace directory for the runner agent. |
| **Remote Server (EC2 via SSH)** | `curl -o ...` & `tar xzf ...` | Downloads and extracts the official GitHub Runner binaries. |
| **Remote Server (EC2 via SSH)** | `./config.sh --url <repo_url> --token <token>` | Authenticates and registers the machine with your GitHub Repository. |
| **Remote Server (EC2 via SSH)** | `sudo ./svc.sh install` | Registers the runner agent as a permanent system service. |
| **Remote Server (EC2 via SSH)** | `sudo ./svc.sh start` | Starts the runner execution loop in the background. |
| **Local Code Repository** | Update `runs-on: [self-hosted, Linux]` in `.github/workflows/*.yml` | Routes target pipeline jobs to your custom infrastructure. |

---
