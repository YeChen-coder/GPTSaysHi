/* Isolated Chromium profile, local fixtures only: no ChatGPT session access. */
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const ROOT=path.resolve(__dirname,'..');
const base='http://127.0.0.1:19088',sleep=ms=>new Promise(r=>setTimeout(r,ms));
const variant=process.argv[2]||'chromium';
const executables={chromium:chromium.executablePath(),
 chrome:'C:/Program Files/Google/Chrome/Application/chrome.exe',
 edge:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'};
const output=path.join(ROOT,'results/browser_extension',variant);fs.mkdirSync(output,{recursive:true});
function fixtureTone(){
 const samples=24000*5,buffer=Buffer.alloc(44+samples*2);
 buffer.write('RIFF');buffer.writeUInt32LE(buffer.length-8,4);buffer.write('WAVEfmt ',8);
 buffer.writeUInt32LE(16,16);buffer.writeUInt16LE(1,20);buffer.writeUInt16LE(1,22);
 buffer.writeUInt32LE(24000,24);buffer.writeUInt32LE(48000,28);buffer.writeUInt16LE(2,32);
 buffer.writeUInt16LE(16,34);buffer.write('data',36);buffer.writeUInt32LE(samples*2,40);
 for(let i=0;i<samples;i++)buffer.writeInt16LE(Math.round(Math.sin(i*2*Math.PI*220/24000)*2500),44+i*2);
 return buffer;
}
(async()=>{
 const extension=path.join(ROOT,'browser_extension');
 const context=await chromium.launchPersistentContext(path.join(output,'profile'),{
  executablePath:executables[variant],
  headless:true,args:[
   '--autoplay-policy=no-user-gesture-required','--enable-unsafe-extension-debugging'],ignoreDefaultArgs:['--disable-extensions','--mute-audio']});
 try{
  const browserCDP=await context.browser().newBrowserCDPSession();
  const loaded=await browserCDP.send('Extensions.loadUnpacked',{path:extension});
  const worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker',{timeout:15000});
  const id=worker.url().split('/')[2];assert.equal(id,loaded.id);console.log(variant+' extension loaded: '+id);
  await context.route('https://chatgpt.com/**',route=>{
   if(route.request().url().endsWith('/voice.wav'))return route.fulfill({contentType:'audio/wav',body:fixtureTone()});
   return route.fulfill({contentType:'text/html',body:'<!doctype html><title>Local ChatGPT-origin test fixture</title><audio id="voice" src="/voice.wav"></audio><button onclick="voice.volume=.15;voice.play()">Play fixture</button>'});
  });
  await context.route('https://example.com/**',route=>route.fulfill({contentType:'text/html',body:'<title>Unrelated local fixture</title><button onclick="const c=new AudioContext();const o=c.createOscillator();const g=c.createGain();g.gain.value=.02;o.frequency.value=880;o.connect(g);g.connect(c.destination);o.start();window.audio=c;">Other tab sound</button>'}));
  const target=await context.newPage();await target.goto('https://chatgpt.com/c/local-test');
  const other=await context.newPage();await other.goto('https://example.com/');
  await target.bringToFront();
  const tabs=await worker.evaluate(()=>chrome.tabs.query({}));
  const tab=tabs.find(tab=>tab.url==='https://chatgpt.com/c/local-test');assert(tab);
  const popup=await context.newPage();await popup.goto(`chrome-extension://${id}/popup.html`);
  const policy=await popup.evaluate(async()=>{
   const {allowedChatGPT}=await import('./policy.js');
   return {valid:allowedChatGPT('https://chatgpt.com/g/g-x/project'),invalid:[
    'https://chatgpt.com.evil.test','http://chatgpt.com','https://example.com',
    'https://chatgpt.com@evil.test','https://chatgpt.com:8443','not-a-url'].map(allowedChatGPT)};
  });assert(policy.valid&&policy.invalid.every(x=>!x));
  await popup.screenshot({path:path.join(output,'popup.png')});
  await target.bringToFront();
  const before=await(await fetch(base+'/health')).json();
  // Invoke the real extension action on the fixture tab to grant activeTab.
  const targets=await browserCDP.send('Target.getTargets',{filter:[{type:'tab'}]});
  const tabTarget=targets.targetInfos.find(t=>t.url===target.url());
  assert(tabTarget,JSON.stringify(targets));
  await browserCDP.send('Extensions.triggerAction',{id,targetId:tabTarget.targetId});
  const result=await popup.evaluate(tabId=>chrome.runtime.sendMessage({target:'worker',type:'start',tabId}),tab.id);
  console.log('Capture result: '+JSON.stringify(result));assert(result.ok,result.error);
  const state=()=>worker.evaluate(async()=> (await chrome.storage.session.get('capture')).capture);
  await other.locator('button').click();await sleep(2000);
  const silent=await state();assert.equal(silent.packets||0,0,'Unrelated tab audio was captured');
  await target.locator('button').click();await sleep(2800);
  const audible=await state();console.log(JSON.stringify({audible,voice:await target.locator('#voice').evaluate(v=>({time:v.currentTime,paused:v.paused,ready:v.readyState,error:v.error?.message}))}));assert(audible.packets>=10,'ChatGPT-origin fixture audio not received');
  const captures=await worker.evaluate(()=>chrome.tabCapture.getCapturedTabs());
  assert.equal(captures.filter(c=>c.status==='active').length,1);
  assert.equal(captures.find(c=>c.status==='active').tabId,tab.id);
  const after=await(await fetch(base+'/health')).json();
  assert.equal(after.source,variant==='edge'?'browser-edge':'browser-chrome');assert(after.frames_rendered>before.frames_rendered&&!after.error);
  // An app connection must stop the extension; it must never reconnect itself.
  const replacement=new WebSocket('ws://127.0.0.1:19088/publish?source=classic');
  await new Promise((resolve,reject)=>{replacement.onopen=resolve;replacement.onerror=reject});
  await sleep(1300);assert.equal((await state()).active,false);
  assert.equal((await(await fetch(base+'/health')).json()).source,'classic');
  // Explicit user reactivation is allowed to become the newest source again.
  await target.bringToFront();
  await browserCDP.send('Extensions.triggerAction',{id,targetId:tabTarget.targetId});
  const again=await popup.evaluate(tabId=>chrome.runtime.sendMessage({target:'worker',type:'start',tabId}),tab.id);
  assert(again.ok,again.error);await sleep(700);
  assert.equal((await(await fetch(base+'/health')).json()).source,variant==='edge'?'browser-edge':'browser-chrome');
  replacement.close();
  // Navigation must revoke capture even though the extension API can continue.
  await target.goto('https://example.com/left-chatgpt');await sleep(1300);
  const stopped=await state();assert.equal(stopped.active,false);
  const health=await(await fetch(base+'/health')).json();assert(!health.publisher&&!health.error);
  const report={passed:true,engine:variant+' '+context.browser().version(),isolated_test_profile:true,real_live_call:false,
    fixtures_only:true,exact_host_validation:true,actual_tab_capture:true,
    unrelated_tab_audible_but_no_packets:true,target_packets:audible.packets,
    frames_generated:after.frames_rendered-before.frames_rendered,one_target_tab:true,
    navigation_stops_capture:true,superseded_browser_stops:true,no_reconnect_fight:true,
    explicit_reactivation:true,sample_rate:audible.sampleRate,health};
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await context.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
