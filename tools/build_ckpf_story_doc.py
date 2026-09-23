from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "reports" / "qa" / "ck-personal-finance-local-internal-270626"
OUT = QA / "CK-Personal-Finance-Complete-Story-Flow-270627.docx"

INK = RGBColor(17, 24, 39)
MUTED = RGBColor(85, 85, 85)
BLUE = RGBColor(45, 116, 181)
DARK_BLUE = RGBColor(31, 78, 121)
GREEN = RGBColor(18, 120, 86)
GOLD = RGBColor(122, 90, 0)
RED = RGBColor(155, 28, 28)

FILL_BLUE = "E8EEF5"
FILL_GREEN = "EAF6F0"
FILL_GOLD = "FFF6DA"
FILL_RED = "FCE8E6"
FILL_GREY = "F2F4F7"


def run_style(run, *, bold=False, italic=False, color=INK, size=11):
    run.bold = bold
    run.italic = italic
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    run.font.size = Pt(size)
    run.font.color.rgb = color


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def border(cell, color="DADCE0"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right"):
        tag = f"w:{edge}"
        node = borders.find(qn(tag))
        if node is None:
            node = OxmlElement(tag)
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "6")
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), color)


def margins(cell):
    tc_pr = cell._tc.get_or_add_tcPr()
    mar = tc_pr.first_child_found_in("w:tcMar")
    if mar is None:
        mar = OxmlElement("w:tcMar")
        tc_pr.append(mar)
    for name, value in (("top", 80), ("bottom", 80), ("start", 120), ("end", 120)):
        node = mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def table_width(table, widths):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl = table._tbl
    tbl_w = tbl.tblPr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl.tblPr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(widths)))
    tbl_w.set(qn("w:type"), "dxa")
    grid = tbl.tblGrid
    if grid is None:
        grid = OxmlElement("w:tblGrid")
        tbl.insert(0, grid)
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(widths[i]))
            tc_w.set(qn("w:type"), "dxa")
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            border(cell)
            margins(cell)


def setup(doc):
    sec = doc.sections[0]
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(11)
    for attr in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(sec, attr, Inches(1))
    sec.header_distance = Inches(0.492)
    sec.footer_distance = Inches(0.492)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    normal.font.size = Pt(11)
    normal.font.color.rgb = INK
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.25
    for name, size, color in (
        ("Heading 1", 16, BLUE),
        ("Heading 2", 13, BLUE),
        ("Heading 3", 12, DARK_BLUE),
    ):
        style = doc.styles[name]
        style.font.name = "Calibri"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        style.font.size = Pt(size)
        style.font.color.rgb = color
        style.font.bold = True
    header = sec.header.paragraphs[0]
    header.text = ""
    run_style(header.add_run("CK Personal Finance - Complete Story Flow Map"), color=MUTED, size=9)
    footer = sec.footer.paragraphs[0]
    footer.text = ""
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run_style(footer.add_run("Local/internal plus approved beyond-local safe paths - 27/06/26"), color=MUTED, size=9)


