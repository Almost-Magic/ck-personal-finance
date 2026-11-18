from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "story-flow"
DOCX = OUT_DIR / "CK-Personal-Finance-Story-Flow-v0.5.docx"
MD = OUT_DIR / "CK-Personal-Finance-Story-Flow-v0.5.md"
QA_DEEP = ROOT / "reports" / "qa" / "ck-personal-finance-deep-ui-audit-270628"
QA_LOCAL = ROOT / "reports" / "qa" / "ck-personal-finance-local-internal-270626"


VERSION = "v0.5"
TITLE = f"CK Personal Finance Story Flow {VERSION}"
ROUTES = "http://127.0.0.1:5124/ and http://amtl/sak/finance/"


COLOURS = {
    "ink": "111410",
    "muted": "5C5548",
    "gold": "C9A96E",
    "green": "476B52",
    "red": "9B2B25",
    "fill": "F6F3EA",
    "fill_alt": "EDE6D8",
    "border": "D8D1C0",
    "dark": "111410",
}


SECTIONS = [
    {
        "group": "Overview",
        "question": "What needs attention today?",
        "tabs": [
            ("Today", "Start with the money items that need care now: next bills, quiet risks, recent changes, and safe local actions."),
            ("What changed", "A short change story instead of a long scroll of every proof row."),
            ("Review later", "Park useful but non-urgent items so the app does not keep shouting."),
            ("Focus mode", "Only today's pulse, one next action, and the evidence link."),
        ],
    },
    {
        "group": "Money Flow",
        "question": "Where is money going?",
        "tabs": [
            ("Transactions", "Rows, merchants, source freshness, and receipt links without bank-provider writes."),
            ("Bills", "Upcoming bills, pressure days, reminders, and exact named rows."),
            ("Subscriptions", "Recurring payments, trial endings, price changes, annual cost, and cancellation routes."),
            ("Refunds", "Expected refunds, received refunds, and follow-up reminders."),
            ("Fees and duplicates", "Bank fees, duplicate charges, price changes, and unusual merchant rows."),
            ("Merchants", "Messy merchant labels, user-friendly names, and remembered context."),
        ],
    },
    {
        "group": "Planning",
        "question": "What happens next?",
        "tabs": [
            ("Forecast", "Month-end, 30-day, bill-pressure, and buffer forecasts with assumptions shown only when opened."),
            ("Monthly run rate", "Daily pace, category pace, and comfort-target drift without shame language."),
            ("Scenario planner", "Try a choice locally before taking any real-world action."),
            ("Safe-to-spend", "A careful estimate, not an instruction or regulated advice."),
            ("Sinking funds", "Turn annual costs into monthly set-aside rhythms."),
            ("Goals", "Comfort targets, future dates, and small repeated actions."),
            ("Reminders", "Local reminders for reviews, bills, refunds, trials, and notice periods."),
        ],
    },
    {
        "group": "Tools",
        "question": "What can help me find or fix things?",
        "tabs": [
            ("Money tools", "Small tools appear as buttons: find, check, match, track, explain, and remember."),
            ("Import", "Excel, CSV, PDF, receipt image, statement, and manual-note flows are mapped before anything is trusted."),
            ("Cancellation finder", "Unsubscribe pages, platform-managed subscriptions, support scripts, and follow-up reminders."),
            ("Renewal centre", "Annual renewals, notice periods, contracts, warranties, and return windows."),
            ("Dispute pack", "Local evidence packs for suspicious or incorrect charges without contacting anyone."),
            ("Money memory", "Decision log, review-later queue, do-not-nag state, and important money events."),
            ("Money rules", "Local rules for reminders, hiding, tone, forecast assumptions, and review rhythm."),
        ],
    },
    {
        "group": "Evidence",
        "question": "Why does the app think this?",
        "tabs": [
            ("Search", "Search approved local documents and indexed NAS evidence with PostgreSQL and pgvector."),
            ("Receipt matcher", "Link receipts, invoices, PDFs, and imported rows to money objects."),
            ("Evidence gaps", "Show what needs one more source, not as blame but as confidence repair."),
            ("Tax evidence pack", "Evidence organisation only; not tax advice."),
            ("NAS sources", "Index approved NAS roots with only the two user-named exclusions."),
        ],
    },
    {
        "group": "Chat",
        "question": "Can I just ask?",
        "tabs": [
            ("Ask my money", "A contextual money co-pilot that answers from local data and offers buttons that open real screens."),
            ("Explain this", "Explain the selected row, amount, date, merchant, report, or action."),
            ("Build scenario", "Turn a chat question into a local scenario plan."),
            ("Find evidence", "Ask for source-backed evidence without exposing raw documents unless approved."),
        ],
    },
    {
        "group": "Reports",
        "question": "What story or export do I need?",
        "tabs": [
            ("Monthly money story", "What happened, what changed, what needs review, and what evidence backs it."),
            ("Forecast report", "Forecast summary, assumptions, pressure days, scenarios, and evidence."),
            ("Subscription report", "Recurring payments, annual costs, review state, price changes, and cancellation status."),
            ("Bills and renewals", "Bills, contracts, notice periods, and renewal timeline."),
            ("Evidence report", "Freshness, gaps, matched receipts, NAS sources, and proof links."),
            ("Refunds and disputes", "Refund promises, dispute packets, waiting state, and follow-up dates."),
            ("Spending change", "New merchants, changed categories, unusual charges, duplicate charges, and fees."),
            ("Data quality", "What is fresh, what is missing, what is inferred, and what needs repair."),
        ],
    },
    {
        "group": "Admin",
        "question": "Is the system healthy and proven?",
        "tabs": [
            ("Proof", "PostgreSQL, pgvector, Workshop, Beast, browser QA, audits, and local route truth."),
            ("Privacy", "Local-only boundaries, provider gates, excluded NAS paths, and blocked external actions."),
            ("AI routing", "OpenRouter free, modest, and full-expensive tiers selected by reasoning level."),
            ("Data sources", "PostgreSQL, pgvector, approved documents, NAS receipts, and import source state."),
            ("Delivery matrix", "The implementation matrix lives here, not in the normal user screen."),
        ],
    },
]


