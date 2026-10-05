"""Exercise real publisher ownership, engine cleanup, and native bridge shutdown."""
import asyncio,json,math,struct,subprocess,sys,time
from pathlib import Path
import websockets
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge import ROOT,health

URL='ws://127.0.0.1:19088/publish'
async def ready(source):
    for _ in range(80):
        state=health(URL)
        if state.get('source')==source:return state
        await asyncio.sleep(.1)
    raise AssertionError(f'Source not selected: {source}')

async def speech(ws,seconds=.8):
    raw=struct.pack('<2400h',*[round(math.sin(i*2*math.pi*220/24000)*2000) for i in range(2400)])
    for _ in range(round(seconds*10)):
        await ws.send(struct.pack('<d',time.time()*1000)+raw)
        await asyncio.sleep(.1)

async def main():
    report={'passed':False};clients=[];player=None;native_bridge=None
    output=ROOT/'results'/'multi_source';output.mkdir(parents=True,exist_ok=True)
    try:
        old=await websockets.connect(URL+'?source=chatgpt');clients.append(old)
        await ready('chatgpt');await speech(old)
        first=health(URL);assert first['speech_active']
        classic=await websockets.connect(URL+'?source=classic');clients.append(classic)
        await ready('classic');await old.wait_closed();assert old.close_code==4001
        await speech(classic)
        browser=await websockets.connect(URL+'?source=browser-edge');clients.append(browser)
        await ready('browser-edge');await classic.wait_closed();assert classic.close_code==4001
        await speech(browser);await asyncio.sleep(1)
        assert not health(URL)['error']
        invalid=await websockets.connect(URL+'?source=unrelated-browser');clients.append(invalid)
        await invalid.wait_closed();assert invalid.close_code==1008
        assert health(URL)['source']=='browser-edge'
        # Three rapid connects: the server serializes shutdown, last remains owner.
        rapid=[]
        for source in ('chatgpt','classic','browser-chrome'):
            client=await websockets.connect(URL+'?source='+source);rapid.append(client);clients.append(client)
        await ready('browser-chrome')
        await asyncio.gather(*(client.wait_closed() for client in rapid[:-1]))
        assert all(client.close_code==4001 for client in rapid[:-1])
        await speech(rapid[-1]);await rapid[-1].close();await asyncio.sleep(1)
        assert not health(URL)['publisher'] and not health(URL)['error']
        # Run the Windows capture bridge against a harmless local process.
        # Even while its audio is silent, replacement must stop it, not reconnect.
        player=subprocess.Popen(['powershell.exe','-NoProfile','-Command','Start-Sleep -Seconds 30'],creationflags=subprocess.CREATE_NO_WINDOW)
        native_bridge=await asyncio.create_subprocess_exec(sys.executable,'-u',str(ROOT/'bridge.py'),
            '--pid',str(player.pid),'--seconds','25','--name','superseded_native',
            stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        await ready('chatgpt')
        replacement=await websockets.connect(URL+'?source=browser-edge');clients.append(replacement)
        await ready('browser-edge')
        stdout,stderr=await asyncio.wait_for(native_bridge.communicate(),timeout=5)
        assert native_bridge.returncode==0,(stdout,stderr)
        native=json.loads((ROOT/'results'/'superseded_native'/'report.json').read_text())
        assert native['stop_reason']=='replaced_by_newer_source' and native['connections']==1 and not native['errors']
        await asyncio.sleep(1.2);assert health(URL)['source']=='browser-edge'
        await replacement.close();await asyncio.sleep(1)
        report.update(passed=True,app_to_classic_to_browser=True,active_speech_takeover=True,
            invalid_source_does_not_replace=True,rapid_connections_latest_wins=True,
            silent_native_bridge_stops_when_replaced=True,no_reconnect_fight=True,
            superseded_exit_code=native_bridge.returncode,after=health(URL))
    finally:
        for client in clients:await client.close()
        if native_bridge and native_bridge.returncode is None:native_bridge.terminate();await native_bridge.wait()
        if player and player.poll() is None:player.terminate();player.wait()
        (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)

if __name__=='__main__':asyncio.run(main())
