# Deploying the Dashboard to Vercel

The Evidence.dev dashboard deploys as a static site. Vercel pulls sources from BigQuery at build time, compiles to plain HTML/CSS/JS, and serves the result with no runtime dependencies.

**Suggested project name / URL:** `risk-intel` → `https://risk-intel.vercel.app`

---

## Prerequisites

- GitHub repo pushed to remote
- GCP service account key file at `credentials/pipeline-sa-key.json` (created by Terraform)

---

## Step 1 — Generate a Vercel-ready `.env` file

Run this command from the project root. It builds a single `.env.vercel` file with all required variables — including the GCP credentials minified to one line:

```bash
python3 -c "
import json, os
key = json.dumps(json.load(open('credentials/pipeline-sa-key.json')))
llm_key = open('.env').read().split('LLM_API_KEY=')[1].split()[0] if 'LLM_API_KEY=' in open('.env').read() else 'your_llm_api_key'
lines = [
    f'GOOGLE_CREDENTIALS={key}',
    f'LLM_API_KEY={llm_key}',
    'LLM_BASE_URL=https://api.deepseek.com',
    'LLM_MODEL=deepseek-chat',
]
open('.env.vercel', 'w').write('\n'.join(lines))
print('Written to .env.vercel')
"
```

The output file `.env.vercel` will look like:

```
GOOGLE_CREDENTIALS={"type":"service_account","project_id":"financial-risk-control-system",...}
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

> `.env.vercel` is gitignored (it contains secrets). Never commit it.

Add it to `.gitignore` if not already there:
```bash
echo ".env.vercel" >> .gitignore
```

---

## Step 2 — Push Latest Code to GitHub

```bash
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

`GOOGLE_CREDENTIALS` must be added **individually** — its value contains `=` signs (inside the base64-encoded private key) that confuse bulk import parsers and cause truncation. The other 3 variables are safe to bulk import.

### 4a — Add GOOGLE_CREDENTIALS individually

1. In the **Environment Variables** section, click **Add**
2. **Key**: `GOOGLE_CREDENTIALS`
3. **Value**: paste the single-line JSON output of:

```bash
python3 -c "import json; print(json.dumps(json.load(open('credentials/pipeline-sa-key.json'))))"
```

Paste the full output into the **Value** field only (not the key name).

### 4b — Bulk import the remaining 3 variables

Create a trimmed file without `GOOGLE_CREDENTIALS`:

```bash
grep -v "^GOOGLE_CREDENTIALS=" .env.vercel > .env.vercel.rest
```

Then paste the contents of `.env.vercel.rest` into the **Key** field — Vercel will auto-split these correctly:

```
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

> **Why separate?** The `private_key` in the service account JSON contains many `=` characters (base64 padding). Vercel's bulk importer splits on `=`, so the JSON gets corrupted mid-value — which is why `client_email` goes missing.

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
