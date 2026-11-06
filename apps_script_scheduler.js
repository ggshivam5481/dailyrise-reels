// DailyRise reel scheduler (Google Apps Script).
// GitHub's own cron is unreliable, so Google's clock starts the GitHub workflows instead.
// Setup once: Project Settings > Script properties > add GH_TOKEN = your github_pat_... token,
// then run setup() once and allow the permissions.
const REPO = 'ggshivam5481/dailyrise-reels';
const JOBS = [
  // [IST start "HH:MM", window minutes, workflow file, inputs]
  ['05:50', 12, 'post.yml', {}],                       // waits inside and posts at 06:00
  ['17:50', 12, 'post.yml', {}],                       // waits inside and posts at 18:00
  ['01:00', 30, 'batch.yml', {count: '35', auto: '1'}], // nightly 35 reels
];

function dispatch_(workflow, inputs) {
  const token = PropertiesService.getScriptProperties().getProperty('GH_TOKEN');
  const res = UrlFetchApp.fetch(
    'https://api.github.com/repos/' + REPO + '/actions/workflows/' + workflow + '/dispatches', {
      method: 'post',
      contentType: 'application/json',
      headers: {Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json'},
      payload: JSON.stringify({ref: 'main', inputs: inputs}),
      muteHttpExceptions: true,
    });
  console.log(workflow + ' -> HTTP ' + res.getResponseCode() + ' ' + res.getContentText());
  return res.getResponseCode() === 204;
}

function minutesOf_(hhmm) {
  const p = hhmm.split(':');
  return Number(p[0]) * 60 + Number(p[1]);
}

// Runs every 5 minutes; fires each job once per day inside its window.
function tick() {
  const now = new Date();
  const day = Utilities.formatDate(now, 'Asia/Kolkata', 'yyyy-MM-dd');
  const nowMin = minutesOf_(Utilities.formatDate(now, 'Asia/Kolkata', 'HH:mm'));
  const props = PropertiesService.getScriptProperties();
  JOBS.forEach(function (job) {
    const start = minutesOf_(job[0]);
    if (nowMin < start || nowMin >= start + job[1]) return;
    const key = 'done_' + job[0] + '_' + job[2];
    if (props.getProperty(key) === day) return;
    if (dispatch_(job[2], job[3])) props.setProperty(key, day);
  });
}

// Run once: creates the 5-minute trigger.
function setup() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('tick').timeBased().everyMinutes(5).create();
  console.log('Scheduler ready. Token set: ' + !!PropertiesService.getScriptProperties().getProperty('GH_TOKEN'));
}

// Optional manual test: starts the post workflow now (it exits if nothing is due).
function testPost() {
  dispatch_('post.yml', {});
}