def h(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.space_before = Pt({1: 18, 2: 14, 3: 10}[level])
    p.paragraph_format.space_after = Pt({1: 8, 2: 6, 3: 4}[level])
    run_style(p.add_run(text), bold=True, color=BLUE if level < 3 else DARK_BLUE, size={1: 16, 2: 13, 3: 12}[level])


def p(doc, text):
    para = doc.add_paragraph()
    para.paragraph_format.line_spacing = 1.25
    para.paragraph_format.space_after = Pt(6)
    run_style(para.add_run(text), color=INK)


def bullet(doc, text):
    para = doc.add_paragraph(style="List Bullet")
    para.paragraph_format.left_indent = Inches(0.375)
    para.paragraph_format.first_line_indent = Inches(-0.188)
    para.paragraph_format.line_spacing = 1.15
    para.paragraph_format.space_after = Pt(3)
    run_style(para.add_run(text), color=INK)


def callout(doc, title, body, fill=FILL_BLUE, accent=BLUE):
    table = doc.add_table(rows=1, cols=1)
    table_width(table, [9360])
    cell = table.cell(0, 0)
    shade(cell, fill)
    para = cell.paragraphs[0]
    run_style(para.add_run(title), bold=True, color=accent)
    para2 = cell.add_paragraph()
    para2.paragraph_format.line_spacing = 1.15
    run_style(para2.add_run(body), color=INK, size=10.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def flow(doc, title, steps):
    callout(doc, title, "  ->  ".join(steps), FILL_GREY, DARK_BLUE)


def kv(doc, title, rows, fill=FILL_BLUE, widths=(2300, 7060)):
    h(doc, title, 3)
    table = doc.add_table(rows=1, cols=2)
    table_width(table, list(widths))
    table.rows[0].cells[0].text = "Item"
    table.rows[0].cells[1].text = "Story / behaviour"
    for cell in table.rows[0].cells:
        shade(cell, fill)
        for para in cell.paragraphs:
            for run in para.runs:
                run_style(run, bold=True, color=DARK_BLUE, size=10)
    for item, body in rows:
        cells = table.add_row().cells
        cells[0].text = item
        cells[1].text = body
        for cell in cells:
            border(cell)
            margins(cell)
            for para in cell.paragraphs:
                para.paragraph_format.line_spacing = 1.1
                para.paragraph_format.space_after = Pt(2)
                for run in para.runs:
                    run_style(run, color=INK, size=10)
    doc.add_paragraph().paragraph_format.space_after = Pt(3)


def story(doc, title, menu, user_goal, app_story, buttons=None, fields=None, proof=None, helper=None):
    h(doc, title, 2)
    callout(doc, "Where the user goes", menu, FILL_GREEN, GREEN)
    p(doc, f"The user wants to {user_goal}.")
    p(doc, app_story)
    if fields:
        kv(doc, "Fields and panels the user sees", fields, FILL_GREY)
    if buttons:
        kv(doc, "Buttons and what they do", buttons, FILL_BLUE)
    if proof:
        callout(doc, "What this proves", proof, FILL_GOLD, GOLD)
    if helper:
        callout(doc, "Right helper rail", helper, FILL_BLUE, DARK_BLUE)


def add_cover(doc):
    para = doc.add_paragraph()
    run_style(para.add_run("CK Personal Finance"), bold=True, color=BLUE, size=26)
    para = doc.add_paragraph()
    run_style(para.add_run("Complete Story Flow Map: every screen, panel, button, field, runtime path, and blocker"), color=INK, size=14)
    para = doc.add_paragraph()
    run_style(para.add_run("Prepared for Mani - 27/06/26"), color=MUTED, size=10)
    callout(
        doc,
        "Document promise",
        "This is a story-like walkthrough of CK Personal Finance. It uses the current app names: Overview, Money Flow, Planning, Evidence, Handoffs, Reports, Admin, Today, Budget, Scenarios, Evidence, Admin proof, Create review receipt, Search evidence, Index NAS sources, Route AI task, Create local report, Run audit loop, and Copy privacy receipt.",
    )
    callout(
        doc,
        "Current truth",
        "Safe product paths are implemented and proved: PostgreSQL-only runtime, pgvector RAG, approved NAS indexing, OpenRouter free/modest/expensive routing, Workshop registration, Beast route proof, browser QA, and five audit loops. Remaining blockers require real external targets or compliance/release decisions.",
        FILL_GREEN,
        GREEN,
    )
    desktop = QA / "desktop.png"
    if desktop.exists():
        doc.add_picture(str(desktop), width=Inches(6.3))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()


def add_contents(doc):
    h(doc, "Contents", 1)
    for item in [
        "Whole product shape",
        "Opening the app and first-screen story",
        "Header, navigation, centre panel, and helper rail",
        "Overview stories",
        "Money Flow stories",
        "Planning stories",
        "Evidence, RAG, and NAS indexing stories",
        "Handoffs and reports stories",
        "Admin, proof, Workshop, and Beast stories",
        "OpenRouter AI routing stories",
        "PostgreSQL and pgvector runtime stories",
        "Failure and blocker stories",
        "Mobile story",
        "End-to-end use cases",
        "Complete button and field catalogue",
        "What remains not app-complete because external targets are missing",
    ]:
        bullet(doc, item)
    doc.add_page_break()


def build_sections(doc):
    h(doc, "1. The Whole Product Shape", 1)
    p(doc, "CK Personal Finance is a calm money cockpit. The first job of the app is to show what needs attention, what changed, what evidence supports the view, and what can be safely done locally.")
    flow(doc, "Primary user journey", ["Open /sak/finance/", "Read prompt", "Choose menu", "Inspect exact rows", "Click safe button", "Receive receipt/evidence/proof", "Use helper rail"])
    kv(doc, "Main app areas", [
        ("Header", "AMTL logo, CK product mark, product name, money prompt, DD/MM/YY date, day, time, runtime/weather status, AMTL seal."),
        ("Left navigation", "Grouped collapsible menu: Overview, Money Flow, Planning, Evidence, Handoffs, Reports, Admin."),
        ("Centre work area", "Segment shortcuts and active work panel: Today, Budget, Scenarios, Evidence, Admin proof."),
        ("Metric buttons", "Clickable counts: Reminders, Scenarios, Evidence chunks, Reports."),
        ("Action bar", "Create review receipt, Search evidence, Index NAS sources, Route AI task, Create local report, Run audit loop, Copy privacy receipt."),
        ("Right helper rail", "Contextual WHAT, WHO, WHY, WHEN, HOW, WHERE, and ELI10 explanations."),
        ("Admin proof panel", "Hidden proof for Postgres, pgvector, RAG, OpenRouter, route, Workshop, Beast, and external-write boundaries."),
    ])

    h(doc, "2. Opening the App and First-Screen Story", 1)
    story(doc, "Opening http://amtl/sak/finance/", "Route: http://amtl/sak/finance/ -> CK Personal Finance cockpit", "understand what money situation needs attention today without being overwhelmed", "The app opens directly into the cockpit in this local/internal build. There is no full auth/login system yet; the current local route is the operator entry point. The first screen shows the brand header, grouped navigation, centre Today panel, clickable metric counts, action buttons, and right helper rail.", fields=[("AMTL logo", "Transparent AMTL logo at top-left."), ("CK product mark", "Local CK Personal Finance mark beside the product name."), ("Money prompt", "Context-aware next-best money prompt."), ("Date/time/status", "DD/MM/YY, day, local time, and Weather/status: local runtime healthy.")], proof="Desktop and mobile browser QA proved logos, seal, date/time/status, nav, segmented content, right rail, no console errors, and no overflow.", helper="The helper rail starts with Today explanations: what needs care first, who can see it, why it matters, when to use it, how to act, where data lives, and ELI10.")
    mobile = QA / "mobile.png"
    if mobile.exists():
        h(doc, "Mobile visual anchor", 3)
        doc.add_picture(str(mobile), width=Inches(3.0))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    h(doc, "3. Header, Navigation, Centre Panel, and Helper Rail", 1)
    story(doc, "Header story", "Top header area", "know this is the correct product and that the runtime is healthy", "The header shows the transparent AMTL logo, CK Personal Finance mark, product name, useful finance prompt, date, day, time, weather/status, and AMTL seal. It gives confidence before the user touches money data.", fields=[("Product identity", "AMTL logo + CK mark + CK Personal Finance title."), ("Prompt", "Useful money prompt, not filler."), ("Runtime status", "Weather/status line shows whether the app is healthy.")], proof="UI contract browser QA checks these items.")
    story(doc, "Left navigation story", "Grouped collapsible left navigation", "choose the right money task without scanning one long dashboard", "The user opens Overview, Money Flow, Planning, Evidence, Handoffs, Reports, or Admin. When the user clicks a menu item, the app highlights it, updates the breadcrumb/title, loads matching drilldown rows, and updates the helper rail.", fields=[("Overview", "Today, What changed."), ("Money Flow", "Accounts, Budget, Cashflow, Debt."), ("Planning", "Savings goals, Scenario planner, Alerts and reminders."), ("Evidence", "Evidence."), ("Handoffs", "Handoffs."), ("Reports", "Reports."), ("Admin", "Proof, Delivery matrix.")])
    story(doc, "Centre panel story", "Segment row: Today, Budget, Scenarios, Evidence, Admin proof", "jump to the highest-value work quickly", "The centre panel shows the active work list, exact named rows, metric cards, and action buttons. The segment row gives shortcuts without replacing the left navigation.", buttons=[("Today", "Daily attention view."), ("Budget", "Budget-related rows and helper explanations."), ("Scenarios", "Local what-if plans."), ("Evidence", "RAG evidence search and NAS indexing actions."), ("Admin proof", "Proof rows hidden from normal money work.")])
    story(doc, "Right helper rail story", "Right rail: WHAT, WHO, WHY, WHEN, HOW, WHERE, ELI10", "understand the selected thing without generic help text", "The user clicks a helper chip. The app explains the selected screen, row, button, account, scenario, receipt, or proof in context and points to the next useful action.", fields=[("WHAT", "What the selected thing is."), ("WHO", "Who it is for and who sees it."), ("WHY", "Why it matters."), ("WHEN", "When to use it."), ("HOW", "How to act safely."), ("WHERE", "Where data or proof lives."), ("ELI10", "A simple explanation.")])

    h(doc, "4. Overview Stories", 1)
    story(doc, "Overview > Today", "Left nav: Overview -> Today; segment: Today", "check what needs attention today", "The app shows tax evidence review, credit card clean-down, private health review, and similar rows. The user can click a metric count such as Reminders or Evidence chunks to open exact named rows.", buttons=[("Create review receipt", "Writes a local finance_decision_receipts row."), ("Search evidence", "Runs pgvector evidence search."), ("Route AI task", "Selects an OpenRouter tier without provider call by default.")], fields=[("Work row title", "Example: Tax evidence review."), ("Status", "Example: Due soon or Monthly."), ("Metric cards", "Reminders, Scenarios, Evidence chunks, Reports.")], proof="Today is covered by browser QA, route proof, and cockpit API proof.")
    story(doc, "Overview > What changed", "Left nav: Overview -> What changed", "see what changed since the last review", "The app shows local changes such as new receipts, report exports, NAS evidence chunks, audit receipts, and runtime proof changes. If nothing important changed, it stays quiet and points back to the next useful money action.", fields=[("Change type", "Receipt, report, NAS index, audit, runtime proof."), ("Source", "Local Postgres row or evidence file."), ("Useful action", "Open the related screen or create a receipt.")])

    h(doc, "5. Money Flow Stories", 1)
    story(doc, "Money Flow > Accounts", "Left nav: Money Flow -> Accounts", "inspect account groups and source state", "The app opens account-group rows such as Everyday account, Bills buffer, Credit card, and Super estimate. The app does not connect to a bank here; it helps the user understand which rows are local, manual, demo, or source-backed.", fields=[("name", "Account group name."), ("group_type", "cash, liability, super, or similar."), ("current_balance", "Current local balance."), ("source_state", "synthetic_demo_local, manual_local, or future imported/source-backed state.")], proof="Rows are read from personal_account_groups in Postgres.")
    story(doc, "Money Flow > Budget", "Left nav: Money Flow -> Budget; segment: Budget", "open budget rows behind the numbers", "The app shows named rows related to reminders, scenarios, and reports. The user clicks Explain beside a row and the helper rail explains why the row matters.", buttons=[("Explain", "Moves row context into the helper rail."), ("Search evidence", "Searches local pgvector evidence."), ("Create review receipt", "Stores a local review receipt.")], fields=[("Reminder rows", "title, due_date, status, source_ref."), ("Scenario rows", "name, scenario_type, inputs, outputs, boundary."), ("Report rows", "title, source_refs, external_send_state.")])
    story(doc, "Money Flow > Cashflow", "Left nav: Money Flow -> Cashflow", "understand cash movement without taking external action", "The app uses local scenarios, reminders, report exports, and evidence to help the user see likely movement. It does not move money or contact a bank.", buttons=[("Create local report", "Creates a report_exports row with external_send_state=not_sent."), ("Run audit loop", "Shows done/partial/blocked/missing counts.")])
    story(doc, "Money Flow > Debt", "Left nav: Money Flow -> Debt", "review a debt clean-down plan calmly", "The app shows debt plan rows, including the credit card clean-down. The helper explains interest pressure and comparison paths without giving regulated advice.", fields=[("name", "Debt plan name."), ("current_balance", "Current local balance."), ("repayment_amount", "Planned repayment amount."), ("repayment_frequency", "monthly or another cadence."), ("interest_rate", "Local planning reference."), ("status", "tracking or another state.")])

    h(doc, "6. Planning Stories", 1)
    story(doc, "Planning > Savings goals", "Left nav: Planning -> Savings goals", "translate future goals into today-sized choices", "The app opens savings goal rows such as Emergency buffer, Tax holding, and Future self fund.", fields=[("name", "Goal name."), ("target_amount", "Target amount."), ("saved_amount", "Saved amount."), ("target_date", "Date the user is working toward."), ("status", "tracking or another state.")], buttons=[("Create review receipt", "Records that the user reviewed the goal locally.")])
    story(doc, "Planning > Scenario planner", "Left nav: Planning -> Scenario planner; segment: Scenarios", "compare a what-if idea before doing anything in real life", "The app shows Subscription redirect, Debt snowball, and EOFY calm buffer. Each scenario has inputs, outputs, type, and a no-advice boundary.", fields=[("name", "Scenario name."), ("scenario_type", "savings, debt, tax, or similar."), ("inputs", "monthly_saving, extra_debt_payment, cancelled_subscriptions."), ("outputs", "Local outputs and calm summary."), ("boundary", "Local what-if only; confirm decisions with qualified professionals.")])
    story(doc, "Planning > Alerts and reminders", "Left nav: Planning -> Alerts and reminders", "see upcoming money review moments without noisy automation", "The app shows reminders with due date, cadence, lead days, status, and source reference.", fields=[("title", "Reminder title."), ("due_date", "When it is due."), ("cadence", "annual, monthly, or other rhythm."), ("lead_days", "How early it should surface."), ("status", "scheduled or reviewed."), ("source_ref", "Why this reminder exists.")])

    h(doc, "7. Evidence, RAG, and NAS Indexing Stories", 1)
    story(doc, "Evidence > Evidence search", "Left nav: Evidence -> Evidence; segment: Evidence", "search source-backed finance evidence", "The app searches finance_document_evidence using Postgres/pgvector. The user clicks Search evidence; the backend embeds the query, compares it with stored vectors, and returns source snippets.", buttons=[("Search evidence", "Calls /api/personal-finance/rag/search."), ("Index NAS sources", "Scans approved NAS roots and creates receipt."), ("Route AI task", "Routes the selected task through OpenRouter policy.")], fields=[("title", "Evidence chunk title."), ("document_type", "approved_source_doc or nas_source_doc."), ("source_path", "Local or NAS source path."), ("evidence_text", "Snippet or metadata text."), ("score", "Similarity score.")], proof="Current proof has 115 evidence chunks after NAS indexing.")
    story(doc, "Evidence > Index NAS sources", "Left nav: Evidence -> Evidence -> button: Index NAS sources", "expand evidence using approved NAS sources", "The app scans approved NAS roots and writes source chunks into Postgres/pgvector. It excludes only the two user-named prefixes. It creates a nas_source_index_receipts row and returns scanned_files, indexed_chunks, skipped_files, blocked_files, limit_reached, mode, and external_send=false.", fields=[("roots", "\\\\NAS2\\\\amtl-documents and \\\\NAS1\\\\Nas."), ("excluded_prefixes", "Only the two user-approved exclusions."), ("scanned_files", "Files scanned in this run."), ("indexed_chunks", "New chunks inserted."), ("blocked_files", "Files blocked by access/error."), ("limit_reached", "Whether bounded run stopped at max_files.")], proof="Proof run scanned 30 files, inserted 54 chunks, blocked 0, skipped 0, and excluded-path matches were 0. Browser QA clicked the button and received a receipt.")
    flow(doc, "NAS indexing data flow", ["Click Index NAS sources", "Scan approved roots", "Reject only two excluded prefixes", "Read chunks/PDF metadata", "Insert pgvector evidence", "Write receipt", "Show output"])
    nas = QA / "nas-index-browser.png"
    if nas.exists():
        doc.add_picture(str(nas), width=Inches(6.3))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    h(doc, "8. Handoffs and Reports Stories", 1)
    story(doc, "Handoffs > Draft handoffs", "Left nav: Handoffs -> Handoffs", "prepare a local draft for another AMTL app without mutating it", "The app shows draft handoff rows for Beast, Workshop, Elaine, Genie, Ripple, Spark, and CK Writer. These are local drafts only.", fields=[("target_app", "AMTL app name."), ("intent", "local_status_or_draft_only."), ("payload", "Draft payload."), ("state", "draft_local_only.")], proof="Rows are persisted in cross_app_handoffs; no receiver mutation is claimed.")
    story(doc, "Reports > Create report", "Left nav: Reports -> Reports -> button: Create local report", "create a local review pack without sending it anywhere", "The backend writes a report_exports row. The action output shows the report export ID and external_send_state=not_sent.", buttons=[("Create local report", "POST /api/personal-finance/reports."), ("Copy privacy receipt", "Copies the local privacy boundary.")], fields=[("report_type", "local_review_pack or requested type."), ("title", "CK Personal Finance local review pack."), ("payload", "Sections and source links."), ("external_send_state", "not_sent.")])

    h(doc, "9. Admin, Proof, Workshop, and Beast Stories", 1)
    story(doc, "Admin > Proof", "Left nav: Admin -> Proof; segment: Admin proof", "verify the product before trusting it or handing it off", "The app shows technical proof only in Admin. The user sees claim state, database, pgvector, RAG, OpenRouter, route, and external-write status.", fields=[("Claim", "DONE_LOCAL_INTERNAL or reason if not complete."), ("Database", "postgres; pass_active_runtime."), ("pgvector", "Version and embedding column."), ("RAG", "indexed_and_searchable and evidence chunk count."), ("OpenRouter", "Route policy and key-configured status."), ("External writes", "Disabled unless a real target contract exists.")])
    story(doc, "Admin > Delivery matrix", "Left nav: Admin -> Delivery matrix", "see row-by-row delivery truth", "The app shows 23 rows, all done for implementable safe paths. It includes core money workflows plus NAS source indexing, OpenRouter live route, and external action gates.", fields=[("id", "Machine-readable row id."), ("surface", "User-facing surface name."), ("status", "DONE, PARTIAL, BLOCKED, or NOT IMPLEMENTED."), ("implementation_location", "File or service where implemented."), ("evidence_path", "Where proof can be checked.")])
    story(doc, "Workshop registration story", "Workshop -> CK Personal Finance app card", "open, inspect, or health-check CK Personal Finance from Workshop", "Workshop has a CK Personal Finance row with product name, port 5124, friendly route, health endpoint, source path, evidence path, and status up.", fields=[("Product name", "CK Personal Finance."), ("Port", "5124."), ("Friendly route", "http://amtl/sak/finance/."), ("Health endpoint", "http://amtl/sak/finance/api/personal-finance/cockpit."), ("Status", "up.")])
    story(doc, "Beast / Port Sentinel story", "Beast Port Sentinel / Runtime Supervisor", "prove the port and route before claiming the friendly route", "The app does not claim /sak/finance/ from guesswork. Beast/Port Sentinel is checked, and the proof says the route maps to 127.0.0.1:5124 without hijacking another app route.", fields=[("Direct Beast health", "http://127.0.0.1:8780/health."), ("Direct port sentinel", "http://127.0.0.1:8780/port-sentinel."), ("AMTL port sentinel", "http://amtl/beast-api/port-sentinel."), ("Rollback", "Remove only CK Personal Finance route blocks and reload nginx.")])

    h(doc, "10. OpenRouter AI Routing Stories", 1)
    story(doc, "Route AI task", "Any relevant view -> button: Route AI task", "choose the right model strength without wasting money", "The app chooses the OpenRouter tier from reasoning level and max cost cap. By default it does not call a provider. It shows selected tier, model, and provider_called=false.", buttons=[("Route AI task", "Selects free, modest, or expensive tier; no provider call by default."), ("AI complete API", "Calls OpenRouter only with server-side key, execute=true, and allow_paid_provider=true.")], fields=[("reasoning_level", "low, medium, high, routine, normal, deep."), ("max_cost_tier", "free, modest, or expensive."), ("tier", "Selected tier after applying cap."), ("model", "openrouter/free, modest model, or expensive model."), ("provider_called", "false for route-only; true only for approved live call.")], proof="Browser QA proved Route AI task. Live free execution proved openrouter/free, returned a :free model, and cost 0.")
    flow(doc, "OpenRouter decision flow", ["Task asks for AI", "Classify reasoning", "Apply cost cap", "Select tier", "Route-only default", "Live call only with execute+approval", "Return content or fallback receipt"])
    ai = QA / "openrouter-routing-browser.png"
    if ai.exists():
        doc.add_picture(str(ai), width=Inches(6.3))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    h(doc, "11. PostgreSQL and pgvector Runtime Stories", 1)
    story(doc, "PostgreSQL-only runtime", "Backend store: app/services/personal_finance_store.py", "trust that CK Personal Finance is not relying on SQLite proof", "The app initialises the CK Personal Finance runtime against PostgreSQL. If Postgres/pgvector is unavailable, the app should show dependency-down repair truth rather than pretending to be complete.", fields=[("store", "postgres."), ("postgres_truth", "pass_active_runtime."), ("pgvector version", "0.8.3."), ("evidence chunks", "115 after approved NAS indexing."), ("sqlite_supported", "false.")], proof="Tests assert store_kind=postgres and DONE requires pgvector evidence.")
    kv(doc, "Postgres table story catalogue", [("personal_profiles", "Local profile, currency, timezone, demo_data flag."), ("personal_account_groups", "Account groups such as cash, liability, super."), ("savings_goals", "Goals, target amounts, saved amounts, dates, status."), ("debt_plans", "Debt balances, repayment amount/frequency, interest rate."), ("finance_decision_receipts", "Review receipts and local decision boundaries."), ("import_rollback_receipts", "Import/reconcile rollback proof path."), ("finance_document_evidence", "RAG evidence chunks with pgvector embeddings."), ("nas_source_index_receipts", "NAS indexing run receipts."), ("finance_reminders", "Due dates, cadence, lead days, source refs."), ("scenario_plans", "Local what-if inputs, outputs, and boundaries."), ("report_exports", "Local report packs with external_send_state."), ("field_helpers", "Field-level helper text and micro-actions."), ("cross_app_handoffs", "Draft-only AMTL handoff records."), ("audit_iterations", "Five-loop audit receipts.")], FILL_GREY)

    h(doc, "12. Failure and Blocker Stories", 1)
    for title, body, fill, accent in [
        ("Postgres down", "The app must show dependency-down repair truth and refuse to claim DONE. It must not silently switch to SQLite.", FILL_RED, RED),
        ("pgvector missing", "The app reports pgvector unavailable, RAG incomplete, and Admin proof shows repair state.", FILL_RED, RED),
        ("NAS unavailable", "Index NAS sources records blocked roots/files in a NAS receipt and keeps existing evidence searchable.", FILL_RED, RED),
        ("Excluded NAS path requested", "Files under either excluded prefix are skipped and never inserted into finance_document_evidence.", FILL_GOLD, GOLD),
        ("OpenRouter key missing", "Route AI task still selects the tier and returns local fallback with provider_called=false.", FILL_GOLD, GOLD),
        ("OpenRouter failure", "The app returns openrouter_unavailable or openrouter_http_error and does not hide provider failure.", FILL_RED, RED),
        ("Workshop or Beast unavailable", "The app stays honest: direct route may work, but Workshop/Beast proof is stale or unavailable until rechecked.", FILL_GOLD, GOLD),
        ("Gateway route failure", "The direct app may run, but friendly route proof fails. Repair only CK Personal Finance route blocks.", FILL_RED, RED),
    ]:
        callout(doc, title, body, fill, accent)
    kv(doc, "True external blockers", [("live_bank_cdr_connection", "Needs bank/CDR credential, consent artefact, account target, rollback plan, and live smoke target."), ("source_customer_system_write", "Needs destination system, credentials, schema contract, receiver acknowledgement, and rollback target."), ("regulated_financial_advice", "Needs qualified human/compliance workflow. The app can support evidence/scenarios but cannot become the adviser by code."), ("deploy_push_public_release", "Still blocked by the original hard rule for this window.")], FILL_RED)

    h(doc, "13. Mobile Story", 1)
    p(doc, "On mobile, the same story remains true but the layout stacks. The header compresses, logo and seal remain visible, navigation and work panel become a vertical flow, and the helper rail appears below or after active content.")
    flow(doc, "Mobile flow", ["Open app", "Header wraps cleanly", "Tap grouped nav", "Tap metric/button", "Read action output", "Scroll to helper/Admin proof"])
    callout(doc, "Mobile QA truth", "Mobile browser QA passed: logo, CK mark, seal, date/day/time/status, grouped navigation, segmented content, right rail, no generic 6W text, no console errors, and no horizontal overflow.", FILL_BLUE, BLUE)

    h(doc, "14. End-to-End Use Cases", 1)
    for title, steps in [
        ("Daily money check", ["Open /sak/finance/", "Read Today prompt", "Click Reminders metric", "Inspect due rows", "Create review receipt", "Use helper rail"]),
        ("Budget evidence check", ["Click Budget", "Click Search evidence", "Review pgvector result", "Create receipt if action is taken"]),
        ("Scenario comparison", ["Click Scenario planner", "Open a scenario", "Read inputs/outputs", "Route AI task if explanation is needed", "Create review receipt"]),
        ("NAS evidence refresh", ["Click Evidence", "Click Index NAS sources", "Exclude only two paths", "Write chunks and receipt", "Evidence count updates"]),
        ("Report creation", ["Click Reports", "Click Create local report", "Write report_exports row", "Show export ID and not_sent state"]),
        ("Admin verification", ["Click Admin proof", "Review runtime proof", "Run audit loop", "Compare done/partial/missing/blockers"]),
        ("OpenRouter free proof", ["Call approved AI complete path", "Select openrouter/free", "Provider returns free model", "Cost 0", "Record proof"]),
        ("External target request", ["User asks to connect bank/write source", "App checks target contract", "No target exists", "Show blocker and safe repair state"]),
    ]:
        flow(doc, title, steps)

    h(doc, "15. Complete Button and Field Catalogue", 1)
    kv(doc, "Buttons", [("Create review receipt", "Creates finance_decision_receipts row."), ("Search evidence", "Runs pgvector evidence search."), ("Index NAS sources", "Runs NAS indexing and shows scanned/indexed/skipped/blocked counts."), ("Route AI task", "Shows OpenRouter tier/model and provider_called=false by default."), ("Create local report", "Creates report_exports row with not_sent state."), ("Run audit loop", "Shows done/partial/blocked/missing."), ("Copy privacy receipt", "Copies no-advice/no-bank/OpenRouter-gated/no-external-write text."), ("Explain", "Moves row context into helper rail.")], FILL_BLUE)
    kv(doc, "Important fields", [("due_date", "When a reminder needs attention."), ("cadence", "Reminder rhythm."), ("source_ref", "Why a row exists."), ("source_path", "Where evidence came from."), ("evidence_text", "Snippet or metadata returned by RAG."), ("score", "pgvector similarity score."), ("external_send_state", "Current safe value is not_sent."), ("boundary", "No-advice/no-bank/no-external-write limits."), ("provider_called", "Whether OpenRouter was actually called."), ("cost", "OpenRouter cost when a live call is made."), ("excluded_prefixes", "The two NAS paths that must not be indexed."), ("excluded_path_matches", "Current matches are 0.")], FILL_GREY)

    h(doc, "16. What Remains Not App-Complete Because External Targets Are Missing", 1)
    callout(doc, "Important distinction", "There are no known implementable safe/local/approved NAS/OpenRouter code gaps after this pass. The remaining items need real external targets, credentials, consent, contracts, qualified human workflow, or a release decision.", FILL_GOLD, GOLD)
    kv(doc, "Remaining blockers and future slices", [("Bank/CDR connection", "Blocked until real target, credential, consent artefact, account scope, live smoke test, and rollback plan exist."), ("Source/customer write", "Blocked until destination system, credentials, schema contract, receiver acknowledgement, and rollback target exist."), ("Regulated advice", "Blocked until qualified adviser/compliance workflow exists."), ("Deploy/push/public release", "Blocked by hard rule for this window."), ("Full exhaustive NAS crawl", "Not claimed as complete. Current app has bounded repeatable indexer with receipts; true full crawl needs scheduler/progress/pause/resume/failure receipts."), ("Real login/roles", "Current local app opens directly to cockpit; full auth/roles need explicit design."), ("Backup/restore/delete/retention UI", "Future explicit product slice."), ("Settings/preferences UI", "Future explicit product slice for currency/timezone/helper visibility/model caps/source preferences.")], FILL_RED)


def main():
    doc = Document()
    setup(doc)
    add_cover(doc)
    add_contents(doc)
    build_sections(doc)
    props = doc.core_properties
    props.title = "CK Personal Finance Complete Story Flow Map"
    props.subject = "Screens, panels, buttons, fields, runtime and evidence stories"
    props.author = "AMTL Codex"
    props.comments = "Generated locally for Mani; no external send."
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
