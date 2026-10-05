import {allowedChatGPT} from './policy.js';
const status = document.getElementById('status'), start = document.getElementById('start');
let tab;
async function refresh() {
  [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
  start.disabled = !allowedChatGPT(tab?.url);
  const result = await chrome.runtime.sendMessage({target: 'worker', type: 'state'});
  status.textContent = result.state?.message || result.error || 'Not connected';
  if (result.state?.active) status.textContent += ` (${result.state.packets || 0} audio packets sent)`;
  if (start.disabled) status.textContent += '. Switch to a ChatGPT tab and open this extension.';
}
start.onclick = async () => {
  start.disabled = true; status.textContent = 'Connecting…';
  try {
    const result = await chrome.runtime.sendMessage({target: 'worker', type: 'start', tabId: tab.id});
    if (!result.ok) throw new Error(result.error);
    await refresh();
  } catch (error) { status.textContent = error.message; start.disabled = false; }
};
document.getElementById('stop').onclick = async () => {
  await chrome.runtime.sendMessage({target: 'worker', type: 'stop'}); await refresh();
};
refresh().catch(error => {status.textContent = error.message;});
