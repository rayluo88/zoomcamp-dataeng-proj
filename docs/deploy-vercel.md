# Deploying the Dashboard to Vercel

The Evidence.dev dashboard deploys as a static site. Vercel pulls sources from BigQuery at build time, compiles to plain HTML/CSS/JS, and serves the result with no runtime dependencies.

**Suggested project name / URL:** `risk-intel` → `https://risk-intel.vercel.app`

---

## Prerequisites

- GitHub repo pushed to remote
- GCP service account key file at `credentials/pipeline-sa-key.json` (created by Terraform)

---

## Step 1 — Prepare the Service Account Credentials

Vercel needs the GCP service account key as an environment variable (not a file).

Copy the entire JSON content of your service account key:

```bash
cat credentials/pipeline-sa-key.json
```

Keep this copied — you'll paste it into Vercel in Step 4.

---

## Step 2 — Push Latest Code to GitHub

Ensure `connection.yaml` (now using `service-account-key`) and updated `package.json` are committed and pushed:

```bash
git add dashboard/sources/bigquery/connection.yaml dashboard/package.json
git commit -m "configure BigQuery service account auth for Vercel deployment"
git push
```

---

## Step 3 — Create a New Vercel Project

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **Add New → Project**
3. Import your GitHub repository (`zoomcamp-dataeng-proj`)
4. On the **Configure Project** screen:
   - **Framework Preset**: Other
   - **Root Directory**: click **Edit** → set to `dashboard`
   - **Build Command**: `npm run build` *(already set in `package.json` to run sources + build)*
   - **Output Directory**: `build`
   - **Install Command**: `npm install`

---

## Step 4 — Add Environment Variables

Still on the Configure Project screen, scroll to **Environment Variables** and add:

| Name | Value |
|---|---|
| `GOOGLE_CREDENTIALS` | *(paste the full JSON content from Step 1)* |
| `LLM_API_KEY` | *(your DeepSeek API key, for narration regeneration)* |
| `LLM_BASE_URL` | `https://api.deepseek.com` |
| `LLM_MODEL` | `deepseek-chat` |

> The `LLM_*` variables are only needed if you want Vercel to regenerate narration on each deploy. If you pre-generate `dashboard/sources/narration/summary.csv` locally and commit it, you can skip these.

---

## Step 5 — Set a Shorter Domain Name

Before deploying:

1. On the **Configure Project** screen, click the project name field at the top
2. Change the name from the auto-generated one to **`risk-intel`**
   - Vercel will check availability — if taken, try `risk-intel-dashboard` or `fraud-risk-intel`
3. Click **Deploy**

The final URL will be `https://risk-intel.vercel.app`.

---

## Step 6 — Deploy

Click **Deploy**. Vercel will:

1. Clone the repo, `cd` to `dashboard/`
2. Run `npm install`
3. Run `npm run build` → which runs `evidence sources` (pulls BigQuery data using the service account) then `evidence build` (compiles to static HTML)
4. Serve the `build/` directory

Build takes ~2–3 minutes. You'll see the live URL when it completes.

---

## Updating the Dashboard

Each `git push` to `main` triggers a Vercel redeploy automatically — pulling fresh data from BigQuery and rebuilding.

To manually trigger a redeploy without a code change: Vercel Dashboard → your project → **Deployments** → **Redeploy**.

---

## Local Dev After This Change

`npm run dev` continues to work (Evidence.dev uses cached source data).

To run `npm run sources` locally (refresh BigQuery data), set `GOOGLE_CREDENTIALS` in your `.env` file:

```bash
# Generate a single-line JSON string from the key file
python3 -c "import json; print(json.dumps(json.load(open('credentials/pipeline-sa-key.json'))))"
```

Paste the output as `GOOGLE_CREDENTIALS=...` in `.env`. Evidence.dev picks it up automatically.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `Error: GOOGLE_CREDENTIALS not set` | Check env var name is exact — no trailing spaces |
| `Invalid JSON in credentials` | Re-paste the key; ensure no line breaks were introduced |
| `BigQuery: Access Denied` | Service account needs `roles/bigquery.dataViewer` + `roles/bigquery.jobUser` on the project |
| Build timeout | Evidence.dev default build timeout is 5 min; Vercel hobby allows up to 45 min — should be fine |
| Narration source missing | Commit `dashboard/sources/narration/summary.csv` or add LLM env vars so Vercel generates it |
