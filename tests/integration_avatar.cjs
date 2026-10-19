/* Real viewer playback: loop boundaries, interruption, resume and reconnect. */
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const base='http://127.0.0.1:19088',root=path.resolve(__dirname,'..');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const opened=ws=>new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true})});
const output=path.join(root,'results','engineering','avatar');fs.mkdirSync(output,{recursive:true});
const source=process.argv[2]?fs.readFileSync(process.argv[2]):Buffer.from(new Int16Array(Array.from({length:2400},(_,i)=>Math.round(Math.sin(i*2*Math.PI*220/24000)*2500))).buffer);
async function stream(ws,seconds){
 const started=Date.now();
 for(let offset=0;offset<seconds*48000;offset+=4800){
  const part=Buffer.alloc(4800);
  for(let copied=0;copied<part.length;){
   const position=(offset+copied)%source.length,count=Math.min(source.length-position,part.length-copied);
   source.copy(part,copied,position,position+count);copied+=count;
  }
  const packet=Buffer.alloc(8+part.length);packet.writeDoubleLE(Date.now());part.copy(packet,8);ws.send(packet);
  await sleep(Math.max(0,started+(offset+part.length)/48-Date.now()));
 }
}
(async()=>{
 const before=await(await fetch(base+'/health')).json();assert(before.ok&&!before.publisher);
 assert.equal(before.frame_delivery,'incremental');assert.equal(before.lookahead_frames,0);assert.equal(before.history_seconds,4);
 assert(before.stream_warmup_seconds>0);
 const range=await fetch(base+'/avatar/video',{headers:{Range:'bytes=100-199'}});assert.equal(range.status,206);
 const browser=await chromium.launch({headless:true,executablePath:process.env.GPTSAYSHI_TEST_BROWSER||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const page=await browser.newPage({viewport:{width:800,height:1000}}),frames=[],controls=[],errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 let viewer,publisher;
 async function idle(){await page.waitForFunction(()=>document.body.dataset.mode==='idle'&&!document.getElementById('idle-video').paused,{}, {timeout:8000})}
 async function connect(){const ws=new WebSocket('ws://127.0.0.1:19088/publish?source=test');await opened(ws);return ws}
 try{
  await page.goto(base);await page.waitForFunction(()=>document.getElementById('idle-video').currentTime>0);
  assert.equal(await page.locator('#idle-video').evaluate(video=>video.duration),before.duration_seconds);
  await page.locator('#idle-video').evaluate(video=>new Promise(resolve=>{
   video.pause();video.addEventListener('seeked',resolve,{once:true});video.currentTime=video.duration-.25;
  }));
  await page.locator('#idle-video').evaluate(video=>video.play());
  await page.waitForFunction(()=>document.getElementById('idle-video').currentTime<1,{}, {timeout:3000});
  viewer=new WebSocket('ws://127.0.0.1:19088/view?protocol=2');await opened(viewer);
  viewer.addEventListener('message',event=>{if(typeof event.data==='string'){
   const control=JSON.parse(event.data);(control.type==='frame'?frames:controls).push(control);
  }});
  publisher=await connect();
  const start=frames.length,seconds=before.duration_seconds+1.2;
  const playback=stream(publisher,seconds);
  await page.waitForFunction(()=>document.body.dataset.mode==='speaking'&&document.getElementById('frame').naturalWidth>0);
  await page.screenshot({path:path.join(output,'speaking.png')});
  await playback;await idle();
  const complete=frames.slice(start),speech=complete.filter(frame=>!frame.phase),tail=complete.filter(frame=>frame.phase==='settling');
  assert.equal(speech.length,Math.round(seconds*25));assert.equal(tail.length,before.settle_ms/40);
  assert(complete.every((frame,i)=>!i||frame.index===(complete[i-1].index+1)%before.base_frames));
  assert(speech.some(frame=>frame.index===0)&&speech.some(frame=>frame.index===Math.floor(before.base_frames/2)));
  assert.equal(Number(await page.evaluate(()=>document.body.dataset.handoffIndex)),complete.at(-1).index);
  await page.screenshot({path:path.join(output,'returned_idle.png')});
  await stream(publisher,.8);publisher.send('{"type":"reset"}');await idle();
  const controlsStart=controls.length;
  await stream(publisher,.8);
  if(before.settle_ms>0){
   await page.waitForFunction(()=>document.body.dataset.mode==='settling',{}, {timeout:5000});
   await stream(publisher,.8);await idle();
   assert(controls.slice(controlsStart).some(control=>control.type==='resume'));
  }else{
   await idle();await stream(publisher,.8);await idle();
   assert(!controls.slice(controlsStart).some(control=>control.type==='settling'));
  }
  publisher.close();await sleep(600);
  publisher=await connect();const restart=frames.length;await stream(publisher,.8);await idle();
  assert.equal(frames.length-restart,20+before.settle_ms/40);
  publisher.close();await sleep(600);
  const after=await(await fetch(base+'/health')).json();
  assert(!after.error&&!after.publisher&&!after.speech_active);assert.deepEqual(errors,[]);
  const report={passed:true,character:after.character,range_requests:true,idle_seek_and_wrap:true,
   speech_frames:speech.length,settle_frames:tail.length,continuous_indices:true,both_loop_turns:true,
   interruption:true,resume_during_settle:before.settle_ms>0,repeated_speech:true,publisher_reconnect:true,
   handoff:before.idle_handoff,errors,health:after};
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{publisher?.close();viewer?.close();await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
