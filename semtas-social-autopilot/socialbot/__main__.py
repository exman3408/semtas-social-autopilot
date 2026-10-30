"""CLI: python -m socialbot demo|prepare|queue|channels|status"""
from datetime import datetime, date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import os
import unicodedata
import sys
import time
import requests
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from .brand import topic_for
from .research import recent_articles
from .copywriter import generate, demo_copy, GenerationError
from .render import render_png
from .approved import get_first_use, seeded_copy
from .buffer_api import BufferAPI, BufferError
from .analytics import create_weekly_report

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / 'content' / 'posts'
MEDIA = ROOT / 'docs' / 'media'
ZONE = ZoneInfo('Europe/Istanbul')


def today():
    return datetime.now(ZONE).date()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def demo():
    topic = {"category": "WEB TASARIM", "seed": "Web tasarım örneği", "angle": "örnek", "channels": ["instagram", "facebook"]}
    copy = demo_copy(topic)
    target = ROOT/'demo'/'semtas-sample.png'
    render_png(target, copy['headline'], copy['subheadline'], topic['category'])
    save_json(ROOT/'demo'/'semtas-sample.json', copy)
    print(f'[demo] Görsel: {target}; metin: demo/semtas-sample.json; API isteği yapılmadı.')


def prepare():
    day = today()
    topic = topic_for(day)
    if not topic:
        print('[prepare] Hafta sonu, planlı içerik yok')
        return
    output = POSTS / f'{day.isoformat()}.json'
    if output.exists():
        print(f'[prepare] Zaten mevcut: {output.name}; yeniden üretmeyecek')
        return
    approved = get_first_use(topic['category'], POSTS)
    if approved:
        name, _, _ = approved
        copy = seeded_copy(topic['category'])
        sources = []
        if not (MEDIA / name).exists():
            raise RuntimeError('Onaylı ve gerçek logolu medya eksik: ' + name)
        art_type = 'approved-logo-design'
    else:
        sources = recent_articles(day)
        copy = generate(topic, sources)
        landscape = topic['channels'] == ['linkedin']
        name = f'semtas-{day.isoformat()}.png'
        render_png(MEDIA/name, copy['headline'], copy['subheadline'], topic['category'], layout='square' if landscape else 'portrait')
        art_type = 'brand-template'

    post = {
        'date': day.isoformat(), 'category': topic['category'], 'seed': topic['seed'],
        'headline': copy['headline'], 'subheadline': copy['subheadline'], 'art_type': art_type,
        'sources_for_research_only': sources, 'media_file': name,
        'channels': {channel: {'caption': copy[channel], 'state': 'pending', 'buffer_post_id': None} for channel in topic['channels']}
    }
    save_json(output, post)
    print('[prepare] Hazır:', output, 'Kanallar:', ', '.join(post['channels']))


def media_accessible(url):
    # Buffer retrieves the image at publishing time; check a real image response now.
    try:
        r = requests.get(url, timeout=16, stream=True, allow_redirects=True)
        content_type = r.headers.get('Content-Type', '').lower()
        good = r.ok and content_type.startswith('image/') and r.url.startswith('https://')
        r.close()
        return good
    except requests.RequestException:
        return False


