# Dashboard Design — Financial Risk Intelligence

## Aesthetic Direction

**"Broadsheet Analytical"** — The visual authority of a Financial Times data page crossed with the precision of a Bloomberg terminal, rendered on warm newsprint-ivory. This is a data briefing, not a SaaS product. Every element earns its space.

---

## Color Palette

| Role | Hex | Rationale |
|---|---|---|
| Page background | `#FDF8F0` | Warm ivory — editorial newsprint feel, not sterile white |
| Card background | `#FFFFFF` | Clean white, slight contrast against ivory |
| Card/panel border | `#E8E0D4` | Warm stone, not cold gray |
| Section dividers | `#D4C9B8` | Muted khaki rule lines |
| Primary text | `#1A1A1A` | Near-black, maximum authority |
| Body text | `#3D3832` | Warm dark brown, softer than pure black |
| Muted / labels | `#8C8279` | Warm gray for captions and axis labels |
| Fraud accent | `#C23D2E` | "Economist red" — authoritative, not alarming |
| Safe / volume | `#2B6B5E` | Deep teal-green, institutional |
| Highlight | `#D4890A` | Amber-gold, FT-style callout color |
| Steel blue | `#4A7FB5` | Secondary categorical color |
| Plum | `#7B6B8A` | Tertiary categorical color |
| Chart gridlines | `#EDE6DA` | Nearly invisible warm grid |

---

## Typography

All fonts from Google Fonts, chosen for character not ubiquity.

| Role | Font | Rationale |
|---|---|---|
| Section headings | **DM Serif Display** | Serif display fonts are rare in dashboards — signals seriousness and editorial gravitas |
| KPI numbers | **JetBrains Mono** | Monospace keeps numbers aligned; feels authoritative for financial data |
| Body, labels, captions | **Source Sans 3** | Highly readable workhorse; not overused like Inter/Roboto |

Avoided: Inter, Roboto, Arial, Space Grotesk — all generic SaaS defaults.

---

## Layout

Single-page scrolling layout, 1120px max-width, centered.

```
Header (title + subtitle)
────────────────────────────
KPI Strip  [4 cards in a row]
────────────────────────────
Temporal Tile   [full width]   ← REQUIRED
Daily fraud trend (line chart)
────────────────────────────
Categorical Tile  [2-column]   ← REQUIRED
  Product Code  |  Card Type
  (horizontal bar charts)
────────────────────────────
Transaction Profile  [2-column]
  Device Type   |  Data Table
────────────────────────────
Amount Distribution  [full width]
Fraud rate by transaction size
────────────────────────────
Footer (source attribution)
```

---

## Signature Details

### KPI Card Left-Border
Each KPI card has a **3px colored left-border** — borrowed from editorial pull-quote styling. Colors: steel blue (volume), Economist red (fraud rate), amber (exposure), teal (top segment). This small motif creates visual rhythm without decoration.

### Chart Rules
- **Horizontal bars** for categorical data — gives label text room to breathe vs cramped vertical bars
- **Horizontal gridlines only** — never vertical; color `#EDE6DA`
- **Square bar corners** — no rounded bars (rounded = playful SaaS; square = financial data)
- **No legend boxes** — color-coded panel titles instead
- **No chart borders or boxes** — charts float on white card backgrounds
- **Axis lines**: bottom (x-axis) only, `1px #D4C9B8`; Y-axis has no line

### What Makes This Distinctive
1. Warm ivory background instead of pure white — immediate editorial feel
2. Serif display headings in a dashboard context — unusual, signals seriousness
3. Monospace numbers — perfect alignment, financial authority
4. "Economist red" (`#C23D2E`) — a specific editorial red, not a generic Material red
5. No icons, no gradients, no illustrations — the data IS the design

---

## Data Sources

All data from BigQuery `financial-risk-control-system.production`:

| Query | Source table | Filter | Powers |
|---|---|---|---|
| `daily` | `mart_risk_summary` | `summary_type = 'daily'` | Temporal tile + KPI totals |
| `by_product` | `mart_risk_summary` | `summary_type = 'product_cd'` | Product bar chart + data table |
| `by_card` | `mart_risk_summary` | `summary_type = 'card_type'` | Card type bar chart |
| `by_device` | `mart_risk_summary` | `summary_type = 'device_type'` | Device type bar chart |
| `amount_buckets` | `fct_transactions` | `GROUP BY amount_bucket` | Amount distribution chart |
| `kpis` | `mart_risk_summary` | `summary_type = 'daily'` aggregate | KPI cards |
| `top_risk_segment` | `mart_risk_summary` | `summary_type = 'product_cd'` | Highest-risk KPI card |

---

## Tech Stack

- **Evidence.dev** — SQL-first BI framework, compiles to static site
- **BigQuery connector** — `@evidence-dev/bigquery`, gcloud-cli auth
- **Deployment** — Vercel (static site, free tier, public URL for peer review)
