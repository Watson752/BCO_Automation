# BCO Cold-Outreach Drafting Instructions

Reference prompt for drafting cold-outreach emails on behalf of Builders Collective Ottawa (BCO). Reconstructed from prior drafting sessions — update this file directly if the rules change rather than re-pasting a fresh prompt each time.

## Account & source sheets

- Gmail account: `builderscollectiveottawa@gmail.com`
- **BCO Master Leads 2.0** — Sheet ID `1JEOMQJVeKDaWyRtknQ_WsaXi05nxhmiPxPksKaPLIfE`, ~999 rows. Drafting-only list, processed in row-range batches (e.g. rows 1-50, 51-100, 101-200...).
- **BCO_Tech_Sponsor_Lead_List_V1** — Sheet ID `1rBqW6rUkCQ58auMSdoXn66iYsKQz3R76d6s0GHZY8j8`. Separate, smaller sponsorship list that gets drafted **and** sent on explicit request — don't conflate with Master Leads 2.0.

## Hard rules

- **Draft only — never send.** Use `create_draft`, never `send_message`, for Master Leads 2.0 batches. Only the V1 sponsor list gets sent, and only when the user explicitly asks.
- **Don't trust row position or the `Drafted?` column** to determine what's already been contacted — the sheet gets re-sorted/edited between runs, and `Drafted?` is never actually written back to (always `FALSE`). Before drafting a batch, cross-check each recipient email against Gmail sent history (`search_threads`, grouped `to:` queries, `in:sent`).
- Don't create duplicate drafts for a company already drafted/sent in an earlier batch.

## Email structure

1. **Opening sentence** — "Hey, we're reaching out from Builders Collective Ottawa, a community of 360+ builders in the city." Hyperlink "Builders Collective Ottawa" to `https://builderscollective.ca/`.
2. **Proof point** — reference the recent fully booked Cursor meetup (vary the phrasing draft-to-draft).
3. **Personalization paragraph** — one paragraph connecting the specific company's work to BCO's members, built from that row's `Personalization_Hook` / `Description` / `Fit_Reason` columns (real prior research, not guesses). Must pass the **swap test**: if you swapped in a different company's name, would the paragraph still make sense? If yes, it's too generic — rewrite it. Avoid banned filler phrases: "we came across", "we noticed", "caught our attention", and similar. No em/en dashes used as sentence breaks.
4. **Booking line** — "If it's easier to just grab time directly, here's our booking link: " followed by the Calendly URL as both link text and href: `https://calendly.com/builderscollectiveottawa-otr1/30min?month=2026-09`.
5. **Signature** — "Srivathsan Murali," / "+1 343 254 0823" / "Outreach Lead" / "Builders Collective Ottawa" (hyperlinked again to `https://builderscollective.ca/`).

Every link (both occurrences of "Builders Collective Ottawa" and the Calendly line) must be wrapped in an actual `<a href>` tag — a bare URL pasted as plain text does **not** get auto-linkified by Gmail and will sit as dead text.

## Facts to periodically reconfirm with the user (don't reuse stale)

- The "360+ builders" membership figure.
- The "fully booked Cursor meetup" proof point.

## Known non-issue: Gmail link rewriting

Gmail rewrites every saved draft's `<a href>` into its own `https://www.google.com/url?q=<original>&source=gmail&ust=...&sa=E` click-tracking redirect, regardless of what href was submitted or which client/API saved it. **This is cosmetic, not a bug** — clicking the wrapped link correctly forwards to the original destination (confirmed by resolving the redirect directly: it returns Google's "Redirect Notice" page naming the correct clean URL). Don't "fix" this by editing hrefs after the fact; judge correctness by the visible anchor text and the href you originally submitted, not by what a post-save re-fetch shows.
