import json
import hashlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from characters import ROOT, select_character
from assets import verify


class CharacterSelection(unittest.TestCase):
    def test_default_dotenv_and_environment_precedence(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            root = Path(directory)
            shutil.copy2(ROOT / 'characters.json', root / 'characters.json')
            self.assertEqual(select_character(root=root)['name'], 'QinChe')
            (root / '.env').write_text('GPTSAYSHI_CHARACTER="gentleman" # previous avatar\n')
            self.assertEqual(select_character(root=root)['name'], 'gentleman')
            with patch.dict(os.environ, {'GPTSAYSHI_CHARACTER': 'qinche'}):
                self.assertEqual(select_character(root=root)['name'], 'QinChe')
                self.assertEqual(select_character('gentleman', root)['name'], 'gentleman')

    def test_unknown_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'gentleman or QinChe'):
            select_character('another-person')

    def test_each_identity_uses_its_own_complete_bundle(self):
        catalog = json.loads((ROOT / 'characters.json').read_text())
        for name in ('gentleman', 'QinChe'):
            selected = select_character(name)
            manifest = json.loads((ROOT / selected['manifest']).read_text())['files']
            checkpoint = manifest['assets/' + selected['checkpoint']]
            idle_root = selected['base'] if selected['renderer'] == 'native_face' else selected['detail']
            idle = manifest['assets/' + idle_root + '/idle.mp4']
            self.assertEqual(checkpoint['sha256'], selected['checkpoint_sha256'])
            self.assertEqual(idle['sha256'], selected['idle_video_sha256'])
            for field in ('image', 'landmarks'):
                self.assertIn('assets/' + selected[field], manifest)
            for field in (('base',) if selected['renderer'] == 'native_face' else ('base', 'teeth', 'detail')):
                self.assertIn('assets/' + selected[field] + '/manifest.json', manifest)
            self.assertIn('assets/feather_hubert.pth', manifest)
        self.assertEqual(catalog['default'], 'QinChe')
        self.assertNotEqual(select_character('gentleman')['checkpoint'], select_character('QinChe')['checkpoint'])

    def test_qinche_approved_appearance_is_isolated_from_gentleman(self):
        qinche, gentleman = select_character('QinChe'), select_character('gentleman')
        self.assertEqual(qinche['renderer'], 'native_face')
        self.assertEqual(qinche['settings'], {'teeth_mode': 'model', 'detail_profile': 'original', 'settle_ms': 0})
        self.assertEqual(gentleman['settings'], {'teeth_mode': 'new', 'detail_profile': 'model_idle', 'settle_ms': 400})
        self.assertNotIn('teeth', qinche)
        self.assertNotIn('detail', qinche)
        self.assertIn('epoch_115.pth', qinche['checkpoint'])
        self.assertEqual(qinche['checkpoint_sha256'], '007975c1ecda2870144d3f150e4c98d3caab1ee422045d904213a457052730b7')
        compositor = (ROOT / 'runtime/native_face_match.py').read_bytes().replace(b'\r\n', b'\n')
        self.assertEqual(hashlib.sha256(compositor).hexdigest(), qinche['compositor_sha256'])

    def test_verification_uses_only_the_selected_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'assets-manifest.json').write_text(json.dumps({'files': {'assets/missing-old-model': {'bytes': 1, 'sha256': 'missing'}}}))
            (root / 'qinche-manifest.json').write_text(json.dumps({'files': {}}))
            self.assertEqual(verify(root, 'qinche-manifest.json'), [])
            self.assertTrue(verify(root))


if __name__ == '__main__':
    unittest.main()
