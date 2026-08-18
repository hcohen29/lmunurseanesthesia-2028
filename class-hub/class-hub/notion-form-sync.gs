// ============================================================
// Class Hub → Notion Feedback Log Sync
// Paste this entire file into your Google Form's Apps Script
// editor (Extensions → Apps Script), then run createTrigger()
// once to activate it.
// ============================================================

const NOTION_TOKEN = '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';
const DATABASE_ID  = 'ae53a511f3dc496ab5bc23938d7d6494';

// Maps "Is this time sensitive?" answer → Notion Priority
function mapPriority(answer) {
  if (!answer) return 'Low';
  if (answer.startsWith('Yes')) return 'High';
  return 'Low';
}

// Maps follow-up answer → Notion From
function mapFrom(answer) {
  if (!answer) return 'Anonymous';
  return answer.startsWith('Yes') ? 'Classmate' : 'Anonymous';
}

function onFormSubmit(e) {
  const responses = e.response.getItemResponses();

  // Build answer map keyed by question title
  const ans = {};
  responses.forEach(r => {
    ans[r.getItem().getTitle()] = r.getResponse() || '';
  });

  const submissionType = ans['What kind of submission is this?']             || '';
  const title          = ans["What's this about?"]                          || (submissionType ? submissionType + ' — ' + new Date().toLocaleDateString() : 'Submission — ' + new Date().toLocaleDateString());
  const context        = ans['Please provide some context surrounding this'] || '';
  const outcome        = ans['What outcome would you like to see?']         || '';
  const timeSensitive  = ans['Is this time sensitive?']                     || '';
  const followUp       = ans['Would you like us to follow up with you?']    || '';
  const name           = ans['Name']                                        || '';
  const contactMethod  = ans['If yes']                                      || '';
  const contactInfo    = [name, contactMethod].filter(Boolean).join(' — ')  || '';
  const shareOnHub     = ans['Is this something you\'re comfortable with us sharing on the hub if posted anonymously?'] || '';

  const today = new Date().toISOString().split('T')[0];

  const payload = {
    parent: { database_id: DATABASE_ID },
    properties: {
      // Title
      'Issue': {
        title: [{ text: { content: title } }]
      },
      // Submission type (Idea / Concern / Request / Question)
      'Submission Type': {
        select: submissionType ? { name: submissionType } : null
      },
      // Full context
      'Context': {
        rich_text: [{ text: { content: context } }]
      },
      // Desired outcome
      'Desired Outcome': {
        rich_text: [{ text: { content: outcome } }]
      },
      // Priority mapped from time-sensitivity
      'Priority': {
        select: { name: mapPriority(timeSensitive) }
      },
      // Anonymous vs named
      'From': {
        select: { name: mapFrom(followUp) }
      },
      // Contact info (only populated if they opted in)
      'Contact Info': {
        rich_text: contactInfo ? [{ text: { content: contactInfo } }] : []
      },
      // Channel — always Intake Form when coming from Google Form
      'Channel': {
        select: { name: 'Intake Form' }
      },
      // Status always starts as Not started
      'Status': {
        status: { name: 'Not started' }
      },
      // Date received
      'Date Received': {
        date: { start: today }
      },
      // Date added — auto-set to submission date for form entries
      'Date Added': {
        date: { start: today }
      },
      // OK to share on hub
      'OK to Share on Hub': {
        select: shareOnHub.toLowerCase().startsWith('yes') ? { name: 'Yes' } : shareOnHub.toLowerCase().startsWith('no') ? { name: 'No' } : null
      }
    }
  };

  // Remove null select values (unanswered optional selects)
  if (!submissionType) delete payload.properties['Submission Type'];
  if (!payload.properties['OK to Share on Hub'].select) delete payload.properties['OK to Share on Hub'];

  const options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'Authorization': 'Bearer ' + NOTION_TOKEN,
      'Notion-Version': '2022-06-28'
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch('https://api.notion.com/v1/pages', options);
  const code     = response.getResponseCode();

  if (code !== 200) {
    console.error('Notion API error ' + code + ': ' + response.getContentText());
  } else {
    console.log('Submission synced to Notion successfully.');
  }
}

// Run this function ONCE manually to register the trigger.
// After that it fires automatically on every form submission.
function createTrigger() {
  // Remove any existing triggers first to avoid duplicates
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'onFormSubmit') {
      ScriptApp.deleteTrigger(t);
    }
  });

  ScriptApp.newTrigger('onFormSubmit')
    .forForm(FormApp.getActiveForm())
    .onFormSubmit()
    .create();

  console.log('Trigger created. Form submissions will now sync to Notion.');
}
