# Deploily Backend
 
> A Flask-based backend application with Keycloak identity management, PostgreSQL, and Docker support.
 
---
 
## Table of Contents
 
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Keycloak Configuration](#keycloak-configuration)
- [Database Migrations](#database-migrations)
- [Running the Application](#running-the-application)
- [Email Configuration](#email-configuration)
- [Database Management](#database-management)
- [Troubleshooting](#troubleshooting)
---
 
## Prerequisites
 
Before you begin, make sure you have the following installed:
 
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Python 3.x](https://www.python.org/downloads/)
- A dev container–compatible IDE (e.g. [VS Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers))
---
 
## Getting Started
 
### 1. Set Up the Dev Environment
 
```bash
cd .devcontainer
cp .env.example .env
pre-commit install
```
 
Then open the project in your IDE and reopen it inside the dev container.
 
> **Note:** All subsequent commands assume you are running inside the dev container unless stated otherwise.
 
---
 
## Keycloak Configuration
 
Keycloak is used as the **Identity Provider (IdP)** via **OpenID Connect (OIDC)**. Follow the steps below to configure it for local development.
 
### Access the Admin Console
 
| URL | Description |
|-----|-------------|
| `http://localhost:8080` | Keycloak landing page |
| `http://localhost:8080/admin` | Admin console (direct link) |
 
**Default credentials:** `admin` / `admin` *(or as defined in your Docker environment)*
 
---
 
### Step 1 — Create a Realm
 
1. Log in to the **Keycloak Admin Console**
2. Click **Realms** (top-left dropdown) → **Create Realm**
3. Enter a name (e.g. `myrealm`) and click **Create**
> **What is a realm?** A realm is an isolated namespace in Keycloak that contains its own users, roles, clients, and configuration. Think of it as a tenant.
 
---
 
### Step 2 — Configure the Realm
 
Navigate to your new realm and configure the following sections as needed:
 
| Section | What to Configure |
|---------|-------------------|
| **Authentication** | Password policies, MFA, login flows |
| **Themes** | Customize the login/registration UI |
| **Security Defenses** | Token lifetimes, brute-force protection |
| **Email** | SMTP settings for email verification |
 
---
 
### Step 3 — Create and Configure the Backend Client
 
#### 3.1 — Create the Client
 
1. Go to **Clients** → **Create client**
2. Fill in the following fields:
| Field | Value |
|-------|-------|
| **Client type** | `OpenID Connect` |
| **Client ID** | `deploily` |
 
3. Click **Next**
#### 3.2 — Set Redirect URIs
 
In the **Settings** tab, under **Valid Redirect URIs**, add:
 
```
http://localhost:5000/*
```
 
Then click **Save**.
 
#### 3.3 — Enable Client Authentication & Copy Secret
 
1. In the **Settings** tab, scroll to **Capability config**
2. Toggle **Client authentication** to **On** → click **Save**
3. Navigate to the **Credentials** tab
4. Copy the value under **Client Secret**
#### 3.4 — Add Environment Variables
 
Open your `.env` file and add:
 
```env
KEYCLOAK_CLIENT_ID=deploily
KEYCLOAK_REALM_NAME=myrealm
KEYCLOAK_CLIENT_SECRET=your_client_secret_here
```
 
> **Important:** These values must exactly match what you configured in the Keycloak console.
 
---
 
### Step 4 — Create an Admin User in Keycloak
 
1. In the Keycloak Admin Console, go to **Users** → **Add user**
2. Set the following:
| Field | Value |
|-------|-------|
| **Username** | `admin` |
 
3. Click **Create**, then go to the **Credentials** tab
4. Set the password to `admin` and toggle **Temporary** to **Off**
5. Click **Save password**
---
 
## Database Migrations
 
### Generate a Fernet Key (First Time Only)
 
Run the following from the `src/` directory to generate and export a Fernet encryption key:
 
```bash
cd src
export FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode('utf-8'))")
```
 
> **Tip:** Store this key securely (e.g. in your `.env` file). Losing it means losing access to encrypted data.
 
---
 
### First-Time Setup
 
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```
 
---
 
### After Schema Changes
 
Whenever you modify a SQLAlchemy model, run:
 
```bash
flask db migrate -m "Describe your change here"
flask db upgrade
```
 
---
 
### Resolving Migration History Conflicts
 
If your local migration history diverges from the remote (e.g. after a rebase or branch switch):
 
```bash
# 1. Attempt a migration — note the revision ID in the error output
flask db migrate -m "your message"
 
# 2. Force a specific revision ID
flask db revision --rev-id <revision_id_from_error>
 
# 3. Regenerate and apply
flask db migrate -m "your message"
flask db upgrade
```
 
---
 
## Running the Application
 
```bash
cd src
flask run
```
 
Then open [http://localhost:5000](http://localhost:5000) in your browser.
 
**Login credentials:** `admin` / `admin`
 
---
 
## Email Configuration
 
The app sends transactional emails (new user, subscriptions, support tickets, payments, expiry reminders, etc.) via SMTP. **Nothing is configured by default** — add these to your `.env` before testing anything email-related:
 
```env
export MAIL_HOST="smtp.gmail.com"
export MAIL_PORT="465"
export MAIL_USER="your-email@example.com"
export MAIL_PASS="your-app-password"
export NOTIFICATION_EMAIL="your-email@example.com"
export SUPPORT_EMAIL="your-email@example.com"
```
 
> **Your provider must support port 465 directly.** The code uses `smtplib.SMTP_SSL(...)`, which connects already-encrypted — a provider whose port 465 expects a different handshake will fail to connect. Gmail works well for local dev: enable 2-Step Verification on the account, then generate an [App Password](https://myaccount.google.com/apppasswords) — your normal account password will not work over SMTP.
 
- `NOTIFICATION_EMAIL` — recipient for most internal/admin notifications (new user, payment completed, new subscription, contact-us, etc.)
- `SUPPORT_EMAIL` — recipient specifically for the support-ticket flow (both the "new ticket" and cron-based auto-close/warning admin copies)
- `MAIL_USER` is also used as the visible `From` address on every email — if your provider requires sender verification, make sure this address is verified there.
 
### Editable Email Templates
 
All email subjects/bodies live in the database (`EmailTemplate` model), not in code — editable from the FAB admin panel without a deploy:
 
```
http://localhost:5000/admin/email-template/list
```
 
On a fresh database, seed the initial 24 templates from their default content:
 
```bash
flask seed email-templates
```
(also included in `flask seed all`). This is idempotent — safe to re-run, it only inserts templates that don't already exist.
 
Admins only edit the message content — layout/branding comes from one of three shared MJML skeletons (`src/app/templates/emails/_base*.mjml`), applied automatically per template based on its key (standard branded, payment-receipt style, or plain internal notification).
 
---
 
## Database Management
 
### Access the PostgreSQL Container
 
```bash
docker exec -it deploily-backend-db psql -U postgres -d deploily
```
 
### Useful Queries
 
**List all application users:**
 
```sql
SELECT * FROM ab_user;
```
 
**Update a user's role:**
 
```sql
UPDATE ab_user_role
SET role_id = 2
WHERE user_id = '<user_id>';
```
 
After updating, refresh [http://localhost:5000](http://localhost:5000) to apply the changes.
 
**Role reference:**
 
| `role_id` | Role |
|-----------|------|
| `1` | Viewer |
| `2` | Admin |
 
---
 
# APISIX + Flask (FAB) Integration Guide
 
> Example Service: Open-Meteo Weather API
 
This guide explains how to expose an external API through Apache APISIX, secure it with key-auth, and register it inside a Flask AppBuilder (FAB) application.
 
---
 
## Table of Contents
 
1. [Get the APISIX Admin API Key](#step-1-get-the-apisix-admin-api-key)
2. [Set Environment Variables](#step-2-set-environment-variables)
3. [Create a Service (Example: open-meteo)](#step-3-create-a-service-example-open-meteo)
4. [Register the Service in Flask (FAB)](#step-4-register-the-service-in-flask-fab)
5. [Subscribe to the Service](#step-5-subscribe-to-the-service)
6. [Get an API Token](#step-6-get-an-api-token)
7. [Test the Registered Service](#step-7-test-the-registered-service)
---
 
## Step 1: Get the APISIX Admin API Key
 
The APISIX admin key is defined in the mounted config file on your host machine:
 
```bash
cat .devcontainer/apisix_conf/config.yaml | grep -A3 "admin_key"
```
 
You will see output similar to:
 
```yaml
deployment:
  admin:
    admin_key:
      - name: admin
        key: edd1c9f034335f136f87ad84b625c8f1   # ← this is your APISIX_API_KEY
        role: admin
```
 
---
 
## Step 2: Set Environment Variables
 
Paste the key into your `.env` file:
 
```env
APISIX_API_KEY=edd1c9f034335f136f87ad84b625c8f1
APISIX_ADMIN_URL=http://localhost:9180
```
 
### Port Reference
 
| Port   | Purpose                                              |
|--------|------------------------------------------------------|
| `9180` | Admin API (create routes, upstreams, consumers)      |
| `9080` | Proxy/Gateway (where clients send requests)          |
| `9000` | Dashboard UI                                         |
 
---
 
## Step 3: Create a Service (Example: open-meteo)
 
Each service requires two resources: an **Upstream** and a **Route**.
 
### 3.1 Create the Upstream
 
```bash
curl -X PUT http://localhost:9180/apisix/admin/upstreams/open-meteo-upstream \
  -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "roundrobin",
    "scheme": "http",
    "pass_host": "rewrite",
    "upstream_host": "api.open-meteo.com",
    "nodes": {
      "api.open-meteo.com": 1
    }
  }'
```
 
### 3.2 Create the Route
 
```bash
curl -X PUT http://localhost:9180/apisix/admin/routes/open-meteo \
  -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" \
  -H "Content-Type: application/json" \
  -d '{
    "uri": "/open-meteo/*",
    "plugins": {
      "key-auth": {},
      "cors": {},
      "proxy-rewrite": {
        "regex_uri": ["^/open-meteo/(.*)", "/$1"]
      }
    },
    "upstream_id": "open-meteo-upstream"
  }'
```
 
---
 
## Step 4: Register the Service in Flask (FAB)
 
After the APISIX route is live at `http://localhost:9080/open-meteo`, register it in your Flask app using `ApiSixService` with the following values:
 
| Field              | Value                   |
|--------------------|-------------------------|
| `service_url`      | `http://localhost:9080/open-meteo` |
| `service_name`     | `open-meteo-weather`    |
| `apisix_group_id`  | `open-meteo`            |
 
---
 
## Step 5: Subscribe to the Service
 
Once the service is registered, subscribe to it using the following request:
 
```bash
curl -X POST \
  'http://localhost:5000/api/v1/api-service-subscription/subscribe' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <YOUR_JWT_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "duration": 3,
    "payment_method": "bank_transfer",
    "profile_id": 1,
    "service_plan_selected_id": 1
  }'
```
 
> Replace `<YOUR_JWT_TOKEN>` with your current Bearer token from Keycloak.
 
---
 
## Step 6: Get an API Token
 
After subscribing, retrieve the API token for your subscription (replace `1` with your subscription ID):
 
```bash
curl -X POST \
  'http://localhost:5000/api/v1/api-service-subscription/1/token' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <YOUR_JWT_TOKEN>' \
  -d ''
```
 
> The returned token (e.g. `e1ed3e2909de481e805c2afd6fae3cb4`) is your APISIX consumer `apikey`.
 
---
 
## Step 7: Test the Registered Service
 
Use the API token from the previous step to call the proxied service:
 
```bash
curl "http://localhost:9080/open-meteo/v1/forecast?latitude=36.75&longitude=3.06&current_weather=true" \
  -H "apikey: e1ed3e2909de481e805c2afd6fae3cb4"
```
 
### Example Response
 
```json
{
  "latitude": 36.75,
  "longitude": 3.0625,
  "generationtime_ms": 0.049,
  "utc_offset_seconds": 0,
  "timezone": "GMT",
  "timezone_abbreviation": "GMT",
  "elevation": 64.0,
  "current_weather": {
    "time": "2026-06-24T12:45",
    "interval": 900,
    "temperature": 26.5,
    "windspeed": 8.9,
    "winddirection": 21,
    "is_day": 1,
    "weathercode": 0
  }
}
```
 
---
