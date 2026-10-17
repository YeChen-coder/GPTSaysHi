"""Wall-clock streaming and steady working-set check; generated tone by default."""
import argparse
import asyncio
import json
import math
import re
import struct
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

import websockets

ROOT=Path(__file__).resolve().parents[1]

def health():
    with urlopen('http://127.0.0.1:19088/health',timeout=3) as response:return json.load(response)

def rss_kib():
    status=subprocess.check_output(['docker','exec','gptsayshi-avatar-1','cat','/proc/1/status'],text=True)
    return int(re.search(r'^VmRSS:\s+(\d+)',status,re.M)[1])

async def run(seconds,source):
    before=health();assert before['ok'] and not before['publisher']
    frames=[];idle=asyncio.Event();memory=[]
    async with websockets.connect('ws://127.0.0.1:19088/view',max_size=None) as viewer:
        async def read():
            async for message in viewer:
                if isinstance(message,str):
                    item=json.loads(message)
                    if item['type']=='start':await viewer.send('{"type":"sync","frame":0}')
                    elif item['type']=='frame':frames.append(item)
                    elif item['type']=='idle':idle.set()
                    elif item['type']=='error':raise AssertionError(item)
        reader=asyncio.create_task(read())
        async with websockets.connect('ws://127.0.0.1:19088/publish?source=test') as publisher:
            started=time.monotonic()
            for packet in range(seconds*10):
                start=packet*4800
                raw=bytearray()
                while len(raw)<4800:
                    position=(start+len(raw))%len(source)
                    raw.extend(source[position:position+min(4800-len(raw),len(source)-position)])
                await publisher.send(struct.pack('<d',time.time()*1000)+raw)
                if packet%100==99:
                    memory.append({'seconds':(packet+1)/10,'rss_kib':await asyncio.to_thread(rss_kib)})
                await asyncio.sleep(max(0,started+(packet+1)/10-time.monotonic()))
            await asyncio.wait_for(idle.wait(),10)
        reader.cancel()
        try:await reader
        except asyncio.CancelledError:pass
    after=health()
    speech=[item for item in frames if not item.get('phase')]
    assert len(speech)==seconds*25,(len(speech),seconds*25)
    assert all(item['index']==index%before['base_frames'] for index,item in enumerate(speech))
    assert not after['error'] and not after['speech_active']
    steady=[row['rss_kib'] for row in memory if row['seconds']>=before['duration_seconds']]
    assert len(steady)>=2 and steady[-1]-steady[0]<64*1024,memory
    report={'passed':True,'seconds':seconds,'speech_frames':len(speech),'continuous_indices':True,
            'rss_samples':memory,'steady_rss_change_kib':steady[-1]-steady[0],
            'measurement':'RSS after one complete idle-reference cycle versus final sample; one-minute check, not an hours-long soak test',
            'health':after}
    output=ROOT/'results/long_stream';output.mkdir(parents=True,exist_ok=True)
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=int,default=60)
    parser.add_argument('--pcm',type=Path)
    args=parser.parse_args()
    if args.seconds<40:parser.error('Use at least 40 seconds for a post-warmup memory comparison')
    source=args.pcm.read_bytes() if args.pcm else struct.pack('<2400h',*[round(math.sin(i*2*math.pi*220/24000)*2000) for i in range(2400)])
    asyncio.run(run(args.seconds,source))
