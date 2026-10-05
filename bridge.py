"""ChatGPT app process audio -> independent FeatherTalk, no OpenAI API."""
import argparse
import array
import asyncio
import json
import math
import struct
import subprocess
import sys
import time
import wave
from collections import deque
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
RATE = 24000
CHUNK = 4800  # 100 ms of mono PCM16

def discover(app='chatgpt'):
    executable='ChatGPT Classic.exe' if app=='classic' else 'ChatGPT.exe'
    script = "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq '"+executable+"' } | Select-Object ProcessId,ParentProcessId,ExecutablePath | ConvertTo-Json -Compress"
    result = subprocess.run(['powershell.exe','-NoProfile','-Command',script],capture_output=True,text=True,check=True)
    records = json.loads(result.stdout or '[]')
    if isinstance(records,dict): records=[records]
    ids = {r['ProcessId'] for r in records}
    roots = [r for r in records if r['ParentProcessId'] not in ids]
    if len(roots)!=1:
        raise RuntimeError(f'Expected one running {executable} root process; found {len(roots)}. Open the requested ChatGPT App, or supply --pid explicitly.')
    return roots[0]

def health(url):
    parsed=urlparse(url)
    if parsed.scheme!='ws' or parsed.hostname not in ('127.0.0.1','localhost') or parsed.port!=19088:
        raise ValueError('This isolated lab accepts only ws://127.0.0.1:19088/publish')
    with urlopen('http://127.0.0.1:19088/health',timeout=3) as response:
        state=json.load(response)
    if not state.get('ok') or (state.get('publisher') and state.get('takeover_policy')!='latest_connection'):
        raise RuntimeError('Independent avatar is unavailable or does not support source replacement')
    return state

def level(raw):
    samples=array.array('h',raw)
    if sys.byteorder!='little': samples.byteswap()
    if not samples: return 0.,0.
    return math.sqrt(sum(x*x for x in samples)/len(samples))/32768,max(abs(x) for x in samples)/32768

