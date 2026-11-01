CK PERSONAL FINANCE - NATIVE WINDOWS VALIDATION KIT (RB6g build)
================================================================
Purpose: run the native Windows validation runbook automatically on a
clean Windows 10 or 11 PC or VM and produce an evidence bundle.

WHAT YOU NEED
- A clean 64-bit Windows 10/11 machine or VM (no Python, Tesseract,
  Poppler or Ollama installed). A VM snapshot so you can restore clean
  state afterwards is ideal.
- The candidate zip under test: ck-personal-finance-windows-v1.0.zip
  (RB6g build; expected sha256 is printed by the script and checked).
- This kit folder.

HOW TO RUN
1. Copy this kit folder and the candidate zip onto the clean machine.
2. Put the candidate zip next to Run-Validation.bat (same folder).
3. Double-click Run-Validation.bat.
   - If SmartScreen or a firewall prompt appears at any point, record
     the exact wording (screenshot) before choosing anything. Choose
     "Run anyway" for SmartScreen; choose Cancel on any firewall prompt
     (the app must work without network access).
4. The script pauses up to 7 times and tells you which screenshot to
   take (S-A to S-G). Save each screenshot into the results folder the
   script creates (ck-validation-results-<timestamp>, next to the kit),
   then press Enter to continue.
5. When it finishes it prints a PASS/FAIL summary. Send back:
   - the whole ck-validation-results-<timestamp> folder
   - your screenshots if you saved them elsewhere
   The folder contains SUMMARY.txt, results.json, a run log, every
   captured output, and RESULTS-MANIFEST.txt with sha256 of each file.

WHAT IT TOUCHES
- Extracts the zip to C:\ck-test and runs the app from there.
- Uses only 127.0.0.1:5002 (loopback). No internet access needed.
- Uploads only the three synthetic fixture bills in fixtures\
  (bill.png, bill-4frame.tif, bill-2page.pdf). No real data anywhere.
- Ends by deleting the app's data folder via the app's own
  Remove-Data.bat, leaving no records behind.
- Takes about 10-15 minutes, mostly OCR time and pauses for screenshots.

IF SOMETHING FAILS
The script stops at the first FAIL step on purpose. Do not retry or
improvise fixes. Send back the results folder as-is; the log and
captured outputs are the evidence.
