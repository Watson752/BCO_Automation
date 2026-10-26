import csv
import glob
import os
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "lead-discovery" / "Snapchat_EasyLens_Toronto_Sponsor_Leads.xlsx"
RESEARCH_GLOB = str(ROOT / "lead-discovery" / "research_*.csv")
EXISTING_FILES = [
    ROOT / "Recovered KNBA and Invest Ottawa files" / "bco_researched_master.csv",
    ROOT / "Recovered KNBA and Invest Ottawa files" / "bco_master_leads_checkpoint.csv",
]

PREFERRED_SOURCE = {
    "canon.ca": "research_devices_creator.csv",
    "samsung.com": "research_ai_dev.csv",
    "vistek.ca": "research_devices_creator.csv",
    "lenovo.com": "research_devices_creator.csv",
    "google.com": "research_ai_dev.csv",
    "cohere.com": "research_ai_dev.csv",
    "d2l.com": "research_ecosystem.csv",
}

# Removed after qualification because the only public route was stale, media/event
# support only, or the primary offering duplicated the already-confirmed venue.
EXCLUDED_DOMAINS = {
    "amazon.com": "Event-support inbox, not a sponsor or partnership route",
    "autodesk.com": "PR-only route with weaker short-window contactability",
    "microsoft.com": "PR-only route and no strong current program trigger",
    "rogers.com": "Media-only route tied to an older source",
    "startwell.co": "Venue-first offer is redundant with the confirmed Snapchat office",
    "telus.com": "Published email source is live but dates to 2020",
    "wework.com": "Media-only route and venue offer is redundant",
}

BLOCKED_SOURCE_DOMAINS = {
    "adobe.com",
    "bestbuy.ca",
    "fasken.com",
    "memoryexpress.com",
    "sony.ca",
    "staples.ca",
    "vistek.ca",
    "xanadu.ai",
}
STATIC_EMAIL_NOT_VISIBLE = {
    "bdo.ca",
    "d2l.com",
    "koho.ca",
    "lenovo.com",
    "oneeleven.com",
    "rodeofx.com",
}
SOURCE_TIMEOUT = {"whites.com"}

HEADERS = [
    "Rank",
    "Tier",
    "Company",
    "Website",
    "Domain",
    "Toronto / Canada Presence",
    "Category",
    "Sponsor Fit Rationale",
    "Recommended Ask",
    "Estimated Capacity",
    "Contact Name",
    "Contact Role",
    "Email",
    "Email Type",
    "Email Source URL",
    "Email Source Check",
    "Personalization Hook",
    "Urgency / Ease-of-Close Signal",
    "Existing BCO Lead",
    "Prior Outreach Recipient",
    "Prior Outreach Status",
    "Fit Score",
    "Toronto Score",
    "Capacity Score",
    "Contactability Score",
    "Speed Score",
    "Priority Score",
    "Last Verified",
    "Outreach Status",
    "Notes",
]


