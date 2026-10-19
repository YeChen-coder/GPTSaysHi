/* Same browser video frame with/without the actual generated mouth PNG. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'results/color-20261019');fs.mkdirSync(out,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.GPTSAYSHI_TEST_BROWSER||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 let publisher;
 try{
 const page=await browser.newPage({viewport:{width:960,height:1088}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:19088/');await page.waitForFunction(()=>document.getElementById('idle-video').currentTime>0);
 const health=await(await fetch('http://127.0.0.1:19088/health')).json();assert.equal(health.frame_transport,'mouth_png');assert.equal(health.idle_color_space,'bt709');
 publisher=new WebSocket('ws://127.0.0.1:19088/publish?source=test');await new Promise((r,j)=>{publisher.onopen=r;publisher.onerror=j});
 const raw=fs.readFileSync(process.argv[2]||path.join(root,'results/migration-20261019/speech_12.pcm'));
 for(let i=0;i<20;i++){const packet=Buffer.alloc(4808);packet.writeDoubleLE(Date.now());raw.copy(packet,8,i*4800,(i+1)*4800);publisher.send(packet);await sleep(100)}
 await page.waitForFunction(()=>document.body.dataset.mode==='idle'&&document.getElementById('frame').naturalWidth>0);
 publisher.close();await sleep(150);
 const snapshot=await page.evaluate(async()=>{
  const v=document.getElementById('idle-video'),img=document.getElementById('frame');v.pause();
  const index=Number(img.dataset.index),seek=new Promise(r=>v.addEventListener('seeked',r,{once:true}));v.currentTime=(index+.1)/25;await seek;await new Promise(r=>setTimeout(r,100));await img.decode();
  const c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;c.getContext('2d').drawImage(img,0,0);
  const r=img.getBoundingClientRect();img.style.opacity='0';return {index,box:{x:r.x,y:r.y,width:r.width,height:r.height},patch:c.toDataURL('image/png')};
 });
 const before=await page.screenshot({path:path.join(out,'native.png')});await page.evaluate(()=>document.getElementById('frame').style.opacity='1');
 const after=await page.screenshot({path:path.join(out,'with-mouth.png')});
 const result=await page.evaluate(async({a,b,snapshot})=>{
  const load=async src=>{const i=new Image();i.src=src;await i.decode();const c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;c.getContext('2d').drawImage(i,0,0);return {pixels:c.getContext('2d').getImageData(0,0,c.width,c.height).data,w:c.width,h:c.height}};
  const A=await load(a),B=await load(b),P=await load(snapshot.patch);let outside=0,maxOutside=0,inside=0;
  const x0=Math.round(snapshot.box.x),y0=Math.round(snapshot.box.y);
  for(let y=0;y<A.h;y++)for(let x=0;x<A.w;x++){
   const px=x-x0,py=y-y0,mask=px>=0&&py>=0&&px<P.w&&py<P.h&&P.pixels[(py*P.w+px)*4+3]>0,k=(y*A.w+x)*4;
   const d=Math.max(Math.abs(A.pixels[k]-B.pixels[k]),Math.abs(A.pixels[k+1]-B.pixels[k+1]),Math.abs(A.pixels[k+2]-B.pixels[k+2]));
   if(d){if(mask)inside++;else {outside++;maxOutside=Math.max(maxOutside,d)}}
  }
  return {outside_mouth_changed_pixels:outside,outside_mouth_max_difference:maxOutside,inside_changed_pixels:inside};
 },{a:'data:image/png;base64,'+before.toString('base64'),b:'data:image/png;base64,'+after.toString('base64'),snapshot});
 assert.equal(result.outside_mouth_changed_pixels,0);assert(result.inside_changed_pixels>0);assert.deepEqual(errors,[]);
 const report={passed:true,character:health.character,release:health.release,same_native_frame:snapshot.index,...result,transport:health.frame_transport,errors};
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{publisher?.close();await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
