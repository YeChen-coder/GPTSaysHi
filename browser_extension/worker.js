import {allowedChatGPT} from './policy.js';
let operation = Promise.resolve();
const serialized = action => {
  const next = operation.then(action, action);
  operation = next.catch(() => {});
  return next;
};
async function state() {
  return (await chrome.storage.session.get('capture')).capture || {active: false, message: 'Not connected'};
}
async function ensureOffscreen() {
  const contexts = await chrome.runtime.getContexts({contextTypes: ['OFFSCREEN_DOCUMENT']});
  if (!contexts.length) await chrome.offscreen.createDocument({url: 'offscreen.html',
    reasons: ['USER_MEDIA'], justification: 'Capture the selected ChatGPT tab audio for the local avatar'});
}
async function stop(message = 'Stopped') {
  await ensureOffscreen();
  await chrome.runtime.sendMessage({target: 'offscreen', type: 'stop'});
  await chrome.storage.session.set({capture: {active: false, message}});
  await chrome.action.setBadgeText({text: ''});
}
async function start(tabId) {
  const tab = await chrome.tabs.get(tabId);
  if (!allowedChatGPT(tab.url)) throw new Error('Connect from an HTTPS ChatGPT tab.');
  const response = await fetch('http://127.0.0.1:19088/health', {signal: AbortSignal.timeout(3000)});
  const health = await response.json();
  if (!health.ok || health.takeover_policy !== 'latest_connection') throw new Error('Start the GPTSaysHi avatar service first.');
  await ensureOffscreen();
  await stop('Switching tabs');
  const session = crypto.randomUUID();
  // This browser API requires the user to invoke this extension on the tab.
  const streamId = await chrome.tabCapture.getMediaStreamId({targetTabId: tabId});
  if (!allowedChatGPT((await chrome.tabs.get(tabId)).url)) throw new Error('The tab left ChatGPT. Connection canceled.');
  await chrome.storage.session.set({capture: {active: false, tabId, session, message: 'Connecting'}});
  const result = await chrome.runtime.sendMessage({target: 'offscreen', type: 'start', streamId, session});
  if (!result?.ok) {
    await stop(result?.error || 'Unable to connect tab audio');
    throw new Error(result?.error || 'Unable to connect tab audio');
  }
  const current = await state();
  if (current.session !== session || !allowedChatGPT((await chrome.tabs.get(tabId)).url)) {
    await stop('The tab changed. Connect again.');
    throw new Error('The tab changed. Connect again.');
  }
  await chrome.storage.session.set({capture: {...current, active: true, message: 'The current ChatGPT tab is connected'}});
  await chrome.action.setBadgeText({text: 'ON'});
  await chrome.action.setBadgeBackgroundColor({color: '#256d45'});
  return state();
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (sender.id !== chrome.runtime.id || message.target !== 'worker') return;
  if (message.type === 'capture-status') {
    state().then(async current => {
      if (message.session !== current.session) return;
      await chrome.storage.session.set({capture: {...current, ...message.status}});
      if (message.status.active === false) await chrome.action.setBadgeText({text: ''});
    }).catch(console.error);
    return;
  }
  const action = message.type === 'start' ? () => start(message.tabId) :
    message.type === 'stop' ? () => stop() : () => state();
  serialized(action).then(value => respond({ok: true, state: value}),
    error => respond({ok: false, error: error.message}));
  return true;
});
// Capture is tied to one document. Stop even on reload; SPA navigation within
// ChatGPT is fine. Loading another origin cannot become an audio source.
chrome.tabs.onUpdated.addListener((tabId, change) => {
  state().then(current => {
    if (current.tabId === tabId && (change.status === 'loading' ||
        (change.url !== undefined && !allowedChatGPT(change.url)))) {
      return serialized(() => stop('The page reloaded or left ChatGPT. Connect again.'));
    }
  }).catch(console.error);
});
chrome.tabs.onRemoved.addListener(tabId => {
  state().then(current => current.tabId === tabId && serialized(() => stop('The ChatGPT tab was closed'))).catch(console.error);
});