BUTTONS = [
    ("Open exact rows", "The detail panel opens named rows for the selected tab instead of asking Mani to trust a vague count."),
    ("Create review receipt", "The app writes a local finance_decision_receipts row and shows the receipt ID and boundary."),
    ("Search evidence", "The app runs local PostgreSQL/pgvector search and returns source-backed evidence."),
    ("Index NAS sources", "The app scans approved NAS roots, excludes only the two user-named paths, writes chunks, and returns a receipt."),
    ("Create local report", "The app writes a local report_exports row with external_send_state kept as not_sent."),
    ("Route AI task", "The app selects an OpenRouter cost/reasoning tier. Provider execution remains gated unless explicitly approved."),
    ("Run audit loop", "The app runs the local audit endpoint and returns done, partial, blocked, and missing counts."),
    ("Copy privacy receipt", "The app copies the local/internal privacy and no-advice boundary text."),
    ("Timeline", "The app opens a compact timeline visual only when requested."),
    ("Trend", "The app opens a compact trend/run-rate visual only when requested."),
    ("Compare", "The app opens a before/after or scenario comparison only when requested."),
    ("Evidence map", "The app shows the row -> source -> evidence -> receipt chain."),
    ("Annual cost", "The app turns a recurring monthly amount into a calm annual-cost view."),
    ("Explain", "The selected row is explained in the right contextual helper rail."),
]


