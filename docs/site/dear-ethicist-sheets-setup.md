# Dear Ethicist — Google Sheets Data Collection Setup

## 1. Create the Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a new spreadsheet
2. Name it: `Dear Ethicist SQND Data`
3. Set up headers in Row 1:

| A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| session_id | timestamp | letter_id | party_1_name | party_1_role | party_1_assigned | party_1_expected | party_2_name | party_2_role | party_2_assigned | party_2_expected | party_3_name | party_3_assigned | correlative_holds | time_spent_seconds | bond_index |

## 2. Deploy the Apps Script

1. In the spreadsheet, go to **Extensions > Apps Script**
2. Replace the default code with the code below
3. Click **Deploy > New deployment**
4. Select type: **Web app**
5. Set "Execute as": **Me**
6. Set "Who has access": **Anyone**
7. Click **Deploy** and copy the URL

## 3. Apps Script Code

```javascript
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var data = JSON.parse(e.postData.contents);
  var rows = data.rows;

  rows.forEach(function(row) {
    sheet.appendRow([
      row.session_id,
      row.timestamp,
      row.letter_id,
      row.party_1_name,
      row.party_1_role,
      row.party_1_assigned,
      row.party_1_expected,
      row.party_2_name,
      row.party_2_role,
      row.party_2_assigned,
      row.party_2_expected,
      row.party_3_name,
      row.party_3_assigned,
      row.correlative_holds,
      row.time_spent_seconds,
      row.bond_index,
    ]);
  });

  return ContentService
    .createTextOutput(JSON.stringify({ status: 'ok', count: rows.length }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({ status: 'ok', message: 'Dear Ethicist SQND endpoint active' }))
    .setMimeType(ContentService.MimeType.JSON);
}
```

## 4. Connect to the Game

After deploying, copy the web app URL (looks like `https://script.google.com/macros/s/XXXXXXX/exec`).

Open `assets/js/dear-ethicist-game.js` and set the `SHEETS_ENDPOINT` variable:

```javascript
var SHEETS_ENDPOINT = 'https://script.google.com/macros/s/YOUR_DEPLOY_ID/exec';
```

## 5. Data Format

Each row in the sheet represents one letter verdict:

- **session_id**: UUID for the play session
- **timestamp**: ISO 8601 when the verdict was submitted
- **letter_id**: Probe identifier (e.g., `gate_promise_baseline`, `corr_borrow_lender`)
- **party_N_assigned**: Player's Hohfeldian classification (O/C/L/N)
- **party_N_expected**: Ground truth if known (empty for ambiguous probes)
- **correlative_holds**: TRUE/FALSE/empty — whether the O↔C or L↔N symmetry held
- **time_spent_seconds**: Deliberation time per letter
- **bond_index**: Session-level Bond Index (same for all rows in a session)

## 6. Analysis

The data maps directly to the SQND probe analysis pipeline. Key analyses:

- **Gate detection**: Compare `party_N_assigned` vs `party_N_expected` across gate levels
- **Correlative symmetry**: Aggregate `correlative_holds` by letter category
- **Bond Index distribution**: Histogram of session-level Bond Index values
- **Deliberation time**: Correlation between `time_spent_seconds` and symmetry violations
- **Bias detection**: Compare same-structure letters with different framing (e.g., `bias_omission_action` vs `bias_omission_inaction`)
