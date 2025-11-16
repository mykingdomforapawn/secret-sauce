# secret-sauce

An exploration of standard patterns for managing secrets in Kubernetes, using Vault and the External Secrets Operator.

> **AI Disclaimer:** This project was developed with the assistance of Google's Gemini to guide the learning process, explain concepts, and generate configuration.

---

## Purpose

This project is a practical, hands-on sandbox for understanding modern secrets management in Kubernetes.

The goal is to build a complete, automated setup on a local cluster to explore the two primary patterns for securely delivering secrets to applications:

1.  **The Operator Pattern:** An operator (ESO) syncs Vault secrets *to* native Kubernetes `Secret` objects.
2.  **The Agent-Injector Pattern:** A sidecar injects secrets directly into the application pod *without* creating a K8s `Secret`.

This repository serves as a reproducible base to build, test, and understand these two critical workflows.

---

## Core Technologies

This project uses the following open-source tools:

* **Cluster**: **`kind`** (Kubernetes in Docker) for a lightweight, declarative local cluster.
* **Deployment**: **`helmfile`** to manage and deploy all backend components in a single, reproducible command.
* **Secrets Manager**: **`HashiCorp Vault`** deployed in dev-mode as the central "source of truth" for all secrets.
* **Networking**: **`Traefik`** as a modern Ingress controller to expose the demo application.
* **Pattern 1 (Operator)**: **`External Secrets Operator (ESO)`** as the "bridge" component that synchronizes secrets from Vault to Kubernetes.
* **Pattern 2 (Injector)**: **`Vault Agent Injector`** (deployed with the Vault chart) to enable the sidecar injection pattern.
* **Automation**: A local **Helm Chart** (`/charts/setup`) containing a **Kubernetes Job** to automatically configure Vault (auth, roles, policies, and demo secrets) on every cluster start.
* **Repo Quality**: **`pre-commit`** hooks using **`yamllint`** and **`gitleaks`** for code quality and secret scanning.

---

## Architecture

This project explores two distinct secrets-delivery architectures.

### Pattern 1: The Operator Model (External Secrets)

This is the primary focus of the setup so far. A central operator polls Vault and translates secrets into native K8s objects.

```text
  [ Vault ]
 (secret/data/...)
      ^
      | (3. Pulls Secret)
      |
[ External Secrets Operator ]
      |
      | (2. Reads Instructions)
      v
 [ ExternalSecret (CRD) ]
      |
      | (4. Creates/Updates)
      v
 [ K8s Secret (Base64) ]
      |
      | (5. Mounts as Env Var)
      v
  [ App Pod ]
```

### Pattern 2: The Agent-Injector Model (Sidecar)

This pattern (the next step) bypasses Kubernetes `Secret` objects entirely.

```text
    [ Vault ]
 (secret/data/...)
      ^
      | (2. Auth & Request)
      |
[ Vault Agent Sidecar ] <----(1. Pod starts, Webhook injects)
      |
      | (3. Writes to in-mem Volume)
      v
 [ /vault/secrets/... ]
      |
      | (4. Reads from file)
      v
  [ App Pod ]
```

---

## How to Run Locally

This guide will get the entire *infrastructure* running on your local machine.

### 1. Prerequisites

* **Docker Desktop**: Must be installed and running.
* **Python 3**: For `pre-commit` and `venv`.
* **Homebrew** (or other package manager) for installing CLIs.

### 2. Install Tools

Install all necessary command-line tools.

```bash
brew install kind kubectl helm helmfile pre-commit
```

**Highly Recommended:** `helmfile` requires the `helm-diff` plugin to run.
```bash
helm plugin install [https://github.com/databus23/helm-diff](https://github.com/databus23/helm-diff)
```

### 3. Clone and Set Up the Repository

```bash
git clone [https://github.com/YOUR_USERNAME/secret-sauce.git](https://github.com/YOUR_USERNAME/secret-sauce.git)
cd secret-sauce
```

Create a virtual environment and install Python tools:
```bash
# Create and activate the venv
python3 -m venv .venv
source .venv/bin/activate

# Install tools
pip install pre-commit yamllint

# Install the Git pre-commit hooks
pre-commit install
```

### 4. Deploy the Full Stack (Cluster + Apps)

This single command does everything:
1.  Creates the `kind` cluster (using `kind-config.yaml`).
2.  Deploys Vault, Traefik, and ESO via `helmfile`.
3.  Deploys the local `setup` chart.
4.  The `vault-setup-job` runs and automatically figures all Vault auth, roles, policies, and demo secrets.

```bash
# This is the only command you need
helmfile sync
```

### 5. Verify the Setup

Wait 1-2 minutes for the setup job to complete, then check:

```bash
# Check that the setup job completed
kubectl get pods -n vault -l job-name=vault-setup-job

# Check that the ClusterSecretStore is ready
kubectl get clustersecretstore vault-backend
```

Both should show `Completed` and `Ready`, respectively.

---

## How to Tear Down

You can destroy the entire setup with two commands:

1.  **Delete all Helm releases:**
    ```bash
    helmfile destroy
    ```
2.  **Delete the local cluster:**
    ```bash
    kind delete cluster --name secret-sauce
    ```

**To rebuild:** Just run `helmfile sync` again.

---

## Project Roadmap

* [x] **Step 1: Cluster Setup**
    * Configured a reproducible `kind` cluster (`kind-config.yaml`).
* [x] **Step 2: Repo Quality**
    * Added `pre-commit` hooks for `yamllint` and `gitleaks`.
* [x] **Step 3: Deploy Core Backends**
    * Used `helmfile` to deploy all components.
    * `HashiCorp Vault` (dev-mode)
    * `Traefik` (Ingress)
    * `External Secrets Operator (ESO)`
* [x] **Step 4: Automate Vault Setup**
    * Created local `setup` Helm chart.
    * Created a `Job` (`vault-setup-job`) to run all config on start.
    * Job enables K8s auth, creates policies, roles, and a demo secret (`secret/my-app/config`).
    * Chart deploys the `ClusterSecretStore` to link ESO to Vault.
* [ ] **Step 5: Phase 1 - Operator Model**
    * [ ] Build "secret-reader" demo app.
    * [ ] Create a local Helm chart for the app.
    * [ ] Create `ExternalSecret` manifest to request `secret/my-app/config`.
    * [ ] Deploy app and verify it reads the K8s `Secret` (via env vars).
* [ ] **Step 6: Phase 2 - Injector Model**
    * [ ] Re-configure app chart to use Vault agent annotations.
    * [ ] Remove the `ExternalSecret` manifest.
    * [ ] Deploy app and verify it reads the secret directly from `/vault/secrets`.