def queue():
    if os.getenv('PUBLISH_ENABLED', 'false').strip().lower() != 'true':
        print('[queue] KAPALI: PUBLISH_ENABLED=true yapılmadı. Hiçbir paylaşım yapılmadı.')
        return
    media_base = os.getenv('MEDIA_BASE_URL', '').strip().rstrip('/')
    org_id = os.getenv('BUFFER_ORG_ID', '').strip()
    if not media_base.startswith('https://') or not org_id:
        raise RuntimeError('MEDIA_BASE_URL https://... ve BUFFER_ORG_ID gerekli')
    client = BufferAPI()
    verified = {item['id']: item for item in client.channels(org_id)}
    targets = {
        channel: os.getenv('BUFFER_'+channel.upper()+'_CHANNEL_ID', '').strip()
        for channel in ('instagram', 'facebook', 'linkedin')
    }
    enabled = {platform: cid for platform, cid in targets.items() if cid}
    if not enabled:
        raise RuntimeError('Hiçbir BUFFER_*_CHANNEL_ID ayarlanmamış')
    for platform, cid in enabled.items():
        result = verified.get(cid)
        if not result or str(result['service']).lower() != platform:
            raise RuntimeError(f'{platform} kanal kimliği bu Buffer organizasyonuna ait değil / platform uyuşmuyor')
        brand_check = os.getenv('BUFFER_BRAND_CHECK', 'semtas').strip().lower()
        def normalized(value):
            return ''.join(c for c in unicodedata.normalize('NFKD', str(value).lower().replace('ı','i')) if not unicodedata.combining(c))
        if brand_check and normalized(brand_check) not in normalized(result.get('name', '')):
            raise RuntimeError(f'{platform} hesabı Semtaş ismiyle uyuşmuyor: {result.get("name")}; güvenlik için durduruldu')
        if result.get('isQueuePaused') or result.get('isDisconnected') or result.get('isLocked'):
            raise RuntimeError(f'{platform} Buffer kanalı kapalı, kilitli veya bağlantısı kesilmiş')

    count = 0
    errors = 0
    for path in sorted(POSTS.glob('*.json')):
        payload = json.loads(path.read_text('utf-8'))
        day = date.fromisoformat(payload['date'])
        if not (today()-timedelta(days=7) <= day <= today()):
            continue
        for platform, item in payload.get('channels', {}).items():
            if platform not in enabled or item.get('state') in ('queued', 'published'):
                continue
            media_url = f"{media_base}/{payload['media_file']}"
            if not media_accessible(media_url):
                print(f'[queue] Görsel halka açık değil, atlandı: {media_url}')
                item['state'] = 'retry'
                item['error'] = 'Public media URL erişilemiyor'
                errors += 1
                save_json(path, payload)
                continue
            try:
                duplicate = client.exists_matching_post(org_id, enabled[platform], item['caption'])
                post = {'id': duplicate} if duplicate else client.queue_image(enabled[platform], item['caption'], media_url)
                item['state'] = 'queued'
                item['buffer_post_id'] = post['id']
                item['queued_at'] = datetime.now(ZONE).isoformat()
                item['due_at'] = post.get('dueAt')
                item.pop('error', None)
                count += 1
                print(f'[queue] {platform}: {"Var olan Buffer gönderisi bulundu" if duplicate else "Buffer kuyruğuna eklendi"}: {post["id"]}')
            except BufferError as exc:
                print(f'[queue] {platform}: {exc}')
                item['state'] = 'retry'
                item['error'] = str(exc)[:300]
                errors += 1
            save_json(path, payload)
    print(f'[queue] Sonuç: {count} sıraya alındı/mevcut; {errors} hata. Yayınlandığını ayrıca Buffer üzerinden kontrol edin.')


def channels():
    api = BufferAPI()
    orgs = api.organizations()
    print('Buffer organizasyonları:')
    for item in orgs:
        print(f"  {item['name']}: {item['id']}")
        for channel in api.channels(item['id']):
            print(f"    {channel['service']}: {channel['name']} -> {channel['id']}")


def status():
    for path in sorted(POSTS.glob('*.json'))[-12:]:
        data = json.loads(path.read_text('utf-8'))
        print(path.name, ', '.join(f'{k}={v["state"]}' for k, v in data['channels'].items()))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else 'demo'
    choices = {'demo': demo, 'prepare': prepare, 'queue': queue, 'channels': channels, 'status': status, 'report': create_weekly_report}
    if arg not in choices:
        print('Kullanım: python -m socialbot [demo|prepare|queue|channels|status|report]')
        sys.exit(2)
    try:
        choices[arg]()
    except (RuntimeError, GenerationError, ValueError, KeyError) as exc:
        print(f'[ERROR] {exc}')
        sys.exit(1)

if __name__ == '__main__':
    main()
