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


class MobileApprovalSafetyTests(unittest.TestCase):
    def test_queue_never_publishes_without_issue_approval_even_when_enabled(self):
        import json
        import os
        from socialbot import __main__ as bot
        from datetime import datetime
        from zoneinfo import ZoneInfo
        d = datetime.now(ZoneInfo("Europe/Istanbul")).date()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / f"{d.isoformat()}.json"
            path.write_text(json.dumps({
                'date': d.isoformat(), 'media_file': 'example.png',
                'review': {'status': 'pending', 'issue_number': 12},
                'channels': {'instagram': {'caption': 'Test caption', 'state': 'pending'}}
            }), encoding='utf-8')
            fake = MagicMock()
            fake.channels.return_value = [{
                'id': 'instagram-1', 'service': 'instagram', 'name': 'semtasdijital',
                'isQueuePaused': False, 'isDisconnected': False, 'isLocked': False
            }]
            keys = {
                'PUBLISH_ENABLED': 'true', 'MEDIA_BASE_URL': 'https://example.com/media',
                'BUFFER_ORG_ID': 'test-org',
                'BUFFER_INSTAGRAM_CHANNEL_ID': 'instagram-1',
                'BUFFER_FACEBOOK_CHANNEL_ID': '',
                'BUFFER_LINKEDIN_CHANNEL_ID': '',
            }
            with (
                patch.object(bot, 'POSTS', Path(td)),
                patch.object(bot, 'BufferAPI', return_value=fake),
                patch.dict(os.environ, keys),
            ):
                bot.queue()
            fake.queue_image.assert_not_called()
            fake.exists_matching_post.assert_not_called()

    def test_issue_body_contains_owner_mobile_mention_and_review_commands(self):
        from socialbot.review import issue_body
        post = {
            'date': '2026-10-30', 'category': 'SEO', 'headline': 'Test',
            'media_file': 'test.png',
            'channels': {'instagram': {'caption': 'Test content'}}
        }
        body = issue_body(post, 'https://example.com/media')
        self.assertIn('@exman3408', body)
        self.assertIn('/onayla', body)
        self.assertIn('/reddet', body)


class RevisionCommandTests(unittest.TestCase):
    def _event(self, path, command):
        import json
        event = {
            "comment": {"id": 991, "body": command, "user": {"login": "exman3408"}},
            "issue": {
                "number": 1, "body": "<!-- semtas-autopilot-review:2026-10-30 -->",
                "user": {"login": "github-actions[bot]"}
            }
        }
        path.write_text(json.dumps(event), encoding="utf-8")

    def test_revision_revokes_previous_test_approval(self):
        import json, os
        from socialbot import review
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            posts=root/"posts";posts.mkdir()
            p=posts/"2026-10-30.json"
            p.write_text(json.dumps({
                "date": "2026-10-30", "review": {
                    "status": "approved", "issue_number": 1, "approved_by": "exman3408",
                    "approved_at": "2026-10-30T12:15:44Z"
                },
                "channels": {"instagram": {"state": "pending", "buffer_post_id": None}}
            }), encoding="utf-8")
            event=root/"event.json"
            self._event(event, "/revize daha kaliteli ve premium bir gorsel tasarla")
            with patch.object(review, "POSTS", posts), patch.object(review, "identity", return_value=("exman3408/semtas-social-autopilot", "dummy")), patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event)}):
                review.apply_comment()
            result=json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(result["review"]["status"], "revision_requested")
            self.assertNotIn("approved_at", result["review"])
            self.assertIn("premium", result["review"]["revision_note"])
            self.assertEqual(result["channels"]["instagram"]["state"], "pending")

    def test_previous_artwork_cannot_be_reapproved_without_redesign(self):
        import json, os
        from socialbot import review
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);posts=root/"posts";posts.mkdir()
            p=posts/"2026-10-30.json"
            p.write_text(json.dumps({
                "date":"2026-10-30",
                "review":{"status":"revision_requested","issue_number":1},
                "channels":{"instagram":{"state":"pending","buffer_post_id":None}}
            }),encoding="utf-8")
            event=root/"event.json"
            self._event(event, "/onayla")
            with patch.object(review, "POSTS", posts), patch.object(review, "identity", return_value=("exman3408/semtas-social-autopilot", "dummy")), patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event)}):
                review.apply_comment()
            result=json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(result["review"]["status"], "revision_requested")


class GeminiImageGatewayTests(unittest.TestCase):

    def test_quality_gate_rejects_template_engine(self):
        import os
        from socialbot.creative import create_artwork, ArtworkError
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {
            "IMAGE_ENGINE": "premium_pillow",
            "REQUIRE_GENERATIVE_IMAGE": "true",
            "ALLOW_PAID_GEMINI_IMAGE_API": "false",
        }):
            with self.assertRaises(ArtworkError):
                create_artwork(Path(d)/"bad.png","Test","Test","SEO")
            self.assertFalse((Path(d)/"bad.png").exists())

    def test_premium_free_image_has_real_logo(self):
        import os
        from socialbot.creative import create_artwork
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {"IMAGE_ENGINE":"premium_pillow"}):
            p=Path(d)/"post.png"
            backend=create_artwork(p,"Reklam ve SEO birlikte çalışmalı","Birbirini destekleyen dijital yatırımlar.","DİJİTAL STRATEJİ",revision_note="Daha premium")
            self.assertEqual(backend,"premium-pillow-free")
            self.assertTrue(p.exists())
            from PIL import Image
            with Image.open(p) as im:
                self.assertEqual(im.size,(1080,1350))

    def test_nano_banana_cannot_make_paid_call_by_default(self):
        import os
        from socialbot.creative import create_artwork, ArtworkError
        with tempfile.TemporaryDirectory() as d:
            with patch.dict(os.environ, {"IMAGE_ENGINE":"gemini","ALLOW_PAID_GEMINI_IMAGE_API":"false"}):
                with patch("socialbot.creative.requests.post") as request:
                    with self.assertRaises(ArtworkError):
                        create_artwork(Path(d)/"test.png","Test","Test","SEO")
                    request.assert_not_called()

    def test_revise_has_no_approval_without_new_issue(self):
        import json, os
        from socialbot import revise
        with tempfile.TemporaryDirectory() as d:
            posts=Path(d)/"posts";posts.mkdir()
            media=Path(d)/"media";media.mkdir()
            p=posts/"2026-10-30.json"
            p.write_text(json.dumps({
              "date":"2026-10-30","category":"SEO","headline":"SEO ve hız",
              "subheadline":"Test","media_file":"old.png",
              "review":{"status":"revision_requested","issue_number":2,"revision_note":"Daha premium"},
              "channels":{"instagram":{"state":"pending","buffer_post_id":None}}
            }),encoding="utf8")
            with patch.object(revise,"POSTS",posts),patch.object(revise,"MEDIA",media),patch("socialbot.revise.create_artwork",return_value="premium-pillow-free") as image_maker:
                def write_file(path,*args,**kwargs):
                    Path(path).write_bytes(b"test-image"*1500)
                    return "premium-pillow-free"
                image_maker.side_effect=write_file
                revise.render_pending()
            result=json.loads(p.read_text(encoding="utf8"))
            self.assertEqual(result["review"]["status"],"revision_rendered")
            self.assertIsNone(result["review"]["issue_number"])
            self.assertEqual(result["review"]["previous_issue_number"],2)
            self.assertNotEqual(result["media_file"],"old.png")
