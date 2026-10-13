"""Install and verify the release assets without depending on another checkout."""
import argparse,hashlib,json,shutil,time,urllib.request,zipfile
from pathlib import Path
from characters import select_character
ROOT=Path(__file__).resolve().parent

def digest(path):
    with path.open('rb') as file:return hashlib.file_digest(file,'sha256').hexdigest()

def target_path(root,relative):
    target=(root/relative).resolve()
    if not target.is_relative_to((root/'assets').resolve()):
        raise ValueError('Asset path is outside the assets directory')
    return target

def verify(root=ROOT,manifest_name='assets-manifest.json'):
    manifest=json.loads((root/manifest_name).read_text(encoding='utf-8'))
    errors=[]
    for relative,expected in manifest['files'].items():
        path=target_path(root,relative)
        if not path.is_file():errors.append('Missing: '+relative)
        elif path.stat().st_size!=expected['bytes'] or digest(path)!=expected['sha256']:
            errors.append('Hash mismatch: '+relative)
    return errors

def extract(archive,root=ROOT,manifest_name='assets-manifest.json'):
    expected=json.loads((root/manifest_name).read_text(encoding='utf-8'))['files']
    with zipfile.ZipFile(archive) as bundle:
        if set(bundle.namelist())!=set(expected):raise ValueError('Archive file list does not match the release')
        for relative,metadata in expected.items():
            path=target_path(root,relative)
            if path.is_file() and digest(path)==metadata['sha256']:continue
            path.parent.mkdir(parents=True,exist_ok=True)
            temporary=path.with_name(path.name+'.part')
            with bundle.open(relative) as source,temporary.open('wb') as output:
                shutil.copyfileobj(source,output,1024*1024)
            if temporary.stat().st_size!=metadata['bytes'] or digest(temporary)!=metadata['sha256']:
                raise ValueError('Extracted asset does not match the release: '+relative)
            temporary.replace(path)

def install(archive=None,character=None):
    selection=select_character(character)
    manifest_name=selection['manifest']
    if not verify(ROOT,manifest_name):print(selection['name']+' avatar assets are verified.');return
    bundle=json.loads((ROOT/selection['bundle']).read_text(encoding='utf-8'))
    if archive is None:
        cache=ROOT/'.downloads';cache.mkdir(exist_ok=True)
        archive=cache/bundle['filename']
        if not archive.is_file() or digest(archive)!=bundle['sha256']:
            partial=archive.with_suffix('.zip.part')
            for attempt in range(3):
                try:
                    request=urllib.request.Request(bundle['url'],headers={'User-Agent':'GPTSaysHi/0.2'})
                    print('Downloading avatar assets from the GitHub release...',flush=True)
                    with urllib.request.urlopen(request,timeout=60) as response,partial.open('wb') as output:
                        shutil.copyfileobj(response,output,1024*1024)
                    if digest(partial)!=bundle['sha256']:raise ValueError('Downloaded asset archive hash mismatch')
                    partial.replace(archive);break
                except Exception:
                    if attempt==2:raise
                    time.sleep(2)
    if digest(archive)!=bundle['sha256']:raise ValueError('Asset archive hash mismatch')
    print('Extracting verified avatar assets...',flush=True);extract(archive,ROOT,manifest_name)
    errors=verify(ROOT,manifest_name)
    if errors:raise ValueError('\n'.join(errors))
    print('Avatar assets installed and verified.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true');parser.add_argument('--archive',type=Path)
    parser.add_argument('--character',help='Override GPTSAYSHI_CHARACTER: gentleman or QinChe')
    args=parser.parse_args()
    if args.verify:
        selection=select_character(args.character)
        errors=verify(ROOT,selection['manifest'])
        if errors:raise SystemExit('\n'.join(errors))
        print(selection['name']+' avatar assets are verified.')
    else:install(args.archive,args.character)
if __name__=='__main__':main()