FIELD_STORIES = [
    ("due_date", "Tells Mani when a reminder, bill, refund, trial, or renewal needs attention."),
    ("cadence", "Shows the rhythm of the review so the app can remind without nagging."),
    ("source_ref", "Explains why a row exists and where the app learned it."),
    ("source_path", "Points to local or NAS evidence when evidence is available."),
    ("evidence_text", "Shows the specific source-backed snippet or metadata behind a claim."),
    ("score", "Shows pgvector similarity for evidence search results."),
    ("external_send_state", "Stays not_sent unless Mani explicitly approves a future external target."),
    ("boundary", "Names the safety limit: local planning, no bank action, no regulated advice, no external write."),
    ("provider_called", "Shows whether OpenRouter was actually called or only routed."),
    ("selectedTier", "Shows the chosen OpenRouter tier: free, modest, or full-expensive."),
    ("excluded_prefixes", "Names the two NAS paths that must never be indexed."),
    ("excluded_path_matches", "Must stay 0 for the excluded NAS paths."),
]


END_TO_END_STORIES = [
    ("Daily money check", ["Open /sak/finance/", "Read the finance wisdom prompt", "Stay on Overview > Today", "Click Reminders", "Open exact rows", "Create review receipt", "Read the helper rail"]),
    ("Subscription review", ["Open Money Flow", "Click Subscriptions", "Click Annual cost", "Open cancellation route", "Create local review receipt", "No auto-cancel happens"]),
    ("Forecast check", ["Open Planning", "Click Forecast", "Open assumptions only if needed", "Click Compare", "Route AI task if reasoning help is needed", "Keep result local"]),
    ("Scenario build from chat", ["Open Chat", "Click Build scenario", "Ask the question", "The app maps it to Scenario planner", "Create a local scenario receipt", "Show safe boundary"]),
    ("Evidence search", ["Open Evidence", "Click Search", "Search approved evidence", "Show source, snippet, score", "Explain selected row in the helper rail"]),
    ("NAS evidence refresh", ["Open Evidence > NAS sources", "Click Index NAS sources", "Scan approved roots", "Skip excluded prefixes", "Write pgvector chunks", "Show receipt"]),
    ("Report creation", ["Open Reports", "Choose Monthly money story", "Click Create local report", "Write report_exports row", "Show external_send_state=not_sent"]),
    ("Admin proof", ["Open Admin", "Click Proof", "Review PostgreSQL/pgvector/route/browser QA truth", "Run audit loop", "Copy privacy receipt"]),
    ("External request boundary", ["Ask to connect a bank, pay, cancel, send, or give regulated advice", "The app shows the missing target/approval boundary", "No external action happens"]),
]


def hex_rgb(value):
    return RGBColor.from_string(value)


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_border(cell, color=None):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color or COLOURS["border"])
        borders.append(el)
    tc_pr.append(borders)


def style_run(run, size=10.5, bold=False, color=None):
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = hex_rgb(color)


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.space_before = Pt(10 if level == 1 else 7)
    p.paragraph_format.space_after = Pt(5)
    for run in p.runs:
        run.clear()
    r = p.add_run(text)
    style_run(r, size={1: 16, 2: 13, 3: 11.5}.get(level, 10.5), bold=True, color=COLOURS["gold"] if level == 1 else COLOURS["ink"])
    return p


