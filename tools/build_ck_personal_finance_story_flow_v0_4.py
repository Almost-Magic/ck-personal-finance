from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "story-flow"
DOCX = OUT_DIR / "CK-Personal-Finance-Story-Flow-v0.4.docx"


GOLD = "C9A96E"
INK = "111410"
MUTED = "5C5548"
FILL = "F6F3EA"
BORDER = "D8D1C0"


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
            ("Subscriptions", "Find recurring payments, trial endings, price changes, annual cost, and cancellation routes."),
            ("Refunds", "Expected refunds, received refunds, and follow-up reminders."),
            ("Fees and duplicates", "Find bank fees, duplicate charges, price changes, and unusual merchant rows."),
            ("Merchants", "Decode messy merchant labels and remember user names for them."),
        ],
    },
    {
        "group": "Planning",
        "question": "What happens next?",
        "tabs": [
            ("Forecast", "Month-end, 30-day, bill pressure, and buffer forecasts with assumptions shown only when opened."),
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
            ("Cancellation finder", "Find unsubscribe pages, platform-managed subscriptions, support scripts, and follow-up reminders."),
            ("Renewal centre", "Annual renewals, notice periods, contracts, warranties, and return windows."),
            ("Dispute pack", "Build local evidence packs for suspicious or incorrect charges without contacting anyone."),
            ("Money memory", "Decision log, review-later queue, do-not-nag state, and important money events."),
            ("Money rules", "User-defined local rules for reminders, hiding, tone, forecast assumptions, and review rhythm."),
        ],
    },
    {
        "group": "Evidence",
        "question": "Why does the app think this?",
        "tabs": [
            ("Search", "Search approved local documents and indexed NAS evidence with Postgres/pgvector."),
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
            ("Proof", "Postgres, pgvector, Workshop, Beast, browser QA, audits, and local route truth."),
            ("Privacy", "Local-only boundaries, provider gates, excluded NAS paths, and blocked external actions."),
            ("AI routing", "OpenRouter free, modest, and full-expensive tiers selected by reasoning level."),
            ("Data sources", "Postgres, pgvector, approved documents, NAS receipts, and import source state."),
            ("Delivery matrix", "The implementation matrix lives here, not in the normal user screen."),
        ],
    },
]


BUTTONS = [
    ("Open exact rows", "Opens the exact named rows for the selected tab in the detail panel."),
    ("Create review receipt", "Writes a local review receipt so the choice is remembered without sending anything outside."),
    ("Search evidence", "Runs local Postgres/pgvector evidence search and shows the best source-backed result."),
    ("Index NAS sources", "Indexes approved NAS finance/evidence sources, excluding only the two user-named paths."),
    ("Create local report", "Creates a local report/export receipt with external_send_state kept local."),
    ("Route AI task", "Selects an OpenRouter reasoning/cost tier. Provider execution remains gated unless explicitly allowed."),
    ("Run audit loop", "Runs the local audit loop and reports done/partial/blocked/missing counts."),
    ("Copy privacy receipt", "Copies the local/internal privacy boundary statement."),
    ("Show proof", "Moves the user to Admin > Proof."),
    ("Timeline", "Opens a compact timeline visual."),
    ("Trend", "Opens a compact trend visual."),
    ("Compare", "Opens a before/after or scenario comparison visual."),
    ("Evidence map", "Opens row -> source -> evidence -> receipt chain."),
    ("Annual cost", "Shows monthly recurring cost as annual impact."),
    ("Explain", "Explains the selected named row in the contextual helper rail."),
]


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_border(cell, color=BORDER):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tc_pr.append(borders)


def style_run(run, size=None, bold=False, color=None):
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    if size:
        run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.style = f"Heading {level}"
    r = p.add_run(text)
    style_run(r, size={1: 16, 2: 13, 3: 12}.get(level, 11), bold=True, color=GOLD if level == 1 else INK)
    p.paragraph_format.space_before = Pt(10 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(5)
    return p


def add_body(doc, text, bold_start=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.18
    if bold_start and text.startswith(bold_start):
        r1 = p.add_run(bold_start)
        style_run(r1, 10.5, True, INK)
        r2 = p.add_run(text[len(bold_start):])
        style_run(r2, 10.5, False, INK)
    else:
        r = p.add_run(text)
        style_run(r, 10.5, False, INK)
    return p


def add_callout(doc, title, body):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Inches(6.4)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_shading(cell, FILL)
    set_cell_border(cell)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(title)
    style_run(r, 10.5, True, INK)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(body)
    style_run(r2, 10, False, INK)
    doc.add_paragraph()


def add_diagram(doc, title, lines):
    add_heading(doc, title, 3)
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, "111410")
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
        r.font.color.rgb = RGBColor(240, 238, 231)
    doc.add_paragraph()


def add_table(doc, headers, rows, widths):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for idx, header in enumerate(headers):
        cell = table.rows[0].cells[idx]
        cell.width = Inches(widths[idx])
        set_cell_shading(cell, "EDE6D8")
        set_cell_border(cell)
        p = cell.paragraphs[0]
        r = p.add_run(header)
        style_run(r, 9.2, True, INK)
    for row in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row):
            cells[idx].width = Inches(widths[idx])
            set_cell_border(cells[idx])
            cells[idx].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            p = cells[idx].paragraphs[0]
            r = p.add_run(value)
            style_run(r, 8.8, False, INK)
    doc.add_paragraph()


