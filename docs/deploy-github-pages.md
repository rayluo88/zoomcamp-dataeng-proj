# Deploying the Dashboard to GitHub Pages

The Evidence.dev dashboard deploys as a static site via GitHub Actions. On every push to `main`, the workflow pulls fresh data from BigQuery, builds the static site, and publishes it to GitHub Pages.

**Live URL**: `https://rayluo88.github.io/zoomcamp-dataeng-proj/`

---

## How It Works

```
git push → GitHub Actions → npm run build → upload artifact → GitHub Pages
                                 │
                          evidence sources   ← authenticates to BigQuery
                          evidence build     ← compiles to static HTML/CSS/JS
```

---

## Setup

### Step 1 — Enable GitHub Pages

In your repo: **Settings → Pages → Source → GitHub Actions**

### Step 2 — Add Repository Secrets

**Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|---|---|
| `GOOGLE_CREDENTIALS` | Full content of `credentials/pipeline-sa-key.json` (single-line JSON) |
| `LLM_API_KEY` | Your DeepSeek / OpenAI API key |

Generate the single-line JSON:
```bash
python3 -c "import json; print(json.dumps(json.load(open('credentials/pipeline-sa-key.json'))))"
```

### Step 3 — Push

The workflow at `.github/workflows/deploy.yml` triggers automatically on push to `main`.

---

## Lessons Learned: GCP Credentials in CI/CD

### The Problem

GCP service account keys are JSON objects containing a `private_key` field whose value is a base64-encoded RSA key — for example:

```json
{
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAK...AQAB\n-----END RSA PRIVATE KEY-----\n"
}
```

The base64 content includes many `=` characters (padding). This causes silent corruption in multiple platforms:

| Platform | Failure mode |
|---|---|
| **Vercel bulk import** | Splits on `=` inside the value → JSON truncated, `client_email` missing |
| **YAML variable substitution** (`credentials: '${GOOGLE_CREDENTIALS}'`) | YAML parser or the connector re-parses the string → same truncation |
| **Any `KEY=VALUE` env file parser** | `=` inside values is ambiguous without proper quoting |

The symptom is always the same: `The incoming JSON object does not contain a client_email field` — meaning the JSON was received and parsed, but it arrived corrupted.

### The Fix: Write to a File First

Instead of passing the entire JSON as an environment variable string, write it to a temporary file and point `GOOGLE_APPLICATION_CREDENTIALS` at the file path. GCP's auth libraries read this path natively:

```yaml
- name: Set up GCP credentials
  run: |
    echo '${{ secrets.GOOGLE_CREDENTIALS }}' > /tmp/gcp-key.json
    echo "GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json" >> $GITHUB_ENV
```

This works because:
- `echo '...' > file` writes the raw secret bytes without interpretation
- Single quotes prevent shell variable expansion and special character issues
- `GOOGLE_APPLICATION_CREDENTIALS` is the standard GCP ADC mechanism — all GCP client libraries respect it automatically

### connection.yaml: Use `gcloud-cli` Authenticator

With the file-based approach, switch Evidence.dev's BigQuery connection to use `gcloud-cli` (which reads ADC) instead of `service-account-key` (which requires the JSON string inline):

```yaml
# dashboard/sources/bigquery/connection.yaml
name: bigquery
type: bigquery
options:
  project_id: your-project-id
  location: your-region
  authenticator: gcloud-cli   # reads GOOGLE_APPLICATION_CREDENTIALS automatically
```

This also works for local development — set `GOOGLE_APPLICATION_CREDENTIALS=./credentials/pipeline-sa-key.json` in `.env` and `npm run sources` authenticates identically.

### Why This Applies to Any CI/CD Platform

This pattern solves the credential problem on **any** platform:
- **Vercel**: write key to file in build command, set `GOOGLE_APPLICATION_CREDENTIALS`
- **Netlify**: same approach in `netlify.toml` build command
- **GitHub Actions**: as shown above
- **Cloud Run / Docker**: mount the key file as a volume or secret, set the env var

The root cause is always the same — `=` signs in base64 content break text-based parsers. The solution is always the same — treat the JSON as a file, not a string.

---

## Security Notes

- GitHub Actions secrets are never exposed in build logs (GitHub masks them automatically)
- The API key is used only at **build time** — it is never embedded in the deployed static site
- The `/tmp/gcp-key.json` file exists only for the duration of the Actions runner and is discarded after the job completes
