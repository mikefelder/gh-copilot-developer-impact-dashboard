# Demo User Configuration

This document explains how to configure demo user credentials for read-only Grafana dashboard access.

## Overview

The deployment creates a demo user with **Viewer** (read-only) role that can access all Grafana dashboards, including the "Developer Activity vs Copilot Usage" dashboard.

## Default Credentials

If not configured, the following default credentials are used:
- **Username:** `demo-user`
- **Password:** `dem0-passw0rd`

## Configuration Methods

### 1. Azure Developer CLI (azd) Deployment

Set the credentials using `azd` environment variables before deployment:

```bash
azd env set DEMO_USER_USERNAME "your-demo-username"
azd env set DEMO_USER_PASSWORD "your-secure-password"
```

Then deploy:

```bash
azd deploy
```

Or provision (if first time):

```bash
azd provision
```

### 2. GitHub Actions CI/CD (Future)

For GitHub Actions workflows, configure the credentials as repository secrets:

1. Go to your repository **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:
   - `DEMO_USER_USERNAME`: Your desired username
   - `DEMO_USER_PASSWORD`: Your desired password

The workflow will automatically use these secrets during deployment.

#### Example GitHub Actions Workflow Configuration

```yaml
- name: Deploy Infrastructure
  run: azd provision --no-prompt
  env:
    AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
    AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
    AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
    DEMO_USER_USERNAME: ${{ secrets.DEMO_USER_USERNAME }}
    DEMO_USER_PASSWORD: ${{ secrets.DEMO_USER_PASSWORD }}
```

## How It Works

1. **Python Script**: The `update_grafana.py` script reads credentials from environment variables:
   - `DEMO_USER_USERNAME` (falls back to `demo-user`)
   - `DEMO_USER_PASSWORD` (falls back to `dem0-passw0rd`)

2. **Infrastructure**: The Bicep templates:
   - Store credentials securely in Azure Key Vault
   - Pass them to the `update-grafana` container job as environment variables

3. **User Creation**: The update-grafana job:
   - Creates the demo user with Viewer role if it doesn't exist
   - Updates the password if the user already exists

## Security Considerations

- Demo user has **read-only** access (Viewer role)
- Credentials are stored securely in Azure Key Vault
- Passwords are passed as secure parameters in Bicep
- Consider using strong, unique passwords for production environments

## Accessing Grafana

After deployment, the demo user can log in at the Grafana URL with the configured credentials.

You can find your Grafana URL with:

```bash
azd env get-values | grep GRAFANA_DASHBOARD_URL
```

Or retrieve stored credentials from Key Vault:

```bash
# Get the Key Vault name
KEYVAULT_NAME=$(az keyvault list --resource-group $(azd env get-values | grep AZURE_RESOURCE_GROUP | cut -d'=' -f2 | tr -d '"') --query "[0].name" -o tsv)

# Retrieve demo user credentials
az keyvault secret show --vault-name $KEYVAULT_NAME --name demo-user-username --query value -o tsv
az keyvault secret show --vault-name $KEYVAULT_NAME --name demo-user-password --query value -o tsv
```
