# Slack Alert Agent

A serverless Python agent that monitors your Gmail for Slack notifications and calls your phone (via Telegram) when new alerts arrive. Designed to run on **GitHub Actions** via **Cron-Job.org** triggers.

---

## 🚀 Features

*   **Smart Time Window**: Only alerts you during your configured working hours (e.g., Mon-Fri, 9-6).
*   **Real Phone Calls**: Uses CallMeBot to ring your Telegram, waking you up for urgent issues.
*   **Gmail Integration**: Uses the official Gmail API (OAuth 2.0) for secure and reliable email scanning.
*   **Deduplication**: Remembers what it has already alerted on (persisted via cache), so you don't get spammed.
*   **Zero Cost**: Runs entirely on GitHub Actions' free tier.

---

## 🛠️ Quick Start

### 1. Prerequisites
*   Python 3.11+
*   A Google Cloud Project (for Gmail API)
*   A Telegram account

### 2. Setup (Local)
1.  **Clone the repo**:
    ```bash
    git clone https://github.com/yourusername/slack-alert-agent.git
    cd slack-alert-agent
    ```

2.  **Create environment**:
    ```bash
    # Using Conda
    conda create -p .\.conda python=3.11 -y
    .\.conda\python.exe -m pip install -r requirements.txt
    ```

3.  **Configure Environment**:
    Copy the sample env file and edit it:
    ```bash
    cp .env.sample .env
    ```

4.  **Edit `config.yaml`**:
    Adjust your working hours and timezone:
    ```yaml
    working_hours:
      timezone: "Europe/Kyiv"
      start: "09:00"
      end: "18:00"
    ```

---

## 🔑 Application Setup Guides

### Part A: Gmail API Setup (Step-by-Step)
You need to generate OAuth credentials to allow the agent to read your emails.

1.  **Create a Project**: Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project (e.g., "Slack Alert Agent").
2.  **Enable Gmail API**:
    *   Go to **APIs & Services > Library**.
    *   Search for "Gmail API" and click **Enable**.
3.  **Configure Consent Screen**:
    *   Go to **APIs & Services > OAuth consent screen**.
    *   Select **External** (unless you have a Google Workspace org, then Internal is fine).
    *   Fill in app name and email.
    *   **Scopes**: Add `https://www.googleapis.com/auth/gmail.modify`.
    *   **Test Users**: Add your own Gmail address. **Important**: Without this, you cannot auth.
4.  **Create Credentials**:
    *   Go to **APIs & Services > Credentials**.
    *   Click **Create Credentials > OAuth client ID**.
    *   Application type: **Desktop app**.
    *   Name: "Local Client".
    *   Click **Create**.
    *   Copy the **Client ID** and **Client Secret** into your `.env` file.
5.  **Get Refresh Token**:
    *   Currently, the easiest way is to use a helper script or the Google OAuth playground.
    *   **Quick Tip**: You can use [Google OAuth Playground](https://developers.google.com/oauthplayground/).
        *   Select "Gmail API v1" > `https://www.googleapis.com/auth/gmail.modify`.
        *   Click "Authorize APIs".
    *   **Quick Tip**: You can use [Google OAuth Playground](        *   Copy the **Refresh Token** into your `.env`.

### Part B: Telegram CallMeBot Setup
1.  Open Telegram and search for **@CallMeBot_txtmsg_bot** (or similar based on current CallMeBot docs).
2.  Follow instructions to allow calls.
3.  Simply putting your `@username` in `.env` is usually sufficient for the free tier.

## ⏱️ Scheduling: Running every 5 minutes

GitHub Actions' built-in schedule is unreliable. Use **[Cron-Job.org](https://cron-job.org)** to trigger your workflow reliably via the GitHub API.

1.  **Generate a GitHub Token**:
    *   Go to GitHub Settings > Developer Settings > Personal access tokens > Tokens (classic).
    *   Generate new token > Scopes: `repo` (nothing else needed) > Copy it.
2.  **Create Cron Job**:
    *   Sign up at Cron-Job.org.
    *   Create a NEW job.
    *   **URL**: `https://api.github.com/repos/YOUR_USERNAME/slack-alert-agent/actions/workflows/agent.yml/dispatches` (Replace `YOUR_USERNAME` with your actual username)
    *   **Execution Method**: `POST`
    *   **Headers**:
        *   `Accept: application/vnd.github.v3+json`
        *   `Authorization: Bearer YOUR_GITHUB_TOKEN`
        *   `User-Agent: CronJob`
    *   **Body (JSON)**: `{"ref":"main"}`
    *   **Schedule**: Every 5 minutes.

Now Cron-Job.org will force GitHub to run your script exactly on time!
### Part C: Pushover Setup (Robust Alternative)
1.  **Create Account**: Sign up at [pushover.net](https://pushover.net/).
2.  **Get User Key**: On your dashboard, copy your **User Key**.
3.  **Create Application**:
    *   Click "Create an Application/API Token".
    *   Name: "Slack Alert Agent".
    *   Type: Application.
    *   Copy the **API Token/Key**.
4.  **Add to `.env`**:
    *   `PUSHOVER_USER_KEY`
    *   `PUSHOVER_API_TOKEN`
5.  **Install App**: Download Pushover on your phone and log in.

---

## ⚙️ Advanced Configuration (Notifications)

You can choose how you want to be notified.

### 3. Configure Notifiers
The agent supports **sequential fallback** and **broadcast** strategies. By default, it acts as a persistent alarm.

*   **Pushover (Recommended)**: Set `priority: 2` and `sound: persistent` in `config.yaml` to receive loud, repeating alerts that bypass silent mode.
*   **Env Var Overrides**: You can override working hours in `.env` without changing `config.yaml`:
    ```
    WORKING_HOURS_START=09:00
    WORKING_HOURS_END=17:00
    ```

### Sequential Fallback (Recommended)
Tries to call you via Telegram first; if that fails (e.g., CallMeBot is down), it sends a high-priority Pushover alert.

```yaml
notifications:
  strategy:
    order: ["telegram_call", "pushover"]
    stop_after_success: true
```

### Pushover Only
If you prefer app alerts over phone calls.

```yaml
notifications:
  strategy:
    order: ["pushover"]
```

---

## 🏃‍♂️ Running Locally

Once `.env` is filled:

```powershell
.\.conda\python.exe agent/main.py
```

---

## ☁️ Deploying to GitHub Actions

1.  **Push your code** to a private GitHub repository.
2.  **Set Secrets**:
    Go to **Settings > Secrets and variables > Actions > New repository secret**. Add:
    *   `GMAIL_CLIENT_ID`
    *   `GMAIL_CLIENT_SECRET`
    *   `GMAIL_REFRESH_TOKEN`
    *   `TELEGRAM_USERNAME`
3.  **Enable Workflow**:
    Go to the **Actions** tab and enable the "Slack Alert Agent" workflow.
4.  **Set up Cron-Job.org**: Follow the "Scheduling" section above to start the agent.

---

## 🏗️ Architecture

```text
slack-alert-agent/
├── agent/
│   ├── config/       # Config loader
│   ├── email/        # Gmail client implementation
│   ├── notifier/     # Notification logic
│   ├── state/        # Deduplication state
│   ├── time/         # Time window logic
│   └── main.py       # Entry point
├── config.yaml       # User settings
└── .github/          # CI/CD
```
