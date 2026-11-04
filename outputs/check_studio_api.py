"""Regression: API coordinates must describe the resized analysis canvas."""
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'api'))
import server

class CanvasDimensionsTest(unittest.IsolatedAsyncioTestCase):
    async def test_large_upload_reports_processed_dimensions(self):
        raw = io.BytesIO()
        Image.new('RGB', (2000, 1000), 'white').save(raw, format='PNG')
        class Upload:
            async def read(self):
                return raw.getvalue()
        class Request:
            headers = {'content-type': 'multipart/form-data'}
            async def form(self):
                return {'file': Upload()}
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as folder:
            mask = Path(folder) / 'mask.png'
            Image.new('L', (1600, 800), 0).save(mask)
            record = {'id': 'test', 'sha256': 'test', 'created': 'test', 'mask_path': str(mask)}
            with patch.object(server, 'analyse', return_value=record):
                result = await server.run_analyse(Request())
            self.assertEqual((result['width'], result['height']), (1600, 800))
            self.assertEqual(result['candidate_count'], 0)

if __name__ == '__main__':
    unittest.main()
