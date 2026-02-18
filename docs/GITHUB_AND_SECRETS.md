# Uploading to GitHub and Keeping Secrets Safe

## 1. What **never** to upload (secrets and sensitive info)

These must **not** be committed to GitHub:

| File or content | Why |
|-----------------|-----|
| **`.env`** | Contains API keys (OpenAI, DeepSeek, Gemini), folder IDs, OAuth paths, and possibly paths to key files. |
| **`.env.local`**, **`user.env`** | Same kind of local config. |
| **`credentials_drive_oauth.json`** | OAuth client secret from Google Cloud; anyone with it could impersonate your app. |
| **`token_drive.json`** | OAuth refresh token; gives access to your Google Drive. |
| **Service account JSON** (e.g. `sprint-demo-bot-service-account.json` or any `*service*account*.json`) | Private key for the bot; full access to whatever the service account can do. |

Your **`.gitignore`** is set up to exclude these (and `*.json` in the project root, except `package*.json`). Double-check before the first push.

---

## 2. Checklist before pushing

1. **Confirm sensitive files are ignored**
   ```bash
   git status
   ```
   You should **not** see: `.env`, `user.env`, `credentials_drive_oauth.json`, `token_drive.json`, or any service account `.json` in the project directory.

2. **If the repo was already used and you ever committed `.env` or keys**
   - They are in history. Remove them with `git filter-branch` or BFG, or create a **new** repo and push only the current (clean) tree. Never just delete the file and commit — the old commit still has the secret.

3. **Use `.env.example` as the template**
   - `.env.example` is safe to commit (no real keys, only variable names and placeholders). New clones copy it to `.env` and fill in their own values.

---

## 3. How to upload the project to GitHub

### Option A: New repo from the command line (no existing remote)

1. **Create the repo on GitHub**
   - Go to [github.com/new](https://github.com/new).
   - Name it (e.g. `integration-bots`).
   - Choose Public or Private. Do **not** tick “Add a README” if you already have one locally.
   - Create the repository.

2. **Initialize git (if not already) and push**
   ```bash
   cd /path/to/integration-bots

   git init
   git add .
   git status   # sanity check: no .env, no *.json secrets
   git commit -m "Initial commit: sprint demo automation agent"

   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/integration-bots.git
   git push -u origin main
   ```
   Replace `YOUR_USERNAME` and `integration-bots` with your GitHub username and repo name.

### Option B: Repo already exists and has a remote

```bash
cd /path/to/integration-bots
git status
git add .
git commit -m "Initial commit: sprint demo automation agent"
git push -u origin main
```

### Option C: Push to an existing empty repo (HTTPS vs SSH)

- **HTTPS:** `git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git`
- **SSH:** `git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git`

Use the URL GitHub shows on the repo page (“Code” → “Clone”).

---

## 4. After uploading

- **Clone on another machine:** Copy `.env.example` to `.env` and fill in keys and paths. Do not commit `.env`.
- **CI/CD (e.g. GitHub Actions):** Put secrets in GitHub repo **Settings → Secrets and variables → Actions**, and have the workflow create a `.env` or set env vars from those secrets. Never put real keys in the repo.

---

## 5. If you accidentally pushed a secret

1. **Rotate the secret immediately** (new API key, new OAuth client, new service account key, etc.).
2. **Remove it from history** (e.g. [BFG Repo-Cleaner](https://rsc.io/bfg) or `git filter-repo`) or create a new repo and push again without the secret.
3. Treat the old key as compromised; don’t rely on just deleting the file in the latest commit.
