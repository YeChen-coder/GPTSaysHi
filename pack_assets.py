"""Build the separate, hash-pinned avatar release archive."""
import argparse,json,zipfile
from assets import ROOT,digest,verify
from characters import select_character
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--character',help='gentleman or QinChe')
    args=parser.parse_args();selection=select_character(args.character)
    errors=verify(ROOT,selection['manifest'])
    if errors:raise SystemExit('\n'.join(errors))
    manifest=json.loads((ROOT/selection['manifest']).read_text())
    output=ROOT/'dist';output.mkdir(exist_ok=True)
    previous=json.loads((ROOT/selection['bundle']).read_text())
    filename=previous['filename'];archive=output/filename
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as bundle:
        for relative in manifest['files']:
            print('Packing '+relative,flush=True);bundle.write(ROOT/relative,relative)
    metadata={'filename':filename,'sha256':digest(archive),'bytes':archive.stat().st_size,
        'url':previous['url']}
    (ROOT/selection['bundle']).write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps(metadata),flush=True)
if __name__=='__main__':main()
