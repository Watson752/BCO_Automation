# BCO Automation

Automation and research for [Builders Collective Ottawa](https://builderscollective.ca/) sponsor and community outreach.

The repo has three event-specific pieces:

1. **Local n8n for Ottawa.** A self-hosted [n8n](https://n8n.io/) instance for Ottawa automation. The Grokbot workflows run here. The Snapchat EasyLens workbook does not.
2. **V1 lead list for the Grokbot event.** Two n8n workflows and `BCO_Tech_Sponsor_Lead_List_V1.xlsx`. They build a company-level sponsor list from Ottawa public directories and Google Maps.
3. **Toronto sponsor workbook for Snapchat EasyLens.** Research notes, scored shortlists, and `Snapchat_EasyLens_Toronto_Sponsor_Leads.xlsx` for the EasyLens × Snapchat workshop on November 12, 2026.

Company-level discovery and sponsor research live here. Sending mail does not. Workflows stop at a sheet or workbook. Email drafts follow `BCO_Drafting_Instructions.md`, and a send happens only when someone explicitly asks for the Grokbot V1 list.

## Repository layout

| Path | What it is |
| --- | --- |
| `compose.yaml` | Ottawa n8n service. Binds to `127.0.0.1:5678` and reads secrets from a root `.env`. |
| `lead-discovery/` | Grokbot V1 workflows and sheet template, plus the Snapchat EasyLens research CSVs and workbook builder. V1 setup steps are in `lead-discovery/SETUP_README.md`. |
| `research_notes/` | Source notes behind the Snapchat EasyLens shortlists (AI, company, and creator tracks). |
| `reports/` | The three finished Snapchat EasyLens shortlist write-ups. |
| `Recovered KNBA and Invest Ottawa files/` | Earlier Kanata North Business Association and Invest Ottawa exports. The workbook builder checks new domains against `bco_researched_master.csv` and `bco_master_leads_checkpoint.csv`. |
| `BCO_Drafting_Instructions.md` | Voice, structure, and send rules for outreach drafts. |
| `local-files/` | Host folder mounted into n8n at `/files`. Gitignored. |

## Ottawa n8n

You need Docker and an [Apify](https://apify.com/) API token. The Grokbot workflows also need a Google Sheet created from the V1 workbook.

```bash
cp lead-discovery/.env.example .env
```

Fill in the root `.env`. Compose also expects these variables, which are not in the example file:

```bash
N8N_ENCRYPTION_KEY=   # long random string; keep it stable so saved credentials still decrypt
GENERIC_TIMEZONE=America/Toronto
TZ=America/Toronto
APIFY_TOKEN=
BCO_GOOGLE_SHEET_ID=
```

Then:

```bash
docker compose up -d
```

Open `http://127.0.0.1:5678`. After any `.env` change, restart the container so n8n picks up the new values. `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` is set in Compose so workflow expressions can read `$env.APIFY_TOKEN` and `$env.BCO_GOOGLE_SHEET_ID`.

Do not commit `.env`. Tokens and the encryption key stay on the machine that runs n8n.

## Grokbot event lead list (V1)

These workflows run on the Ottawa n8n instance. They only build the Grokbot sponsor list. They do not feed the Snapchat EasyLens workbook.

Full click-by-click setup, including the Google Sheet tabs and credential reconnect, is in [`lead-discovery/SETUP_README.md`](lead-discovery/SETUP_README.md).

Import both workflows from `lead-discovery/`, then reconnect every Google Sheets node to the BCO Google credential. The credential id baked into the JSON is a placeholder.

| Workflow | What a manual run does |
| --- | --- |
| `BCO V1 - Directory Sources to Google Sheets` | Scrapes Kanata North BA, Invest Ottawa companies, and the Ottawa Board of Trade technology directory through Apify Web Scraper. Appends raw rows to `Raw - Directories`, filters for technology relevance, and upserts into `Master Leads` on `Dedup Key`. |
| `BCO V1 - Google Maps Tech Leads to Google Sheets` | Runs six Ottawa searches (software, AI, cybersecurity, cloud, telecommunications, robotics), 20 places each. Appends raw rows to `Raw - Google Maps` and upserts the same master tab. Reviews, images, place-detail pages, and contact enrichment are off so the first run stays small. |

Upload `lead-discovery/BCO_Tech_Sponsor_Lead_List_V1.xlsx` to Google Drive and open it as a Sheet first. Leave the tab names as `Master Leads`, `Raw - Directories`, and `Raw - Google Maps`. Put that spreadsheet id in `BCO_GOOGLE_SHEET_ID`.

After a run, score `Master Leads` by hand: BCO Relevance, Sponsorship Capacity, Ottawa Presence, and Community Signal. Priority Score is calculated from those. Directory page structure changes; if a source comes back empty, update that source’s page function in the workflow.

These workflows collect public company records. They do not look up employees or personal inboxes.

## Snapchat EasyLens sponsor workbook

This track is separate from the Ottawa n8n instance and the Grokbot V1 list. `lead-discovery/build_toronto_sponsor_workbook.py` turns the `lead-discovery/research_*.csv` files into `lead-discovery/Snapchat_EasyLens_Toronto_Sponsor_Leads.xlsx` for the November 12, 2026 EasyLens × Snapchat workshop at the Snapchat Toronto office.

It keeps one row per domain, drops excluded or duplicate domains, scores fit, Toronto presence, capacity, contactability, and speed, and writes four sheets: `Sponsor Leads`, `Methodology`, `Event Brief`, and `Excluded & Duplicates`. A successful run asserts 75 unique domains, split into tiers A (1–20), B (21–50), and C (51–75).

```bash
python3 -m pip install openpyxl
python3 lead-discovery/build_toronto_sponsor_workbook.py
```

The research CSVs are the inputs. The `Snapchat_EasyLens_Toronto_Sponsor_Leads*.csv` files are exports of that workbook for Drive and Google Sheets. Narrative shortlists, each capped at 18 companies with a published company-owned email, are in:

- `reports/Toronto company sponsors.md`
- `reports/Toronto AI sponsor candidates.md`
- `reports/Toronto creator sponsor candidates.md`

Supporting notes sit in the matching folders under `research_notes/`.

## Outreach drafts

`BCO_Drafting_Instructions.md` is the source of truth for voice, links, personalization, and which list may be sent.

Keep the lists separate:

- **BCO Master Leads 2.0** is draft-only. Create Gmail drafts. Do not send.
- **Grokbot V1 list** (`BCO_Tech_Sponsor_Lead_List_V1`) is drafted the same way, and sent only when explicitly asked.
- **Snapchat EasyLens** uses the Toronto workbook. Draft from that list only when asked. It is not the Grokbot sheet.

Before drafting a batch, check Gmail sent history for each recipient. Row order and the `Drafted?` column are not reliable; that column is not written back.
