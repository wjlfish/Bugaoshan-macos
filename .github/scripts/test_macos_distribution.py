import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import macos_signing
import macos_dmg

class PersonalDistributionTest(unittest.TestCase):
    def test_staple_and_validate_retry_transient_disconnect(self):
        for action in ['staple', 'validate']:
            with self.subTest(action=action), patch.object(macos_dmg, 'run', side_effect=[RuntimeError('-1005'), 'ok']) as run, patch.object(macos_dmg.time, 'sleep'):
                self.assertEqual(macos_dmg.stapler(action, Path('test.dmg')), 'ok')
                self.assertEqual(run.call_count, 2)
                self.assertEqual(run.call_args.args[:3], ('xcrun', 'stapler', action))
    def test_final_validation_failure_is_not_ignored(self):
        with patch.object(macos_dmg, 'run', side_effect=RuntimeError('invalid')) as run, patch.object(macos_dmg.time, 'sleep'):
            with self.assertRaises(RuntimeError):
                macos_dmg.stapler('validate', Path('test.app'))
            self.assertEqual(run.call_count, 3)
    def test_select_does_not_require_an_upstream_signing_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=source, text=True).strip()
            git('init', '-q')
            git('config', 'user.name', 'Test')
            git('config', 'user.email', 'test@example.invalid')
            (source/'pubspec.yaml').write_text('version: 2.5.4+20513\n')
            git('add', '.')
            git('commit', '-qm', 'source without signing config')
            git('tag', 'v2.5.4-preview.31')
            git('update-ref', 'refs/remotes/origin/preview', 'HEAD')
            actual=macos_signing.run
            def missing_release(*args, **kwargs):
                if args[0]=='gh':
                    return subprocess.CompletedProcess(args, 1, '', 'release not found')
                return actual(*args, **kwargs)
            with patch.object(macos_signing, 'run', side_effect=missing_release):
                selected=macos_signing.select(source)
            self.assertEqual(selected['ready'], 'true')
            self.assertEqual(selected['sha'], git('rev-parse','HEAD'))
            self.assertEqual(selected['version'], '2.5.4')
    def test_published_release_is_skipped(self):
        with patch.object(macos_signing, 'git', return_value='v2.5.4'), patch.object(macos_signing, 'run', return_value=subprocess.CompletedProcess([],0,'{"isDraft":false}','')):
            self.assertEqual(macos_signing.select(Path('source')), {'ready':'false'})
if __name__=='__main__':
    unittest.main()
