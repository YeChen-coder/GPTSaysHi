/* Same-page timing: first complete audio packet -> receive / decoded frame + rAF. */
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),base='http://127.0.0.1:19088';
const label=process.argv[2]||'current',pcmPath=process.argv[3];
const output=path.join(root,'results','engineering',label);fs.mkdirSync(output,{recursive:true});
const pcm=pcmPath?fs.readFileSync(pcmPath):Buffer.from(new Int16Array(Array.from({length:24000*2},(_,i)=>Math.round(Math.sin(i*2*Math.PI*220/24000)*2500))).buffer);
const median=values=>{const sorted=[...values].sort((a,b)=>a-b),middle=Math.floor(sorted.length/2);return sorted.length%2?sorted[middle]:(sorted[middle-1]+sorted[middle])/2};
(async()=>{
 const health=await(await fetch(base+'/health')).json();assert(health.ok&&!health.publisher);
 const range=await fetch(base+'/avatar/video',{headers:{Range:'bytes=100-199'}});
 assert.equal(range.status,206);assert.equal((await range.arrayBuffer()).byteLength,100);
 const executablePath=process.env.GPTSAYSHI_TEST_BROWSER||(process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':chromium.executablePath());
 const browser=await chromium.launch({headless:true,executablePath});
 const page=await browser.newPage({viewport:{width:800,height:1000}}),errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 await page.addInitScript(()=>{
  window.timing={sent:null,received:[],displayed:[],controls:[]};
  const Original=window.WebSocket;
  window.WebSocket=class extends Original {
   constructor(...args){super(...args);if(String(args[0]).includes('/view')){
    let control=null;
    this.addEventListener('message',event=>{
     if(typeof event.data==='string'){
      control=JSON.parse(event.data);window.timing.controls.push(control);
     }else window.timing.received.push({index:control.index,phase:control.phase||'speaking',ms:performance.now()-window.timing.sent});
    });
   }}
  };
  addEventListener('DOMContentLoaded',()=>{
   const image=document.getElementById('frame');
   new MutationObserver(records=>{
    if(!records.some(record=>record.attributeName==='src'))return;
    const index=Number(image.dataset.index),phase=image.dataset.phase;
    requestAnimationFrame(()=>window.timing.displayed.push({index,phase,ms:performance.now()-window.timing.sent}));
   }).observe(image,{attributes:true});
  });
 });
 const rounds=[];
 try{
  await page.goto(base);await page.waitForFunction(()=>document.getElementById('idle-video').currentTime>0);
  const duration=await page.locator('#idle-video').evaluate(video=>video.duration);
  assert.equal(duration,health.duration_seconds);
  for(let round=0;round<7;round++){
   await page.waitForFunction(()=>document.body.dataset.mode==='idle');
   await page.evaluate(async audio=>{
    const ws=new WebSocket(`ws://${location.host}/publish?source=test`);
    await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
    window.timing={sent:null,received:[],displayed:[],controls:[]};
    const bytes=Uint8Array.from(audio),begin=performance.now();
    for(let offset=0;offset<bytes.length;offset+=4800){
     const part=bytes.subarray(offset,offset+4800),packet=new ArrayBuffer(8+part.length);
     new DataView(packet).setFloat64(0,Date.now(),true);new Uint8Array(packet,8).set(part);
     if(window.timing.sent===null)window.timing.sent=performance.now();
     ws.send(packet);
     await new Promise(resolve=>setTimeout(resolve,Math.max(0,begin+(offset+part.length)/48-performance.now())));
    }
    await new Promise((resolve,reject)=>{
     const beginWait=performance.now();
     const timer=setInterval(()=>{
      if(window.timing.controls.some(item=>item.type==='idle')&&document.body.dataset.mode==='idle'){clearInterval(timer);resolve()}
      else if(performance.now()-beginWait>8000){clearInterval(timer);reject(Error('Idle handoff timed out'))}
     },20);
    });
    ws.close();await new Promise(resolve=>ws.addEventListener('close',resolve,{once:true}));
   },[...pcm.subarray(0,48000*1.6)]);
   const result=await page.evaluate(()=>window.timing);
   const speech=result.received.filter(frame=>frame.phase==='speaking');
   const settle=result.received.filter(frame=>frame.phase==='settling');
   assert.equal(speech.length,40);assert.equal(settle.length,health.settle_ms/40);
   assert(result.received.every((frame,i)=>!i||frame.index===(result.received[i-1].index+1)%health.base_frames));
   const firstDisplay=result.displayed.find(frame=>frame.phase==='speaking');assert(firstDisplay);
   rounds.push({round:round+1,first_arrival_ms:speech[0].ms,first_display_ms:firstDisplay.ms,
    speech_frames:speech.length,settle_frames:settle.length,displayed_frames:result.displayed.length});
  }
  await page.screenshot({path:path.join(output,'returned_idle.png')});
  assert.deepEqual(errors,[]);
 const report={passed:true,label,character:health.character,checkpoint_sha256:health.checkpoint_sha256,
   compositor:health.compositor,release:health.release,settle_ms:health.settle_ms,
   input:pcmPath?'Same local speech PCM, not a new Live call':'Generated local tone fixture',
   timing:'First complete 100 ms packet send -> receipt / decoded image assignment followed by rAF; excludes capture, packet filling, model load and physical screen scanout',
   rounds,steady_first_arrival_median_ms:median(rounds.slice(1).map(row=>row.first_arrival_ms)),
   steady_first_display_median_ms:median(rounds.slice(1).map(row=>row.first_display_ms)),
   range_requests:true,continuous_indices:true,idle_handoff:true,errors};
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
