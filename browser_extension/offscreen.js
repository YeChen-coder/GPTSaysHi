import {AudioGate} from './audio_gate.js';
let capture = null;
async function stop(message = 'Stopped') {
  const old = capture; capture = null;
  if (!old) return;
  clearInterval(old.timer);
  old.node?.disconnect(); old.source?.disconnect();
  old.stream?.getTracks().forEach(track => track.stop());
  if (old.socket && old.socket.readyState < WebSocket.CLOSING) old.socket.close(1000, 'Capture stopped');
  if (old.context && old.context.state !== 'closed') await old.context.close();
  await chrome.runtime.sendMessage({target: 'worker', type: 'capture-status', session: old.session,
    status: {active: false, message, packets: old.gate?.packets || 0}}).catch(() => {});
}
async function start(message) {
  await stop();
  const current = {session: message.session}; capture = current;
  try {
    current.stream = await navigator.mediaDevices.getUserMedia({audio: {mandatory: {
      chromeMediaSource: 'tab', chromeMediaSourceId: message.streamId}}, video: false});
    if (capture !== current) throw new Error('Connection canceled');
    current.context = new AudioContext({sampleRate: 24000});
    if (current.context.sampleRate !== 24000) throw new Error('The browser did not provide 24 kHz audio');
    await current.context.audioWorklet.addModule('pcm_worklet.js');
    await current.context.resume();
    const sourceName = /Edg\//.test(navigator.userAgent) ? 'browser-edge' : 'browser-chrome';
    current.socket = new WebSocket('ws://127.0.0.1:19088/publish?source=' + sourceName);
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('The local avatar connection timed out')), 6000);
      current.socket.onopen = () => { clearTimeout(timer); resolve(); };
      current.socket.onerror = () => { clearTimeout(timer); reject(new Error('Could not connect to the local avatar')); };
      current.socket.onclose = () => { clearTimeout(timer); reject(new Error('The local avatar rejected the connection')); };
    });
    if (capture !== current) throw new Error('Connection canceled');
    current.socket.send('{"type":"reset"}');
    current.socket.onclose = event => {
      if (capture === current) void stop(event.code === 4001 ? 'Replaced by a newer source. Click Connect to switch back.' : 'Connection ended. Connect again.');
    };
    current.gate = new AudioGate(packet => {
      if (capture !== current || current.socket.readyState !== WebSocket.OPEN) return;
      if (current.socket.bufferedAmount > 4808 * 8) { void stop('Audio sending fell behind. Connect again.'); return; }
      current.socket.send(packet);
    });
    current.source = current.context.createMediaStreamSource(current.stream);
    current.node = new AudioWorkletNode(current.context, 'pcm24');
    current.node.port.onmessage = event => {
      if (capture === current) current.gate.push(event.data);
    };
    // tabCapture diverts the tab output. Restore it once so Live remains audible.
    current.source.connect(current.context.destination);
    current.source.connect(current.node);
    current.node.connect(current.context.destination); // silent output keeps the graph running
    current.stream.getTracks().forEach(track => track.addEventListener('ended', () => {
      if (capture === current) void stop('Tab audio ended');
    }));
    current.timer = setInterval(() => {
      chrome.runtime.sendMessage({target: 'worker', type: 'capture-status', session: current.session,
        status: {packets: current.gate.packets, chunks: current.gate.chunks, maxRms: current.gate.maxRms,
          audioState: current.context.state, sampleRate: current.context.sampleRate}}).catch(() => {});
    }, 1000);
    return {ok: true};
  } catch (error) {
    if (capture === current) await stop(error.message);
    return {ok: false, error: error.message};
  }
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (sender.id !== chrome.runtime.id || message.target !== 'offscreen') return;
  (message.type === 'start' ? start(message) : stop().then(() => ({ok: true}))).then(respond,
    error => respond({ok: false, error: error.message}));
  return true;
});
