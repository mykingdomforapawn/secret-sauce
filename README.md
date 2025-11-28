# secret-sauce

An exploration of standard patterns for managing secrets in Kubernetes, using Vault and the External Secrets Operator.

> **AI Disclaimer:** This project was developed with the assistance of AI tools to guide the learning process, explain concepts, and generate configuration.

---

## Purpose

This project is a practical, hands-on sandbox for understanding modern secrets management in Kubernetes.

The goal is to build a complete, automated setup on a local cluster to explore three primary patterns for securely delivering secrets to applications:

1.  **The Operator Pattern:** An operator (ESO) syncs Vault secrets *to* native Kubernetes `Secret` objects.
2.  **The Agent-Injector Pattern:** A sidecar injects secrets directly into the application pod *without* creating a K8s `Secret`.
3.  **The Dynamic Secrets Pattern:** Vault generates temporary, unique database credentials on-demand for each application instance.

This repository serves as a reproducible base to build, test, and understand these critical workflows.

---

## Core Technologies

This project uses the following open-source tools:

* **Cluster**: **`kind`** (Kubernetes in Docker) for a lightweight, declarative local cluster.
* **Deployment**: **`helmfile`** to manage and deploy all backend components in a single, reproducible command.
* **Secrets Manager**: **`HashiCorp Vault`** deployed in dev-mode as the central "source of truth" for all secrets.
* **Networking**: **`Traefik`** as a modern Ingress controller to expose the demo application.
* **Pattern 1 (Operator)**: **`External Secrets Operator (ESO)`** as the "bridge" component that synchronizes secrets from Vault to Kubernetes.
* **Pattern 2 & 3 (Injector)**: **`Vault Agent Injector`** (deployed with the Vault chart) to enable the sidecar injection pattern.
* **Automation**: A local **Helm Chart** (`/charts/setup`) containing a **Kubernetes Job** to automatically configure Vault (auth, roles, policies, and demo secrets) on every cluster start.
* **Repo Quality**: **`pre-commit`** hooks using **`yamllint`** and **`gitleaks`** for code quality and secret scanning.

---

## Architecture

This project explores three distinct secrets-delivery architectures.

### Pattern 1: The Operator Model (External Secrets)

A central operator polls Vault and translates secrets into native K8s objects.

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

This pattern bypasses Kubernetes `Secret` objects entirely.

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

### Pattern 3: Dynamic Secrets

This pattern extends the Injector model. Instead of reading a static string, Vault generates a new database user for the app.

```text
    [ Vault ] <----(2. Create User)----> [ Database ]
      ^   |
      |   | (3. Return new creds)
      |   v
[ Vault Agent Sidecar ]
      |
      v
 [ /vault/secrets/... ]
      |
      v
  [ App Pod ]
```

---

## Pattern Comparison

| Feature         | Operator (Pattern 1)                                                    | Injector (Pattern 2 & 3)                                                         |
|:----------------|:------------------------------------------------------------------------|:---------------------------------------------------------------------------------|
| **Best For...** | **Legacy / Simple Apps.** Apps that expect Environment Variables.       | **High Security / Dynamic Apps.** Apps that can read files and handle rotation.  |
| **Security**    | **Medium.** Secrets stored in `etcd`. Visible via `kubectl get secret`. | **High.** Secrets exist *only* in the Pod's memory (RAM).                        |
| **Updates**     | **Static.** Requires Pod restart to pick up changes.                    | **Dynamic.** Sidecar updates the file instantly; app can reload without restart. |
| **Complexity**  | **Low.** Standard K8s usage.                                            | **High.** Requires sidecars and file-based config handling.                      |
| **Scale**       | **Efficient.** One operator manages thousands of secrets.               | **Heavy.** Every pod gets a sidecar container.                                   |

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
2.  Builds and loads the app image.
3.  Deploys Vault, Traefik, and ESO via `helmfile`.
4.  Deploys the local `setup` chart which configures Vault via a Job.
5.  Deploys the `secret-reader` app.

```bash
# 1. Create the cluster
kind create cluster --name secret-sauce --config kind-config.yaml

# 2. Build and load the image
docker build -t secret-reader:v1 ./services/secret-reader
kind load docker-image secret-reader:v1 --name secret-sauce

# 3. Deploy
helmfile sync
```

### 5. Verify the Setup

Wait 1-2 minutes for the setup job to complete and the pods to start.

```bash
# Check that the setup job completed
kubectl get pods -n vault -l job-name=vault-setup-job

# Check that the ClusterSecretStore is ready
kubectl get clustersecretstore vault-backend
```

**View the Demo:**
Open **[http://localhost:8081](http://localhost:8081)** in your browser. You should see all three patterns populated with secrets.

---

## Production Readiness Checklist

This project uses several shortcuts for ease of demonstration. **Do not use this configuration in production.**

| Area               | The Shortcut (Demo)                                             | The Production Standard                                                |
|:-------------------|:----------------------------------------------------------------|:-----------------------------------------------------------------------|
| **Vault Mode**     | **Dev Mode:** Unsealed, in-memory storage, single node.         | **HA Mode:** 3+ nodes, Raft storage, Auto-Unseal (AWS/GCP KMS).        |
| **Authentication** | **Root Token:** Used `VAULT_TOKEN=root` in scripts.             | **Least Privilege:** Never use root. Use Terraform to configure Vault. |
| **Configuration**  | **Shell Scripts:** Used `vault write` commands in a Job.        | **Infrastructure as Code:** Use the **Terraform Vault Provider**.      |
| **Secret Zero**    | **Hardcoded:** Postgres password plain text in `helmfile.yaml`. | **Existing Secrets:** Create K8s secrets out-of-band (e.g., SOPS).     |
| **Traffic**        | **HTTP:** Plain text traffic within the cluster.                | **mTLS:** Enable TLS on Vault and use Cert-Manager for Ingress.        |
| **Database**       | **Ephemeral:** Data lost on restart.                            | **Persistent:** Use PVCs or a managed cloud database (RDS/CloudSQL).   |

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

**To rebuild:** Run the commands in Step 4 ("Deploy the Full Stack") again.

---

## Project Roadmap

* [x] **Step 1: Cluster Setup**
  * Configured a reproducible `kind` cluster (`kind-config.yaml`).
* [x] **Step 2: Repo Quality**
  * Added `pre-commit` hooks for `yamllint` and `gitleaks`.
* [x] **Step 3: Deploy Core Backends**
  * Used `helmfile` to deploy Vault, Traefik, and ESO.
* [x] **Step 4: Automate Vault Setup**
  * Created local `setup` Helm chart.
  * Created a `Job` (`vault-setup-job`) to autoconfigure Vault auth, roles, and policies.
  * Configured the Database Secrets Engine for dynamic credentials.
* [x] **Step 5: Pattern 1 - Operator Model**
  * Created `ExternalSecret` manifest to request `secret/my-app/config`.
  * Verified app reads the K8s `Secret` via env vars.
* [x] **Step 6: Pattern 2 - Injector Model**
  * Configured app deployment with Vault Agent annotations.
  * Verified app reads secrets from `/vault/secrets`.
* [x] **Step 7: Pattern 3 - Dynamic Secrets**
  * Configured Vault to generate on-demand Postgres credentials.
  * Verified app receives unique, short-lived database credentials.