def read_research_rows():
    rows = []
    for filename in sorted(glob.glob(RESEARCH_GLOB)):
        with open(filename, encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                row["_source_file"] = os.path.basename(filename)
                rows.append(row)
    return rows


def select_unique_leads(rows):
    selected = {}
    excluded = []
    for row in rows:
        domain = row["Domain"].strip().lower()
        if domain in EXCLUDED_DOMAINS:
            excluded.append(
                {
                    "Company": row["Company"],
                    "Domain": domain,
                    "Reason": EXCLUDED_DOMAINS[domain],
                    "Source File": row["_source_file"],
                }
            )
            continue
        if domain not in selected:
            selected[domain] = row
        elif PREFERRED_SOURCE.get(domain) == row["_source_file"]:
            excluded.append(
                {
                    "Company": selected[domain]["Company"],
                    "Domain": domain,
                    "Reason": f"Duplicate domain; stronger record retained from {row['_source_file']}",
                    "Source File": selected[domain]["_source_file"],
                }
            )
            selected[domain] = row
        else:
            excluded.append(
                {
                    "Company": row["Company"],
                    "Domain": domain,
                    "Reason": f"Duplicate domain; retained record from {selected[domain]['_source_file']}",
                    "Source File": row["_source_file"],
                }
            )
    return list(selected.values()), excluded


def load_existing_leads():
    existing = {}
    for filename in EXISTING_FILES:
        with open(filename, encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                domain = (row.get("Domain") or "").strip().lower()
                if domain:
                    existing[domain] = row
    return existing


def contactability_score(row):
    route = row["Email_Type"].lower()
    role = row["Contact_Role"].lower()
    if any(word in route for word in ("sponsorship", "partnership", "community investment")):
        return 20
    if any(word in route for word in ("media", "press", "support", "webmaster")):
        return 8
    if any(word in f"{route} {role}" for word in ("events", "event ", "creator", "education", "corporate sales")):
        return 18
    if row["Contact_Name"].strip():
        return 17
    if any(word in route for word in ("sales", "business", "general", "orders", "catering")):
        return 13
    return 11


def toronto_score(row):
    text = row["Toronto_Canada_Presence"].lower()
    gta_terms = (
        "toronto",
        "gta",
        "mississauga",
        "brampton",
        "markham",
        "richmond hill",
        "etobicoke",
    )
    if any(term in text for term in gta_terms):
        return 20
    if any(term in text for term in ("ontario", "kitchener", "waterloo")):
        return 16
    if any(term in text for term in ("canada", "canadian", "montréal", "montreal", "vancouver")):
        return 12
    return 7


def capacity_score(row):
    text = row["Capacity"].lower()
    if "very high" in text or text.startswith("high") or " high;" in text:
        return 15
    if "medium-high" in text or "medium high" in text:
        return 12
    if "medium" in text:
        return 10
    if any(word in row["Category"].lower() for word in ("catering", "photography", "swag", "snack", "bakery")):
        return 11
    return 9


def fit_score(row):
    category = row["Category"].lower()
    if any(
        phrase in category
        for phrase in (
            "3d",
            "vfx",
            "xr",
            "virtual production",
            "creative software",
            "camera",
            "imaging",
            "mobile device",
            "creator hardware",
            "creator economy",
            "social media",
            "voice ai",
        )
    ):
        return 25
    if any(
        phrase in category
        for phrase in (
            "ai",
            "developer",
            "cloud",
            "database",
            "observability",
            "computing",
            "gaming",
            "interactive",
            "animation",
            "education technology",
        )
    ):
        return 23
    if any(
        phrase in category
        for phrase in (
            "catering",
            "meals",
            "bakery",
            "snack",
            "dessert",
            "beverage",
            "photography",
            "videography",
            "swag",
        )
    ):
        return 22
    if any(
        phrase in category
        for phrase in (
            "fintech",
            "banking",
            "recruiting",
            "talent",
            "coworking",
            "law",
            "accounting",
            "accelerator",
            "retail",
        )
    ):
        return 18
    return 20


def speed_score(row):
    route = row["Email_Type"].lower()
    text = f"{row['Recommended_Contribution']} {row['Urgency_Signal']} {row['Toronto_Canada_Presence']}".lower()
    score = 7
    if any(word in route for word in ("sponsorship", "partnership", "community investment")):
        score += 8
    elif any(word in f"{route} {text}" for word in ("event", "local", "toronto")):
        score += 5
    if any(
        word in text
        for word in (
            "in-kind",
            "loan",
            "credit",
            "prize",
            "inventory",
            "delivery",
            "digital",
            "gift card",
            "speaker",
            "mentor",
            "activation",
            "branded",
            "collaboration",
        )
    ):
        score += 5
    if any(word in route for word in ("press", "media", "support", "webmaster")):
        score -= 5
    return max(5, min(score, 20))


def normalized_ask(row):
    category = row["Category"].lower()
    original = row["Recommended_Contribution"]
    if "catering" in category or "meals" in category:
        return "Food Sponsor: in-kind catering for 100 attendees; target about $800 value."
    if any(word in category for word in ("bakery", "snack", "dessert", "beverage")):
        return "Bronze / in-kind: 100 servings plus winner bundles; target $250-$600 value."
    if "photography" in category or "videography" in category:
        return "Photography Sponsor: event photo/video coverage and rapid highlights; target $500-$1,000 in-kind."
    if "swag" in category or "retail" in category:
        return "Bronze / in-kind: useful attendee items, gift cards, or winner bundles; target $300-$800 value."
    return original


def source_check(domain):
    if domain in BLOCKED_SOURCE_DOMAINS:
        return "Official source URL; automated check blocked (HTTP 403)"
    if domain in STATIC_EMAIL_NOT_VISIBLE:
        return "Official source URL; HTTP 200; email not exposed in static HTML"
    if domain in SOURCE_TIMEOUT:
        return "Official source URL; automated check timed out"
    return "Official source URL; HTTP 200; exact email observed"


def prepare_leads(rows, existing):
    prepared = []
    for row in rows:
        domain = row["Domain"].strip().lower()
        components = {
            "fit": fit_score(row),
            "toronto": toronto_score(row),
            "capacity": capacity_score(row),
            "contact": contactability_score(row),
            "speed": speed_score(row),
        }
        prior = existing.get(domain, {})
        prepared.append(
            {
                **row,
                "_domain": domain,
                "_ask": normalized_ask(row),
                "_fit": components["fit"],
                "_toronto": components["toronto"],
                "_capacity": components["capacity"],
                "_contact": components["contact"],
                "_speed": components["speed"],
                "_score": sum(components.values()),
                "_existing": "Yes" if prior else "No",
                "_prior_recipient": prior.get("Outreach_Recipient", ""),
                "_prior_status": prior.get("Outreach_Status", ""),
                "_source_check": source_check(domain),
            }
        )
    prepared.sort(
        key=lambda item: (
            -item["_score"],
            -item["_contact"],
            -item["_toronto"],
            item["Company"].lower(),
        )
    )
    for index, row in enumerate(prepared, start=1):
        row["_rank"] = index
        row["_tier"] = "A" if index <= 20 else "B" if index <= 50 else "C"
    return prepared


def style_header(ws, row=1):
    fill = PatternFill("solid", fgColor="17365D")
    for cell in ws[row]:
        cell.fill = fill
        cell.font = Font(name="Arial", color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def add_leads_sheet(wb, leads):
    ws = wb.active
    ws.title = "Sponsor Leads"
    ws.append(HEADERS)
    for lead in leads:
        row_number = ws.max_row + 1
        ws.append(
            [
                lead["_rank"],
                lead["_tier"],
                lead["Company"],
                lead["Website"],
                lead["_domain"],
                lead["Toronto_Canada_Presence"],
                lead["Category"],
                lead["Fit_Rationale"],
                lead["_ask"],
                lead["Capacity"],
                lead["Contact_Name"],
                lead["Contact_Role"],
                lead["Email"],
                lead["Email_Type"],
                lead["Email_Source_URL"],
                lead["_source_check"],
                lead["Personalization_Hook"],
                lead["Urgency_Signal"],
                lead["_existing"],
                lead["_prior_recipient"],
                lead["_prior_status"],
                lead["_fit"],
                lead["_toronto"],
                lead["_capacity"],
                lead["_contact"],
                lead["_speed"],
                f"=SUM(V{row_number}:Z{row_number})",
                lead["Last_Verified"],
                "Not Contacted",
                "",
            ]
        )

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:AD{ws.max_row}"
    ws.sheet_view.showGridLines = False
    ws.row_dimensions[1].height = 42

    widths = {
        "A": 7,
        "B": 7,
        "C": 27,
        "D": 29,
        "E": 23,
        "F": 40,
        "G": 29,
        "H": 52,
        "I": 48,
        "J": 37,
        "K": 22,
        "L": 31,
        "M": 34,
        "N": 28,
        "O": 48,
        "P": 42,
        "Q": 53,
        "R": 52,
        "S": 17,
        "T": 27,
        "U": 21,
        "V": 11,
        "W": 13,
        "X": 14,
        "Y": 18,
        "Z": 12,
        "AA": 14,
        "AB": 14,
        "AC": 18,
        "AD": 30,
    }
    for column, width in widths.items():
        ws.column_dimensions[column].width = width

    tier_fills = {
        "A": PatternFill("solid", fgColor="C6E0B4"),
        "B": PatternFill("solid", fgColor="FFF2CC"),
        "C": PatternFill("solid", fgColor="E7E6E6"),
    }
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.font = Font(name="Arial", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        row[1].fill = tier_fills[row[1].value]
        row[0].alignment = Alignment(horizontal="center", vertical="top")
        for index in range(21, 27):
            row[index].alignment = Alignment(horizontal="center", vertical="top")
        for index in (3, 14):
            row[index].hyperlink = row[index].value
            row[index].style = "Hyperlink"

    ws.conditional_formatting.add(
        f"AA2:AA{ws.max_row}",
        ColorScaleRule(
            start_type="min",
            start_color="F8696B",
            mid_type="percentile",
            mid_value=50,
            mid_color="FFEB84",
            end_type="max",
            end_color="63BE7B",
        ),
    )
    table = Table(displayName="TorontoSponsorLeads", ref=f"A1:AD{ws.max_row}")
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(table)


def add_methodology_sheet(wb, leads):
    ws = wb.create_sheet("Methodology")
    rows = [
        ["Toronto Hackathon Sponsor Lead List", "Methodology and use notes"],
        ["Purpose", "Cold-outreach prospecting for the EasyLens × Snapchat Toronto event on November 12, 2026."],
        ["List size", "Exactly 75 unique company domains. Tier A = ranks 1-20; Tier B = 21-50; Tier C = 51-75."],
        ["Email rule", "Every retained email was reported as publicly published on an official company-owned page. No address was guessed or pattern-generated."],
        ["Source check", "Automated URL checks ran on 2026-10-26. HTTP 403 means the official page blocked automation, not that the page is invalid. Static-HTML warnings identify pages where client rendering or obfuscation hid the email from the automated fetch."],
        ["Existing BCO check", "Domains were checked against bco_researched_master.csv and bco_master_leads_checkpoint.csv. No retained domain matched either export."],
        ["Fit Score (25)", "Relevance to AR/XR, 3D, creators, cameras, AI/developer tools, students, food, photography, or prizes."],
        ["Toronto Score (20)", "20 for Toronto/GTA; 16 for wider Ontario; 12 for Canada/major Canadian presence; 7 otherwise."],
        ["Capacity Score (15)", "Estimated ability to contribute cash, devices, credits, food, services, or prizes. This is a research estimate, not confirmed budget."],
        ["Contactability Score (20)", "Highest for sponsorship/partnership/community routes, then event/creator/education or named contacts, then general/sales, then press/support."],
        ["Speed Score (20)", "Rewards direct local routes and quickly deliverable in-kind contributions; penalizes press/support routing."],
        ["Priority Score", "Formula: Fit + Toronto + Capacity + Contactability + Speed. Tiers are relative to this 75-lead portfolio."],
        ["Package context", "The package seeks $3,000-$4,000 total. Food is about $800; prizes target $500/$200/$100, with first prize up to $1,000; photography is also needed."],
        ["Timing assumption", "Research performed 2026-10-26, leaving 17 days. In-kind inventory, digital credits, prizes, mentors, and local services are generally faster than new cash approvals."],
        ["Outreach guardrail", "This workbook is a lead list only. No emails were drafted or sent during this phase."],
    ]
    for row in rows:
        ws.append(row)
    ws.merge_cells("A1:B1")
    ws["A1"].font = Font(name="Arial", size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor="17365D")
    ws["A1"].alignment = Alignment(horizontal="center")
    for row in ws.iter_rows(min_row=2):
        row[0].font = Font(name="Arial", bold=True, color="17365D")
        row[1].font = Font(name="Arial")
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 110
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"


def add_event_sheet(wb):
    ws = wb.create_sheet("Event Brief")
    data = [
        ["Field", "Confirmed draft-package detail"],
        ["Event", "EasyLens × Snapchat workshop plus hackathon"],
        ["Location", "Snapchat Toronto office"],
        ["Date / time", "Thursday, November 12, 2026; proposed 6:00 PM-9:30 PM"],
        ["Audience", "100 students, young designers, creators, and AI-curious builders"],
        ["Format", "One-night workshop and hackathon; environment, character, and generative-AI lenses"],
        ["Reach", "Promotion across Snapchat, Discord, and LinkedIn; recent events reported 200+ signups and 150+ attendance"],
        ["Funding target", "$3,000-$4,000 total, cash or in kind"],
        ["Uses", "Food (~$800), prizes ($500/$200/$100, first prize up to $1,000), and photography/video"],
        ["Sponsor benefits", "Logo placement, social shoutouts, stage/mentor options, named prize, and a custom brand Lens depending on package"],
        ["Packages", "Gold, Silver, Bronze, Food Sponsor, Prizes, or a custom cash/in-kind mix"],
        ["Event contact", "Ayoub Alghali, Event Lead · ayoub.alghali@gmail.com"],
        ["Source", "Draft sponsorship-package.pdf dated October 22, 2026"],
    ]
    for row in data:
        ws.append(row)
    style_header(ws)
    for row in ws.iter_rows(min_row=2):
        row[0].font = Font(name="Arial", bold=True, color="17365D")
        row[1].font = Font(name="Arial")
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 105
    ws.freeze_panes = "A2"
    ws.sheet_view.showGridLines = False


def add_exclusions_sheet(wb, exclusions):
    ws = wb.create_sheet("Excluded & Duplicates")
    headers = ["Company", "Domain", "Reason", "Research Source"]
    ws.append(headers)
    for item in sorted(exclusions, key=lambda row: (row["Domain"], row["Company"])):
        ws.append([item["Company"], item["Domain"], item["Reason"], item["Source File"]])
    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:D{ws.max_row}"
    ws.sheet_view.showGridLines = False
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="Arial")
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    for column, width in {"A": 30, "B": 24, "C": 72, "D": 34}.items():
        ws.column_dimensions[column].width = width


def validate_inputs(leads):
    assert len(leads) == 75, f"Expected 75 leads, found {len(leads)}"
    domains = [row["_domain"] for row in leads]
    emails = [row["Email"].strip().lower() for row in leads]
    assert len(domains) == len(set(domains)), "Duplicate domains remain"
    assert len(emails) == len(set(emails)), "Duplicate emails remain"
    assert all(row["Email_Source_URL"].startswith("http") for row in leads), "Missing source URL"
    assert all("@" in row["Email"] for row in leads), "Invalid email"
    assert all(row["Last_Verified"] == "2026-10-26" for row in leads), "Unexpected verification date"


def validate_workbook(path):
    workbook = load_workbook(path, data_only=False)
    assert workbook.sheetnames == [
        "Sponsor Leads",
        "Methodology",
        "Event Brief",
        "Excluded & Duplicates",
    ]
    ws = workbook["Sponsor Leads"]
    assert ws.max_row == 76
    assert ws.max_column == 30
    assert Counter(ws.cell(row=row, column=2).value for row in range(2, 77)) == {
        "A": 20,
        "B": 30,
        "C": 25,
    }
    assert all(str(ws.cell(row=row, column=27).value).startswith("=") for row in range(2, 77))


def main():
    raw_rows = read_research_rows()
    selected, exclusions = select_unique_leads(raw_rows)
    existing = load_existing_leads()
    leads = prepare_leads(selected, existing)
    validate_inputs(leads)

    workbook = Workbook()
    add_leads_sheet(workbook, leads)
    add_methodology_sheet(workbook, leads)
    add_event_sheet(workbook)
    add_exclusions_sheet(workbook, exclusions)
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True
    workbook.calculation.calcMode = "auto"
    workbook.save(OUTPUT)
    validate_workbook(OUTPUT)
    print(f"Created {OUTPUT}")
    print(f"Leads: {len(leads)} | exclusions/duplicates logged: {len(exclusions)}")


if __name__ == "__main__":
    main()