async def run(args):
    import websockets
    state=health(args.url) if not args.capture_only else None
    target=discover(args.app) if args.pid is None else {'ProcessId':args.pid,'source':'explicit_pid'}
    pid=target['ProcessId']
    report={'target':target,'source':'windows_process_tree_loopback','sample_rate':RATE,
            'channels':1,'pcm_bits':16,'capture_only':args.capture_only,
            'chunks':0,'audible_chunks':0,'sent_packets':0,'peak':0.,'max_rms':0.,
            'queue_resets':0,'connections':0,'errors':[],'initial_health':state}
    output=ROOT/'results'/args.name
    output.mkdir(parents=True,exist_ok=True)
    process=await asyncio.create_subprocess_exec(str(ROOT/'ProcessAudio.exe'),str(pid),str(args.seconds),
                    stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW)
    queue=asyncio.Queue(maxsize=8)
    connected=asyncio.Event()
    superseded=asyncio.Event()
    native=[]
    async def diagnostics():
        while line:=await process.stderr.readline():
            message=line.decode(errors='replace').strip(); native.append(message)
            print(message,flush=True)
    async def relay():
        while True:
            try:
                health(args.url)
                source=args.app
                url=args.url+('?' if '?' not in args.url else '&')+'source='+source
                async with websockets.connect(url,open_timeout=3,max_size=None) as ws:
                    while not queue.empty(): queue.get_nowait()
                    await ws.send('{"type":"reset"}')
                    report['connections']+=1; connected.set()
                    print('Avatar connected: http://127.0.0.1:19088/',flush=True)
                    async def send_queued():
                        while True:
                            packet=await queue.get()
                            await ws.send(packet)
                            if isinstance(packet,bytes): report['sent_packets']+=1
                    sender=asyncio.create_task(send_queued())
                    try:
                        await ws.wait_closed()
                    finally:
                        sender.cancel()
                        try:await sender
                        except (asyncio.CancelledError,websockets.ConnectionClosed):pass
                    if ws.close_code==4001:
                        report['stop_reason']='replaced_by_newer_source'
                        superseded.set();connected.clear()
                        print('Replaced by newer source. Capture stopping; no automatic takeover.',flush=True)
                        return
                    raise RuntimeError(f'Avatar closed: {ws.close_code} {ws.close_reason}')
            except asyncio.CancelledError: raise
            except Exception as exc:
                connected.clear()
                report['errors'].append(str(exc))
                print('Avatar connection failed: '+str(exc),flush=True)
                while not queue.empty(): queue.get_nowait()
                await asyncio.sleep(1)
    def enqueue(raw):
        if not connected.is_set(): return
        if queue.full():
            while not queue.empty(): queue.get_nowait()
            queue.put_nowait('{"type":"reset"}')
            report['queue_resets']+=1
        queue.put_nowait(struct.pack('<d',time.time()*1000)+raw)
    diagnostic_task=asyncio.create_task(diagnostics())
    relay_task=asyncio.create_task(relay()) if not args.capture_only else None
    recording=None
    if args.record:
        recording=wave.open(str(output/'captured.wav'),'wb')
        recording.setnchannels(1);recording.setsampwidth(2);recording.setframerate(RATE)
    preroll=deque(maxlen=2)
    speaking=False; trailing=0
    started=time.monotonic()
    print(f'Capturing PID {pid}. Duration {args.seconds}s. Audio recording: {args.record}',flush=True)
    try:
        while True:
            if superseded.is_set():break
            try: raw=await process.stdout.readexactly(CHUNK)
            except asyncio.IncompleteReadError as exc:
                raw=exc.partial
                if not raw: break
            if len(raw)%2: raise RuntimeError('Incomplete PCM16 sample')
            if recording: recording.writeframesraw(raw)
            rms,peak=level(raw)
            report['chunks']+=1; report['peak']=max(report['peak'],peak)
            report['max_rms']=max(report['max_rms'],rms)
            audible=rms>=args.threshold
            report['audible_chunks']+=int(audible)
            if audible:
                if not speaking:
                    for old in preroll: enqueue(old)
                    preroll.clear(); speaking=True
                    print('ChatGPT audio detected',flush=True)
                trailing=2
                enqueue(raw)
            elif speaking and trailing>0:
                enqueue(raw);trailing-=1
            else:
                speaking=False;preroll.append(raw)
            if len(raw)<CHUNK: break
        if superseded.is_set() and process.returncode is None:
            process.terminate()
        code=await process.wait()
        if code and not superseded.is_set(): raise RuntimeError(f'Native capture exited with code {code}')
        await asyncio.sleep(.8 if relay_task else 0)
    finally:
        if process.returncode is None:
            process.terminate();await process.wait()
        await diagnostic_task
        if recording: recording.close()
        if relay_task:
            relay_task.cancel()
            try: await relay_task
            except asyncio.CancelledError: pass
        report['elapsed_seconds']=time.monotonic()-started
        report['native_diagnostics']=native
        report['audible_seconds']=report['audible_chunks']*.1
        report['captured_seconds']=report['chunks']*.1
        (output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False),flush=True)
    if report['audible_chunks']==0:
        print('No usable speech captured. Start a ChatGPT live voice reply and repeat.',flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid',type=int)
    parser.add_argument('--app',choices=['chatgpt','classic'],default='chatgpt')
    parser.add_argument('--seconds',type=float,default=120)
    parser.add_argument('--capture-only',action='store_true')
    parser.add_argument('--record',action='store_true',help='Explicitly save captured audio locally')
    parser.add_argument('--name',default='latest')
    parser.add_argument('--threshold',type=float,default=.001)
    parser.add_argument('--url',default='ws://127.0.0.1:19088/publish')
    args=parser.parse_args()
    if Path(args.name).name!=args.name or args.name in ('.','..'): parser.error('--name must be one folder name')
    if not 1<=args.seconds<=86400: parser.error('--seconds must be 1..86400')
    if not 0<args.threshold<1: parser.error('--threshold must be between 0 and 1')
    try: asyncio.run(run(args))
    except KeyboardInterrupt: print('Lab capture stopped.')

if __name__=='__main__': main()