def add_body(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.18
    style_run(p.add_run(text), size=10.5, color=COLOURS["ink"])


def add_callout(doc, title, body, fill=None):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    set_cell_shading(cell, fill or COLOURS["fill"])
    set_cell_border(cell)
    p = cell.paragraphs[0]
    style_run(p.add_run(title), size=10.5, bold=True, color=COLOURS["ink"])
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    style_run(p2.add_run(body), size=10, color=COLOURS["ink"])
    doc.add_paragraph()


def add_diagram(doc, title, lines):
    add_heading(doc, title, 3)
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, COLOURS["dark"])
    set_cell_border(cell, "3A3429")
    p = cell.paragraphs[0]
    for i, line in enumerate(lines):
        if i:
            p.add_run("\n")
        r = p.add_run(line)
        r.font.name = "Consolas"
        r._element.rPr.rFonts.set(qn("w:ascii"), "Consolas")
        r._element.rPr.rFonts.set(qn("w:hAnsi"), "Consolas")
        r.font.size = Pt(8.5)
        r.font.color.rgb = hex_rgb("F0EEE7")
    doc.add_paragraph()


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, header in enumerate(headers):
        cell = table.rows[0].cells[idx]
        set_cell_shading(cell, COLOURS["fill_alt"])
        set_cell_border(cell)
        style_run(cell.paragraphs[0].add_run(header), size=9.2, bold=True, color=COLOURS["ink"])
    for row in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row):
            set_cell_border(cells[idx])
            cells[idx].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            cells[idx].paragraphs[0].paragraph_format.space_after = Pt(2)
            style_run(cells[idx].paragraphs[0].add_run(str(value)), size=8.8, color=COLOURS["ink"])
    doc.add_paragraph()


def module_story(group, tab, copy):
    return [
        f"Mani opens the grouped left menu item {group} and selects {tab}.",
        f"The centre column changes to {group} > {tab} and says, in plain language: {copy}",
        "The app keeps the centre calm. It shows the relevant tab, one primary row first, exact named rows in the detail panel, and only the buttons that make sense for this screen.",
        "The right rail changes to this context. Its detail boxes stay collapsed until Mani asks for Selected thing, Why shown here, or Safe boundary.",
    ]


def button_rows_for(group, tab):
    rows = [
        ("Open exact rows", "Shows named rows behind the count or screen."),
        ("Create review receipt", "Records a local review receipt when Mani takes or parks an action."),
    ]
    if group in {"Overview", "Evidence", "Tools", "Chat"} or tab in {"Tax Evidence Pack", "Evidence report", "Data quality"}:
        rows.append(("Search evidence", "Searches local PostgreSQL/pgvector evidence."))
    if group == "Evidence":
        rows.append(("Index NAS sources", "Indexes approved NAS source paths with the two exclusions kept out."))
    if group in {"Reports", "Overview", "Planning"}:
        rows.append(("Create local report", "Creates a local report/export receipt with not_sent external state."))
    if group in {"Planning", "Chat", "Admin"}:
        rows.append(("Route AI task", "Routes through OpenRouter policy without provider execution by default."))
    if group == "Admin":
        rows.extend([
            ("Run audit loop", "Runs the five-loop style audit endpoint and reports counts."),
            ("Copy privacy receipt", "Copies the local/internal boundary."),
        ])
    if tab in {"Subscriptions", "Monthly run rate", "Forecast", "Scenario planner"}:
        rows.append(("Trend / Compare / Annual cost", "Opens compact visuals only when requested."))
    return rows


