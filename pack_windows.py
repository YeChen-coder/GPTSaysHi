"""Package tracked application files and the compiled helper, excluding local data."""
import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',default=json.loads((ROOT/'package.json').read_text())['version'])
    args=parser.parse_args()
    files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    files=[n for n in files if n]
    helper=ROOT/'ProcessAudio.exe'
    if not helper.is_file():raise SystemExit('Compile ProcessAudio.exe with setup.ps1 first')
    files.append('ProcessAudio.exe')
    forbidden={'.git','.env','assets','dist','results','node_modules','.venv','.downloads'}
    if any(Path(n).parts[0]in forbidden for n in files):raise SystemExit('Private/generated files in tracked input')
    output=ROOT/'dist';output.mkdir(exist_ok=True)
    archive=output/f'gptsayshi-windows-v{args.version}.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for name in sorted(set(files)):z.write(ROOT/name,'GPTSaysHi/'+name)
    result={'filename':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':len(set(files))}
    print(json.dumps(result))
if __name__=='__main__':main()
