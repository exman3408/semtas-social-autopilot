from datetime import date
from pathlib import Path
import tempfile
import unittest
from socialbot.brand import topic_for
from socialbot.render import render_png
from socialbot.copywriter import demo_copy, GenerationError
from socialbot.buffer_api import BufferAPI
from unittest.mock import patch, MagicMock
from PIL import Image, ImageDraw

class SocialbotTests(unittest.TestCase):
    def test_weekends_are_skipped(self):
        self.assertIsNone(topic_for(date(2026, 10, 31)))
        self.assertIsNotNone(topic_for(date(2026, 11, 2)))

    def test_demo_has_complete_platform_copy(self):
        text = demo_copy({})
        self.assertTrue(text['instagram'].startswith('Modern'))
        self.assertTrue(text['linkedin'])

    def test_image_is_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp)/'card.png'
            render_png(image, 'Hızlı web siteleri neden önemlidir?',
                'İşletmeniz için daha sade bir deneyim oluşturun.', 'WEB TASARIM')
            with Image.open(image) as im:
                self.assertEqual(im.size, (1080, 1350))

    def test_graphql_image_post_inputs(self):
        api = BufferAPI('test-token')
        with patch.object(api, 'call', return_value={'createPost': {'post': {'id': 'post-123'}}}) as req:
            result = api.queue_image('channel-id', 'deneme', 'https://example.com/a.png')
            self.assertEqual(result['id'], 'post-123')
            self.assertEqual(req.call_args[0][1]['input']['assets'][0]['image']['url'], 'https://example.com/a.png')

    def test_no_network_publication_by_default(self):
        import os
        from socialbot.__main__ import queue
        with patch.dict(os.environ, {'PUBLISH_ENABLED': 'false'}):
            with patch('socialbot.__main__.BufferAPI') as connect:
                queue()
                connect.assert_not_called()

if __name__ == '__main__':
    unittest.main()

class V2Tests(unittest.TestCase):
    def test_real_logo_is_embedded_in_generated_render(self):
        from socialbot.render import LOGO, render_png
        self.assertTrue(LOGO.is_file())
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'render.png'
            render_png(out, 'Üç SEO kontrolü', 'Arama görünürlüğü için temel kontroller.', 'SEO')
            with Image.open(out) as im:
                self.assertEqual(im.size, (1080,1350))
                self.assertNotEqual(im.getpixel((75,75)), im.getpixel((1000,1000)))

    def test_approved_seed_assets_exist(self):
        from socialbot.approved import ASSETS, get_first_use, seeded_copy
        from socialbot.__main__ import MEDIA
        self.assertEqual(len(ASSETS),3)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNotNone(get_first_use('E-TİCARET', tmp))
            d=Path(tmp)/'2026-11-05.json'
            d.write_text('{"category":"E-TİCARET"}',encoding='utf8')
            self.assertIsNone(get_first_use('E-TİCARET', tmp))
        for category,(filename,*_) in ASSETS.items():
            self.assertTrue((MEDIA/filename).is_file())
            self.assertIn('semtasdijital.com',seeded_copy(category)['linkedin'])

    def test_duplicate_checks_pagination(self):
        from socialbot.buffer_api import BufferAPI
        api=BufferAPI('dummy')
        pages=[{'posts': {'edges':[{'node': {'id':'X','text':'other','channelId':'123'}}], 'pageInfo':{'hasNextPage':True,'endCursor':'cursor1'}}},
               {'posts': {'edges':[{'node': {'id':'Y','text':'my caption','channelId':'123'}}], 'pageInfo':{'hasNextPage':False,'endCursor':'cursor2'}}}]
        with patch.object(api,'call',side_effect=pages) as call:
            self.assertEqual(api.exists_matching_post('org','123','my caption'),'Y')
            self.assertEqual(call.call_count,2)

    def test_first_day_uses_approved_design_without_ai_request(self):
        import json
        from datetime import date
        from socialbot import __main__ as app
        with tempfile.TemporaryDirectory() as td:
            with patch.object(app, 'POSTS', Path(td)), patch.object(app, 'today', return_value=date(2026,11,2)):
                with patch.object(app, 'generate') as g:
                    app.prepare()
                    data=json.loads((Path(td)/'2026-11-02.json').read_text(encoding='utf-8'))
                    self.assertEqual(data['art_type'],'approved-logo-design')
                    self.assertEqual(data['media_file'],'approved-web.png')
                    g.assert_not_called()
