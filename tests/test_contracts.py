import importlib.util,json,re,tempfile,unittest,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('assets',ROOT/'assets.py')
assets=importlib.util.module_from_spec(spec);spec.loader.exec_module(assets)

class DistributionContracts(unittest.TestCase):
    def test_user_visible_surfaces_are_english(self):
        paths=list((ROOT/'browser_extension').glob('*'))+[ROOT/'runtime'/'specter.html']
        for path in paths:
            if path.suffix in ('.html','.js','.json'):
                self.assertIsNone(re.search(r'[\u3400-\u9fff]',path.read_text(encoding='utf-8')),str(path))

    def test_runtime_does_not_mount_another_checkout(self):
        compose=(ROOT/'compose.yaml').read_text()
        self.assertIn('./assets:/work:ro',compose)
        self.assertNotIn('SpecterSaysHi',compose)
        self.assertNotIn('../',compose)

    def test_archive_must_match_expected_file_list(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'assets-manifest.json').write_text(json.dumps({'files':{}}))
            archive=root/'bad.zip'
            with zipfile.ZipFile(archive,'w') as bundle:bundle.writestr('../outside.txt','bad')
            with self.assertRaisesRegex(ValueError,'file list'):assets.extract(archive,root)
            self.assertFalse((root.parent/'outside.txt').exists())

    def test_hash_mismatch_is_not_installed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);relative='assets/model.bin'
            expected={'sha256':hashlib.sha256(b'expected').hexdigest(),'bytes':8}
            (root/'assets-manifest.json').write_text(json.dumps({'files':{relative:expected}}))
            archive=root/'bad.zip'
            with zipfile.ZipFile(archive,'w') as bundle:bundle.writestr(relative,b'tampered')
            with self.assertRaisesRegex(ValueError,'does not match'):assets.extract(archive,root)
            self.assertFalse((root/relative).exists())

    def test_verified_assets_install_and_detect_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);relative='assets/model.bin';content=b'expected'
            (root/'assets-manifest.json').write_text(json.dumps({'files':{relative:{
                'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)}}}))
            archive=root/'good.zip'
            with zipfile.ZipFile(archive,'w') as bundle:bundle.writestr(relative,content)
            assets.extract(archive,root);self.assertEqual(assets.verify(root),[])
            (root/relative).write_bytes(b'tampered')
            self.assertEqual(assets.verify(root),['Hash mismatch: '+relative])

if __name__=='__main__':unittest.main()
