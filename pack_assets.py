"""Build the separate, hash-pinned avatar release archive."""
import json,zipfile
from assets import ROOT,digest,verify
def main():
    errors=verify()
    if errors:raise SystemExit('\n'.join(errors))
    manifest=json.loads((ROOT/'assets-manifest.json').read_text())
    output=ROOT/'dist';output.mkdir(exist_ok=True)
    filename='gptsayshi-avatar-20261004.zip';archive=output/filename
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as bundle:
        for relative in manifest['files']:
            print('Packing '+relative,flush=True);bundle.write(ROOT/relative,relative)
    metadata={'filename':filename,'sha256':digest(archive),'bytes':archive.stat().st_size,
        'url':'https://github.com/YeChen-coder/GPTSaysHi/releases/download/v0.1.0/'+filename}
    (ROOT/'asset-bundle.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps(metadata),flush=True)
if __name__=='__main__':main()