def module_story(group, tab, copy):
    return [
        f"Mani wants to use {group} > {tab}. He opens the grouped left menu item {group}, then selects {tab}.",
        f"The middle column changes to the {tab} tab and shows the purpose in plain language: {copy}",
        "The app keeps the centre calm. It shows one primary row first, then exact named rows in the detail panel. Mani can use the relevant action buttons without opening reports or admin proof.",
        "The right contextual rail updates to this tab. Its boxes stay collapsed until Mani asks: Why this matters, Evidence, Next action, Safety, plus Selected thing, Why shown here, and Safe boundary.",
    ]


def build():
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

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = title.add_run("CK Personal Finance Story Flow v0.4")
    style_run(r, 22, True, INK)
    subtitle = doc.add_paragraph()
    r = subtitle.add_run("Updated after Product Bible addendum, Elaine calm UI comparison, and deep visual audit. Current routes: http://127.0.0.1:5124/ and http://amtl/sak/finance/.")
    style_run(r, 10.5, False, MUTED)
    add_callout(
        doc,
        "Version truth",
        "v0.4 supersedes the earlier story-flow draft. It matches the current UI labels in public/index.html and the 2026-06-28 Product Bible/UI contract."
    )

    add_heading(doc, "1. What happens when Mani opens the app", 1)
    add_body(doc, "Mani opens CK Personal Finance. The app starts with a calm local cockpit, not a wall of technical proof. At the top-left, the AMTL logo appears first. Immediately beside it are the CK Personal Finance logo, product name, and the line Private local money cockpit.")
    add_body(doc, "In the middle of the header, the app shows a finance wisdom prompt. It may be a money principle, a small anecdote, or the next best money prompt. Below it are DD MMM, the day, the time, and Weather/status. On the top-right, the AMTL seal is visible and large enough to read as a real brand/proof signal.")
    add_body(doc, "The left menu opens only Overview by default. Money Flow, Planning, Tools, Evidence, Chat, Reports, and Admin stay collapsed until Mani asks for them. The middle column opens Overview > Today. The right rail opens the Contextual helper, with helper boxes collapsed.")

    add_diagram(doc, "Login/opening screen flow", [
        "Open CK Personal Finance",
        "  -> Header: AMTL logo + CK logo/name + wisdom prompt + DD MMM/day/time/status + AMTL seal",
        "  -> Left: Overview open, other groups collapsed",
        "  -> Middle: Overview segment + Today tab + counts + exact rows",
        "  -> Right: Contextual helper + Next useful action, detail boxes collapsed",
    ])

    add_heading(doc, "2. The universal screen contract", 1)
    add_body(doc, "Every screen follows the same calm pattern. The left column answers where Mani is. The middle column answers what Mani can do now. The right rail answers why this selected thing matters, what evidence backs it, and what the safest next action is.")
    add_table(
        doc,
        ["Area", "What Mani sees", "Why it exists"],
        [
            ("Header", "AMTL logo, CK Personal Finance logo/name, finance wisdom prompt, DD MMM, day, time, Weather/status, AMTL seal.", "Orientation, calmness, trust, and local runtime status."),
            ("Left menu", "Overview, Money Flow, Planning, Tools, Evidence, Chat, Reports, Admin.", "Grouped navigation that avoids long scrolling and keeps proof/admin away from normal use."),
            ("Middle column", "Primary segment buttons, subtabs, clickable counts, current work panel, exact named rows panel.", "The main action surface. Tabs replace one long page."),
            ("Right rail", "Contextual helper, Why this matters, Evidence, Next action, Safety, Selected thing, Why shown here, Safe boundary.", "Just-in-time help without generic 6W clutter."),
            ("Action bar", "Open exact rows, Create review receipt, Search evidence, Create local report, Route AI task, and other relevant buttons.", "Buttons do local work, create receipts, search evidence, or navigate."),
        ],
        [1.25, 2.8, 2.35],
    )

    add_heading(doc, "3. Full module stories", 1)
    for section_data in SECTIONS:
        group = section_data["group"]
        add_heading(doc, group, 2)
        add_body(doc, f"Menu story: Mani opens {group} because the question is: {section_data['question']} The app expands only this group and keeps the rest of the menu quiet.")
        for tab, copy in section_data["tabs"]:
            add_heading(doc, f"{group} > {tab}", 3)
            for para in module_story(group, tab, copy):
                add_body(doc, para)
            if group == "Overview" and tab == "Today":
                add_body(doc, "Buttons and fields: Mani sees Reminders, Scenarios, Evidence chunks, and Reports as clickable counts. He can click Open exact rows, Create review receipt, Search evidence, Timeline, or Evidence map.")
            elif group == "Money Flow" and tab == "Subscriptions":
                add_body(doc, "Buttons and fields: Mani uses Open exact rows to see recurring candidates, Annual cost to see yearly impact, Create review receipt to remember a decision, and Route AI task only for a gated local explanation or cancellation-route reasoning.")
            elif group == "Planning":
                add_body(doc, "Buttons and fields: Mani can open exact rows, compare assumptions, create a review receipt, or route an AI task when reasoning level needs more help. The result remains local unless explicitly approved.")
            elif group == "Evidence":
                add_body(doc, "Buttons and fields: Mani can Search evidence, Index NAS sources, open Evidence map, create a receipt, or open exact rows. Evidence stays local/internal.")
            elif group == "Reports":
                add_body(doc, "Buttons and fields: Mani clicks Create local report. The app creates a local report/export receipt and keeps external_send_state local.")
            elif group == "Admin":
                add_body(doc, "Buttons and fields: Mani can Show proof, Run audit loop, Copy privacy receipt, or inspect local runtime proof. These details are intentionally hidden from normal screens.")
            else:
                add_body(doc, "Buttons and fields: Mani gets the relevant action buttons for the tab, with exact rows in the detail panel and contextual explanation in the right rail.")

    add_heading(doc, "4. Button and panel stories", 1)
    for button, story in BUTTONS:
        add_heading(doc, button, 3)
        add_body(doc, f"Mani clicks {button}. {story}")
        add_body(doc, "The action output panel tells Mani what happened. If a receipt, report, audit, evidence result, or route was created, it shows the local result. If the action would require external sending, bank access, cancellation, payment, or regulated advice, the app blocks it or keeps it as a local preparation step.")

    add_heading(doc, "5. Runtime and evidence flow", 1)
    add_diagram(doc, "Local/internal runtime flow", [
        "UI click",
        "  -> FastAPI route under /api/personal-finance",
        "  -> PostgreSQL-only store",
        "  -> pgvector evidence search when evidence is requested",
        "  -> local receipt/report/audit row",
        "  -> UI output panel + exact rows + contextual helper",
        "  -> external actions remain blocked unless explicitly approved",
    ])
    add_body(doc, "The runtime story matters because CK Personal Finance is not a decorative dashboard. A button must either navigate, open rows, search local evidence, create a local receipt/report, run a proof/audit, or clearly state that the action is approval-gated.")

    add_heading(doc, "6. Boundary stories", 1)
    add_body(doc, "If Mani asks the app to cancel a subscription, the app can help find the cancellation route, draft a local support script, create a reminder, and track follow-up. It does not auto-cancel.")
    add_body(doc, "If Mani asks the app to connect to a bank, the app can explain that live bank/provider connection is approval-gated. It does not silently connect.")
    add_body(doc, "If Mani asks for financial advice, the app can organise evidence, explain rows, and build local scenarios. It does not provide regulated advice.")
    add_body(doc, "If Mani asks for AI help, OpenRouter routing selects free, modest, or full-expensive tiers by reasoning level. Provider execution remains gated unless explicitly allowed.")

    add_heading(doc, "7. Completeness checklist", 1)
    checklist = []
    for section_data in SECTIONS:
        for tab, _ in section_data["tabs"]:
            checklist.append((section_data["group"], tab, "Covered"))
    add_table(doc, ["Menu group", "Tab/screen", "Story status"], checklist, [1.6, 3.5, 1.2])

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = footer.add_run("CK Personal Finance Story Flow v0.4 - local/internal UI story map")
    style_run(r, 8, False, MUTED)

    doc.save(DOCX)
    print(DOCX)


if __name__ == "__main__":
    build()