def build_docx():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    styles = doc.styles
    styles["Normal"].font.name = "Calibri"
    styles["Normal"].font.size = Pt(10.5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    style_run(p.add_run(TITLE), size=22, bold=True, color=COLOURS["ink"])
    p = doc.add_paragraph()
    style_run(p.add_run(f"Regenerated after Product Bible v0.6 addendum, deep UI/Elaine comparison audit, AMTL logo/seal pass, CK Personal Finance logo generation, and current UI changes. Current routes: {ROUTES}"), size=10.5, color=COLOURS["muted"])
    add_callout(doc, "Version truth", f"{VERSION} supersedes v0.4. It describes the current UI contract in public/index.html and the current proof state recorded on 2026-06-28.")

    desktop = QA_DEEP / "desktop-final-ready-viewport.png"
    if desktop.exists():
        doc.add_picture(str(desktop), width=Inches(6.4))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_body(doc, "Visual anchor: current desktop ready-state screenshot from the five-loop UI audit.")

    add_heading(doc, "1. Opening Story", 1)
    add_body(doc, "When Mani opens CK Personal Finance, the app does not begin as a wall of proof. It opens as a calm local money cockpit. At the top left, the AMTL logo appears first. Immediately beside it, on the same line, are the generated CK Personal Finance logo, the product name, and the line Private local money cockpit.")
    add_body(doc, "The middle of the header shows a finance wisdom prompt: a money note, an investment reminder, or a small money story. Next to that rhythm are DD MMM, the day, the local time, and Weather/status. On the top right, the AMTL seal is large and visible.")
    add_body(doc, "The left menu opens only Overview by default. Money Flow, Planning, Tools, Evidence, Chat, Reports, and Admin stay collapsed. The centre opens Overview > Today. The right side opens the contextual helper and keeps the deeper boxes collapsed until Mani asks.")
    add_diagram(doc, "First-screen flow", [
        "Open /sak/finance/",
        "  -> Header: AMTL logo + CK Personal Finance logo/name + wisdom prompt + DD MMM/day/time/status + AMTL seal",
        "  -> Left: Overview open; other menu groups collapsed",
        "  -> Middle: Overview > Today, clickable counts, current work panel, exact rows",
        "  -> Right: contextual helper, next useful action, collapsed detail boxes",
    ])

    add_heading(doc, "2. Universal Screen Contract", 1)
    add_table(doc, ["Area", "What Mani sees", "What the app does"], [
        ("Header", "AMTL logo, CK logo/name, finance prompt, DD MMM, day, time, Weather/status, AMTL seal.", "Establishes identity, proof mood, and local runtime health without opening Admin."),
        ("Left menu", "Overview, Money Flow, Planning, Tools, Evidence, Chat, Reports, Admin.", "Keeps navigation grouped and collapsed so the default view is not a dumping ground."),
        ("Centre", "Primary segment row, per-section tabs, clickable counts, work panel, exact named rows.", "Turns each task into a story path: choose, inspect, click, receive local result."),
        ("Right rail", "Contextual helper, next action, Selected thing, Why shown here, Safe boundary.", "Explains what the selected thing means only when it helps."),
        ("Action output", "Plain result text after a button click.", "Shows receipt IDs, evidence results, audit counts, route decisions, or boundaries."),
    ])

    add_heading(doc, "3. Complete Menu And Screen Stories", 1)
    for section_data in SECTIONS:
        group = section_data["group"]
        add_heading(doc, group, 2)
        add_body(doc, f"Menu story: Mani opens {group} when the question is: {section_data['question']} The app expands that group, keeps the rest quiet, updates the breadcrumb, and loads the matching screen.")
        for tab, copy in section_data["tabs"]:
            add_heading(doc, f"{group} > {tab}", 3)
            for para in module_story(group, tab, copy):
                add_body(doc, para)
            add_table(doc, ["Button or field", "What happens"], button_rows_for(group, tab))

    add_heading(doc, "4. Button Stories", 1)
    for button, story in BUTTONS:
        add_heading(doc, button, 3)
        add_body(doc, f"Mani clicks {button}. {story}")
        add_body(doc, "The app writes the result into the action output panel. If the action would require bank access, payment, cancellation, regulated advice, source/customer writes, external send, deploy, push, or public release, the app names the boundary instead of pretending it happened.")

    add_heading(doc, "5. Runtime And Evidence Flow", 1)
    add_diagram(doc, "Local/internal runtime flow", [
        "UI click",
        "  -> /api/personal-finance route",
        "  -> PostgreSQL-only runtime store",
        "  -> pgvector evidence search when needed",
        "  -> local receipt, report, audit, or route decision",
        "  -> action output + exact rows + contextual helper",
        "  -> external actions remain blocked unless explicitly approved",
    ])
    add_table(doc, ["Field", "Story"], FIELD_STORIES)

    add_heading(doc, "6. End-To-End Story Flows", 1)
    for title, steps in END_TO_END_STORIES:
        add_heading(doc, title, 3)
        add_diagram(doc, title, [steps[0], *[f"  -> {step}" for step in steps[1:]]])
        add_body(doc, f"In this story, Mani starts with {steps[0]}. The app then guides him through {', '.join(steps[1:-1])}, and the end state is: {steps[-1]}.")

    add_heading(doc, "7. Boundary Stories", 1)
    add_body(doc, "If Mani asks the app to cancel a subscription, the app can find the route, draft a script, create a reminder, and record a receipt. It does not auto-cancel.")
    add_body(doc, "If Mani asks the app to connect to a bank or CDR provider, the app names that live bank/provider connection is approval-gated. It does not silently connect.")
    add_body(doc, "If Mani asks for financial advice, the app organises evidence, explains rows, and builds local scenarios. It does not provide regulated advice.")
    add_body(doc, "If Mani asks for AI help, OpenRouter routing selects a tier by reasoning level. Provider execution remains gated unless explicitly allowed.")

    add_heading(doc, "8. Evidence And Version Anchors", 1)
    add_table(doc, ["Anchor", "Current truth"], [
        ("Product Bible", "CK-PRODUCT-BIBLE-v0.6.md addendum: CK Personal Finance Calm Layout And 500 Ideas Absorption Contract."),
        ("Story Flow", f"{TITLE}; regenerated after v0.4."),
        ("Routes", ROUTES),
        ("Visual proof", str(QA_DEEP / "five-loop-visual-product-audit-final.json")),
        ("Delivery matrix", str(QA_LOCAL / "product-bible-delivery-matrix-270627.md")),
        ("Status file", str(QA_LOCAL / "C1-CK-PERSONAL-FINANCE-LOCAL-INTERNAL-270626.md")),
    ])

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(footer.add_run(f"{TITLE} - local/internal story map"), size=8, color=COLOURS["muted"])
    doc.save(DOCX)


def mermaid_flow(title, steps):
    lines = ["```mermaid", "flowchart TD"]
    previous = None
    for idx, step in enumerate(steps):
        node = f"N{idx}"
        safe = step.replace('"', "'")
        lines.append(f'  {node}["{safe}"]')
        if previous:
            lines.append(f"  {previous} --> {node}")
        previous = node
    lines.append("```")
    return "\n".join(lines)


def build_markdown():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {TITLE}",
        "",
        f"Regenerated after Product Bible v0.6 addendum, deep UI/Elaine comparison audit, AMTL logo/seal pass, CK Personal Finance logo generation, and current UI changes. Current routes: `{ROUTES}`.",
        "",
        f"Version truth: `{VERSION}` supersedes `v0.4` and describes the current UI contract in `public/index.html` plus the 2026-06-28 proof state.",
        "",
        "## Opening Story",
        "",
        "When Mani opens CK Personal Finance, the app does not begin as a wall of proof. It opens as a calm local money cockpit. At the top left, the AMTL logo appears first. Immediately beside it, on the same line, are the generated CK Personal Finance logo, the product name, and the line `Private local money cockpit`.",
        "",
        "The middle of the header shows a finance wisdom prompt: a money note, an investment reminder, or a small money story. Next to that rhythm are `DD MMM`, the day, the local time, and `Weather/status`. On the top right, the AMTL seal is large and visible.",
        "",
        mermaid_flow("First screen", [
            "Open /sak/finance/",
            "Header shows AMTL logo, CK logo/name, wisdom prompt, DD MMM, day, time, weather/status, AMTL seal",
            "Left menu opens Overview only",
            "Middle opens Overview > Today",
            "Right rail opens contextual helper with detail boxes collapsed",
        ]),
        "",
        "## Universal Screen Contract",
        "",
        "| Area | What Mani sees | What the app does |",
        "|---|---|---|",
        "| Header | AMTL logo, CK logo/name, finance prompt, DD MMM, day, time, Weather/status, AMTL seal | Establishes identity and local runtime health |",
        "| Left menu | Overview, Money Flow, Planning, Tools, Evidence, Chat, Reports, Admin | Keeps navigation grouped and collapsed |",
        "| Centre | Segment row, tabs, clickable counts, work panel, exact rows | Turns each task into choose, inspect, click, local result |",
        "| Right rail | Contextual helper, next action, Selected thing, Why shown here, Safe boundary | Explains only the current selected thing |",
        "| Action output | Plain result text after a button click | Shows receipt IDs, evidence results, audit counts, routes, or boundaries |",
        "",
        "## Complete Menu And Screen Stories",
        "",
    ]

    for section_data in SECTIONS:
        group = section_data["group"]
        lines.extend([
            f"### {group}",
            "",
            f"Mani opens `{group}` when the question is: {section_data['question']} The app expands that group, keeps the rest quiet, updates the breadcrumb, and loads the matching screen.",
            "",
        ])
        for tab, copy in section_data["tabs"]:
            lines.extend([
                f"#### {group} > {tab}",
                "",
            ])
            for para in module_story(group, tab, copy):
                lines.extend([para, ""])
            lines.extend(["| Button or field | What happens |", "|---|---|"])
            for label, behaviour in button_rows_for(group, tab):
                lines.append(f"| {label} | {behaviour} |")
            lines.append("")

    lines.extend([
        "## Button Stories",
        "",
    ])
    for button, story in BUTTONS:
        lines.extend([
            f"### {button}",
            "",
            f"Mani clicks `{button}`. {story}",
            "",
            "The app writes the result into the action output panel. If the action would require bank access, payment, cancellation, regulated advice, source/customer writes, external send, deploy, push, or public release, the app names the boundary instead of pretending it happened.",
            "",
        ])

    lines.extend([
        "## Runtime And Evidence Flow",
        "",
        mermaid_flow("Runtime", [
            "UI click",
            "/api/personal-finance route",
            "PostgreSQL-only runtime store",
            "pgvector evidence search when needed",
            "local receipt, report, audit, or route decision",
            "action output plus exact rows plus contextual helper",
            "external actions blocked unless explicitly approved",
        ]),
        "",
        "| Field | Story |",
        "|---|---|",
    ])
    for field, story in FIELD_STORIES:
        lines.append(f"| `{field}` | {story} |")

    lines.extend(["", "## End-To-End Story Flows", ""])
    for title, steps in END_TO_END_STORIES:
        lines.extend([f"### {title}", "", mermaid_flow(title, steps), "", f"In this story, Mani starts with `{steps[0]}`. The app then guides him through {', '.join(steps[1:-1])}, and the end state is: {steps[-1]}.", ""])

    lines.extend([
        "## Boundary Stories",
        "",
        "If Mani asks the app to cancel a subscription, the app can find the route, draft a script, create a reminder, and record a receipt. It does not auto-cancel.",
        "",
        "If Mani asks the app to connect to a bank or CDR provider, the app names that live bank/provider connection is approval-gated. It does not silently connect.",
        "",
        "If Mani asks for financial advice, the app organises evidence, explains rows, and builds local scenarios. It does not provide regulated advice.",
        "",
        "If Mani asks for AI help, OpenRouter routing selects a tier by reasoning level. Provider execution remains gated unless explicitly allowed.",
        "",
        "## Evidence And Version Anchors",
        "",
        f"- Product Bible: `CK-PRODUCT-BIBLE-v0.6.md`, addendum `CK Personal Finance Calm Layout And 500 Ideas Absorption Contract`.",
        f"- Story Flow: `{TITLE}`.",
        f"- Routes: `{ROUTES}`.",
        f"- Visual proof: `{QA_DEEP / 'five-loop-visual-product-audit-final.json'}`.",
        f"- Delivery matrix: `{QA_LOCAL / 'product-bible-delivery-matrix-270627.md'}`.",
        "- Boundary: no bank connection, payment, auto-cancellation, external send, regulated advice, deploy, push, public release, or unrelated product edit.",
        "",
    ])
    MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    build_markdown()
    build_docx()
    print(MD)
    print(DOCX)


if __name__ == "__main__":
    main()
