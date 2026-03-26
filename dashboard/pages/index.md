---
title: Risk Analytics Dashboard
---

<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=JetBrains+Mono:wght@400;500&family=Source+Sans+3:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap');

  :root {
    --ivory: #FDF8F0;
    --card-bg: #FFFFFF;
    --border: #E8E0D4;
    --divider: #D4C9B8;
    --text-primary: #1A1A1A;
    --text-body: #3D3832;
    --text-muted: #8C8279;
    --fraud-red: #C23D2E;
    --safe-teal: #2B6B5E;
    --amber: #D4890A;
    --steel-blue: #4A7FB5;
    --grid-line: #EDE6DA;
  }

  body, .app-shell {
    background-color: var(--ivory) !important;
    font-family: 'Source Sans 3', sans-serif !important;
    color: var(--text-body) !important;
  }

  h1, h2, h3 {
    font-family: 'DM Serif Display', serif !important;
    color: var(--text-primary) !important;
    font-weight: 400 !important;
  }

  .header-block {
    padding: 36px 0 24px;
    border-bottom: 1px solid var(--divider);
    margin-bottom: 32px;
  }

  .header-block h1 {
    font-size: 34px;
    line-height: 1.15;
    margin: 0 0 8px;
    letter-spacing: -0.01em;
  }

  .header-subtitle {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    color: var(--text-muted);
    margin: 0;
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 40px;
  }

  .kpi-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 20px 20px 20px 17px;
    position: relative;
  }

  .kpi-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    border-radius: 2px 0 0 2px;
  }

  .kpi-card.red::before   { background: var(--fraud-red); }
  .kpi-card.teal::before  { background: var(--safe-teal); }
  .kpi-card.amber::before { background: var(--amber); }
  .kpi-card.blue::before  { background: var(--steel-blue); }

  .kpi-label {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 0 0 8px;
  }

  .kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 36px;
    font-weight: 500;
    color: var(--text-primary);
    line-height: 1;
    margin: 0 0 6px;
  }

  .kpi-context {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 13px;
    color: var(--text-muted);
    margin: 0;
  }

  .section-rule {
    border: none;
    border-top: 1px solid var(--divider);
    margin: 40px 0 32px;
  }

  .section-heading {
    font-family: 'DM Serif Display', serif !important;
    font-size: 22px !important;
    color: var(--text-primary) !important;
    margin: 0 0 6px !important;
  }

  .section-sub {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 14px;
    color: var(--text-muted);
    margin: 0 0 20px;
  }

  .two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 8px;
  }

  .panel {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 20px;
  }

  .panel-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 0 0 16px;
  }

  .chart-note {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 12px;
    font-style: italic;
    color: var(--text-muted);
    margin-top: 8px;
  }

  .footer-rule {
    border: none;
    border-top: 1px solid var(--divider);
    margin: 48px 0 0;
  }

  .footer-text {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 12px;
    color: var(--text-muted);
    padding: 16px 0 24px;
    display: flex;
    justify-content: space-between;
  }

  .ai-narration {
    background: #FAFAF7;
    border: 1px solid var(--border);
    border-left: 3px solid var(--text-muted);
    border-radius: 2px;
    padding: 16px 20px;
    margin: 20px 0 8px;
  }

  .ai-label {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 0 0 8px;
  }

  .ai-text {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: var(--text-body);
    margin: 0;
    font-style: italic;
  }

  .ai-footer {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 11px;
    color: var(--text-muted);
    margin: 8px 0 0;
  }
</style>

<div class="header-block">
  <h1>Financial Risk Intelligence</h1>
  <p class="header-subtitle">IEEE-CIS Fraud Detection Analysis — 590,540 E-Commerce Transactions · Vesta Corporation</p>
</div>

<div class="kpi-grid">
  <div class="kpi-card blue">
    <p class="kpi-label">Transactions Analyzed</p>
    <p class="kpi-value"><Value data={kpis} column=total_txns fmt='#,##0'/></p>
    <p class="kpi-context">Full dataset</p>
  </div>
  <div class="kpi-card red">
    <p class="kpi-label">Overall Fraud Rate</p>
    <p class="kpi-value"><Value data={kpis} column=fraud_rate_pct fmt='0.00%'/></p>
    <p class="kpi-context"><Value data={kpis} column=fraud_txns fmt='#,##0'/> transactions flagged</p>
  </div>
  <div class="kpi-card amber">
    <p class="kpi-label">Fraud Exposure</p>
    <p class="kpi-value">$<Value data={kpis} column=fraud_amt_m fmt='0.0"M"'/></p>
    <p class="kpi-context">of $<Value data={kpis} column=total_amt_m fmt='0.0"M"'/> total volume</p>
  </div>
  <div class="kpi-card teal">
    <p class="kpi-label">Highest Risk Segment</p>
    <p class="kpi-value"><Value data={top_risk_segment} column=segment/></p>
    <p class="kpi-context"><Value data={top_risk_segment} column=fraud_rate_pct fmt='0.00%'/> fraud rate</p>
  </div>
</div>

