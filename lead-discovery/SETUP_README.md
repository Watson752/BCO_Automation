# BCO Version 1 — Ottawa Tech Lead Discovery

## Included files

- `BCO_Tech_Sponsor_Lead_List_V1.xlsx`
- `BCO_V1_Directory_Sources_to_Google_Sheets.n8n.json`
- `BCO_V1_Google_Maps_to_Google_Sheets.n8n.json`
- `.env.example`

## Scope

This version only creates and maintains a company-level lead list. It does **not** find individual employees, enrich personal contact details, draft emails, or send outreach.

## 1. Create the Google Sheet

1. Upload `BCO_Tech_Sponsor_Lead_List_V1.xlsx` to Google Drive.
2. Open it with Google Sheets.
3. Keep these tab names unchanged:
   - `Master Leads`
   - `Raw - Directories`
   - `Raw - Google Maps`
4. Copy the spreadsheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`

## 2. Create the Apify credential

1. Create or open the BCO Apify account.
2. Copy the API token from Apify Console.
3. Put the token and spreadsheet ID in the environment used by n8n.

Example Docker Compose fragment:

```yaml
environment:
  - APIFY_TOKEN=${APIFY_TOKEN}
  - BCO_GOOGLE_SHEET_ID=${BCO_GOOGLE_SHEET_ID}
  - N8N_BLOCK_ENV_ACCESS_IN_NODE=false
```

Restart the n8n container after changing environment variables.

## 3. Import the workflows

In n8n:

1. Open **Workflows**.
2. Choose **Import from File**.
3. Import both `.n8n.json` files.
4. Open every Google Sheets node and reconnect it to the BCO Google OAuth credential.
5. Confirm the document and target tab names.

The included placeholder credential ID will not work until the nodes are reconnected.

## 4. Test the directory workflow

Run:

`BCO V1 - Directory Sources to Google Sheets`

It calls Apify Web Scraper once for each of:

- Kanata North BA member directory
- Invest Ottawa companies
- Ottawa Board of Trade technology directory

The workflow:

1. Writes extracted rows to `Raw - Directories`.
2. Applies a technology keyword filter.
3. Upserts technology-relevant companies into `Master Leads` using `Dedup Key`.
4. Sets source-specific flags and source URLs.

### Expected review

- Invest Ottawa records should generally pass the technology filter.
- Kanata North contains non-technology businesses, so review the filtered output.
- Directory websites can change their page structure. If a source returns zero or malformed rows, open the Actor input in Apify development mode and update that source's page function.

## 5. Test the Google Maps workflow

Run:

`BCO V1 - Google Maps Tech Leads to Google Sheets`

The default input runs six searches:

- software companies
- artificial intelligence companies
- cybersecurity companies
- cloud computing companies
- telecommunications companies
- robotics companies

Each search is capped at 20 places, for a theoretical maximum of 120 raw results.

The workflow deliberately disables:

- contact enrichment
- reviews
- images
- place-detail pages
- directory-inside-place scraping
- web-result enrichment

This keeps the first run small and cost-controlled.

## 6. Review the master list

In `Master Leads`:

1. Mark obvious duplicates.
2. Reject businesses with weak technology relevance.
3. Complete the four 1–5 scores:
   - BCO Relevance
   - Sponsorship Capacity
   - Ottawa Presence Score
   - Community Signal
4. Use the calculated Priority Score to rank the list.
5. After the first successful run, copy `Date Last Verified` into `Date First Found` as values for new rows.

## Known limitation

The importable workflows are configured with live-site extraction logic but were not executed against your Apify account or your Google Sheet. Website DOM changes, n8n version differences, or credential settings may require a small node or selector adjustment during the first test.
