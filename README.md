# 🗺️ Google Maps Scraper (Leads Sniper) — Agent Skill

This project is a portable, zero-touch Google Maps scraping skill designed for the **Hermes Desktop** AI Agent framework. It automates B2B lead generation via the bundled **Leads Sniper** local server, allowing you to extract leads directly into local CSV files and automatically upload them to **Google Sheets**.

---

## 📋 Prerequisites

Before installing, make sure your computer has the following requirements ready:

1. **Google Chrome Browser**: Installed and running on your system.
2. **Leads Sniper Chrome Extension**: Installed in Google Chrome.
3. **Leads Sniper API Key**: Active and copied from the extension side panel.
4. **Hermes Desktop Application**: Installed on your system.
5. **Python 3.8 or newer**: Installed and added to your system's `PATH`.
6. **Node.js (v22.22.0 or newer)**: Required to run `npx skills` installation commands (Note: Hermes Agent requires Node >= 22.22.0).

---

## 🚀 Quick Install via `skills.sh`

[skills.sh](https://www.skills.sh/) is the package manager and registry for AI Agent skills (used by Claude Code, Cursor, Hermes, Copilot, etc.). You can install this skill automatically in your agent's environment using the CLI.

### Option 1: Global Symlink Installation (Recommended)
This installs the skill globally in your home directory using the **symlink** method (allowing automatic updates). 

To force the `skills` CLI to create a symbolic link (symlink) on Windows, target both `hermes-agent` and `claude-code` (targeting a single agent defaults to copying the files instead of symlinking):
```bash
npx skills add https://github.com/leads-sniper/google-maps-scraper-leads-sniper-agents --skill google-maps-scraping --agent hermes-agent --agent claude-code --global --yes
```

### Option 2: Interactive Installation
To customize the installation scope and method step-by-step:
```bash
npx skills add https://github.com/leads-sniper/google-maps-scraper-leads-sniper-agents --skill google-maps-scraping
```
During the prompt:
1. Select **Global** as the installation scope.
2. Select both **Hermes Agent** and **Claude Code** to ensure the symlink method is used.

---

## 🛠️ Manual Installation (Hermes Desktop)

If you are not using `skills.sh` or wish to install the skill manually onto your Hermes installation, follow these steps:

### Step 1: Copy the Skill Folder
Move or copy the `google-maps-scraping` directory to your local Hermes skills folder:
```cmd
# Windows File Explorer Path (paste this in your address bar):
%LOCALAPPDATA%\hermes\skills\google-maps-scraping
```

---

## ⚙️ Step-by-Step Configuration Guide

Once the files are in place, you need to configure the API credentials and storage paths. 

### Step 1: Run the Interactive Setup Wizard
Run the setup wizard directly from your terminal using the copy-pasteable command that matches your installation:

*   **If running directly from the cloned workspace root**:
    Double-click **`setup.bat`** (on Windows) or run:
    ```bash
    python setup.py
    ```
    *(The root script automatically detects the skill's location and runs the setup wizard).*

*   **If installed via `skills.sh` globally (Recommended)**:
    Run the script using the system home path:
    ```bash
    # Windows (CMD):
    python %USERPROFILE%\.agents\skills\google-maps-scraping\scripts\setup.py

    # Windows (PowerShell):
    python $HOME\.agents\skills\google-maps-scraping\scripts\setup.py

    # macOS & Linux (Terminal):
    python3 ~/.agents/skills/google-maps-scraping/scripts/setup.py
    ```

*   **If installed manually in Hermes AppData**:
    Run the script using the local AppData path:
    ```bash
    # Windows (CMD):
    python %LOCALAPPDATA%\hermes\skills\google-maps-scraping\scripts\setup.py

    # Windows (PowerShell):
    python $env:LOCALAPPDATA\hermes\skills\google-maps-scraping\scripts\setup.py

    # macOS & Linux (Terminal):
    python3 ~/.hermes/skills/google-maps-scraping/scripts/setup.py
    ```

The script will guide you through the following configurations:
1.  **API Base URL**: The local address where your scraping server runs. (Press **Enter** to keep the default `http://127.0.0.1:8787`).
2.  **API Token**: Get this token from your Leads Sniper Chrome extension's side panel.
3.  **Local Server Path**: The wizard automatically detects the bundled `server/local-api.exe` inside the skill directory.
4.  **Storage Directory**: Where all downloaded CSV scrapes and execution history are stored (default: `~/Hermes_Scrapes`).
5.  **Telegram Bot Token**: (Optional) Used if you want to receive notifications and interact via Telegram.
6.  **Google Workspace Setup**: (Optional) Connects your Google Sheets account to upload scrape results automatically.

---

## 📊 Google Sheets Integration (Optional)

To enable automatic uploading of scraped leads to Google Sheets, you need to set up Google Workspace API access:

1.  **Create OAuth Credentials**:
    *   Go to the [Google Cloud Console Credentials Page](https://console.cloud.google.com/apis/credentials).
    *   Click **Create Credentials** → **OAuth 2.0 Client ID**.
    *   Select **Desktop app** as the Application Type, name it, and click **Create**.
    *   **Download the client secret JSON file**.
2.  **Enable APIs**:
    *   Enable the [Google Sheets API](https://console.developers.google.com/apis/api/sheets.googleapis.com/overview).
    *   Enable the [Google Drive API](https://console.developers.google.com/apis/api/drive.googleapis.com/overview).
3.  **Authenticate**:
    *   During `setup.py`, enter the path to the downloaded `client_secret.json` when prompted.
    *   Open the generated URL in your browser, log in to your Google Account, authorize the application, and copy the final redirect URL.
    *   Paste the redirect URL back into the terminal wizard to complete authentication.

---

## 💬 Optimizing Hermes Chat Settings

To prevent the agent from spamming your chat window with raw terminal command progress or internal reasoning loops, run these two commands in your Hermes terminal:

```bash
hermes config set display.tool_progress false
hermes config set display.show_reasoning false
```
*This keeps your agent conversations clean, presenting only final results and readable updates.*

---

## 🗺️ How to Use the Scraping Skill

Once everything is configured, start a new session in your Hermes Desktop App or Telegram Bot interface:

1.  Start a fresh session:
    ```
    /new
    ```
2.  Load the skill:
    ```
    load google maps scraping skill
    ```
3.  *(Optional)* Bring up the interactive control panel buttons (if using Telegram):
    ```
    show menu of google maps scraping skill
    ```
4.  Start scraping by telling the agent what you are looking for:
    ```
    scrap for dentist in new york
    ```
    *Or use the Telegram Menu buttons:*
    *   `🗺️ Scrape Maps`: Prompts you for a keyword and location.
    *   `📊 View Last CSV`: Previews the first 10-15 rows of your most recent scrape.
    *   `🗂️ List All Scrapes`: Shows your historical scrapes with Google Sheets links.
    *   `❓ Help`: Shows help instructions.

---

## 📂 Project Structure

Here is how the skill folder is structured:
```
google-maps-scraping/
├── SKILL.md                          # Main instructions for the AI Agent
├── config.json                       # Local configurations (created by setup.py)
├── server/
│   └── local-api.exe                 # Bundled Leads Sniper API server
├── scripts/
│   ├── lib.py                        # Common libraries and helpers
│   ├── setup.py                      # Interactive setup wizard
│   ├── server.py                     # Controls server start/stop/status
│   ├── upload_csv_to_sheets.py       # Uploads scraped CSVs to Google Sheets
│   ├── run_scrape.py                 # Background scraping runner
│   └── telegram_menu.py              # Draws Telegram keyboard buttons
└── references/                       # Technical documentations and spec files
```

---

## ⚠️ Troubleshooting & Warnings

> [!WARNING]
> **Multi-Tenant VPS Usage**
> You cannot share one VPS or PC with multiple people running this skill simultaneously, as the local server runs on a single port (`8787`) and relies on active browser resources.

> [!IMPORTANT]
> **401 Unauthorized Error**
> If your scrapes suddenly fail with a `401 Unauthorized` message, it means the API token has expired or rotated. To fix this:
> 1. Open the Leads Sniper Chrome extension.
> 2. Copy the active API key.
> 3. Re-run `python scripts/setup.py` or edit the token directly in `config.json`.

> [!TIP]
> **Windows Emojis Crash**
> To avoid crashes in Windows Command Prompt, the scripts use safe ASCII representations (`+`, `!`, `x`) in terminal outputs. Emojis are only displayed directly in the chat client.