{#if narration && narration.length > 0 && narration[0].executive_summary}
<div class="ai-narration">
  <p class="ai-label">AI-Generated Summary — verify against data above</p>
  <p class="ai-text">{narration[0].executive_summary}</p>
  <p class="ai-footer">Generated {narration[0].generated_at} · {narration[0].data_period}</p>
</div>
{/if}

<hr class="section-rule"/>

<h2 class="section-heading">Daily Fraud Activity</h2>
<p class="section-sub">Transaction volume and fraud rate across the observation period</p>

<LineChart
  data={daily}
  x=txn_date
  y={["fraud_txns", "total_txns"]}
  yAxisTitle="Transactions"
  colorPalette={["#C23D2E", "#2B6B5E"]}
  fillOpacity=0.15
  lineWidth=2
/>

<p class="chart-note">Fraud rate averaged {(kpis[0].fraud_rate_pct * 100).toFixed(2)}% across the observation period. Daily series shows fraudulent transactions (red) against total volume (teal).</p>

<hr class="section-rule"/>

<h2 class="section-heading">Fraud Distribution by Category</h2>
<p class="section-sub">Fraud rate and transaction volume across product codes and card types</p>

<div class="two-col">
  <div class="panel">
    <p class="panel-title">By Product Code</p>
    <BarChart
      data={by_product}
      x=product_cd
      y=fraud_rate_pct
      yAxisTitle="Fraud Rate %"
      yFmt='0.00%'
      colorPalette={["#C23D2E"]}
      swapXY=true
      labels=true
    />
  </div>
  <div class="panel">
    <p class="panel-title">By Card Type</p>
    <BarChart
      data={by_card}
      x=card_type
      y=fraud_rate_pct
      yAxisTitle="Fraud Rate %"
      yFmt='0.00%'
      colorPalette={["#4A7FB5"]}
      swapXY=true
      labels=true
    />
  </div>
</div>

{#if narration && narration.length > 0 && narration[0].risk_highlights}
<div class="ai-narration">
  <p class="ai-label">AI-Generated Analysis — verify against charts above</p>
  <p class="ai-text">{narration[0].risk_highlights} {narration[0].segment_analysis}</p>
</div>
{/if}

<hr class="section-rule"/>

<h2 class="section-heading">Transaction Profile</h2>
<p class="section-sub">Fraud patterns by device type and product-level statistics</p>

<div class="two-col">
  <div class="panel">
    <p class="panel-title">By Device Type</p>
    <BarChart
      data={by_device}
      x=device_type
      y=fraud_rate_pct
      yAxisTitle="Fraud Rate %"
      yFmt='0.00%'
      colorPalette={["#7B6B8A"]}
      swapXY=true
      labels=true
    />
  </div>
  <div class="panel">
    <p class="panel-title">Product Code Summary</p>
    <DataTable
      data={by_product}
      rows=10
    >
      <Column id=product_cd title="Product" />
      <Column id=total_txns title="Total Txns" fmt='#,##0' />
      <Column id=fraud_txns title="Fraud Txns" fmt='#,##0' />
      <Column id=fraud_rate_pct title="Fraud Rate" fmt='0.00%' contentType=colorscale colorScale=negative />
      <Column id=avg_txn_amt title="Avg Amt $" fmt='$#,##0.00' />
    </DataTable>
  </div>
</div>

<hr class="section-rule"/>

<h2 class="section-heading">Risk by Transaction Size</h2>
<p class="section-sub">Fraud rate across amount buckets — higher-value transactions show elevated risk</p>

<BarChart
  data={amount_buckets}
  x=amount_bucket
  y=fraud_rate_pct
  yAxisTitle="Fraud Rate %"
  yFmt='0.00%'
  colorPalette={["#D4890A"]}
  labels=true
/>

<p class="chart-note">Amount buckets: low (&lt;$50), medium ($50–$500), high ($500–$5,000), very_high (&gt;$5,000).</p>

<hr class="section-rule"/>

<h2 class="section-heading">Data Sources</h2>
<p class="section-sub">Queries powering this dashboard, sourced from BigQuery <code>production</code> dataset</p>

#### Daily Trend

<DataTable data={daily} rows=5/>

#### By Product Code

<DataTable data={by_product}/>

#### By Card Type

<DataTable data={by_card}/>

#### By Device Type

<DataTable data={by_device}/>

#### Amount Buckets

<DataTable data={amount_buckets}/>

---

```sql daily
select
  dimension_value as txn_date,
  total_txns,
  fraud_txns,
  fraud_rate_pct,
  total_amt,
  fraud_amt
from bigquery.risk_summary
where summary_type = 'daily'
order by txn_date
```

```sql by_product
select
  dimension_value as product_cd,
  total_txns,
  fraud_txns,
  fraud_rate_pct,
  avg_txn_amt
from bigquery.risk_summary
where summary_type = 'product_cd'
order by fraud_rate_pct desc
```

```sql by_card
select
  dimension_value as card_type,
  total_txns,
  fraud_txns,
  fraud_rate_pct
from bigquery.risk_summary
where summary_type = 'card_type'
order by fraud_rate_pct desc
```

```sql by_device
select
  dimension_value as device_type,
  total_txns,
  fraud_txns,
  fraud_rate_pct
from bigquery.risk_summary
where summary_type = 'device_type'
order by fraud_rate_pct desc
```

```sql kpis
select
  sum(total_txns)                                                  as total_txns,
  round(sum(fraud_txns) / sum(total_txns), 6)                      as fraud_rate_pct,
  sum(fraud_txns)                                                  as fraud_txns,
  round(sum(fraud_amt) / 1000000, 2)                               as fraud_amt_m,
  round(sum(total_amt) / 1000000, 2)                               as total_amt_m
from bigquery.risk_summary
where summary_type = 'daily'
```

```sql top_risk_segment
select
  dimension_value as segment,
  fraud_rate_pct
from bigquery.risk_summary
where summary_type = 'product_cd'
order by fraud_rate_pct desc
limit 1
```

```sql amount_buckets
select * from bigquery.amount_buckets
```

```sql narration
select * from narration.summary
```

<div class="footer-rule"></div>
<div class="footer-text">
  <span>Source: IEEE-CIS Fraud Detection Dataset, Vesta Corporation</span>
  <span>Built with Evidence.dev · BigQuery · DataTalksClub DE Zoomcamp</span>
</div>
