"""Use public RSS headlines only as leads, not verified evidence for uncorroborated claims."""
import datetime as dt
import urllib.parse
import xml.etree.ElementTree as ET
import requests

QUERY_BY_DAY = {
  0: 'web tasarım kullanıcı deneyimi dönüşüm',
  1: 'Google Ads Meta reklam dönüşüm izleme',
  2: 'technical SEO core web vitals search',
  3: 'Shopify ecommerce checkout conversion design',
  4: 'dijital pazarlama kurumsal web SEO trend',
}

def recent_articles(day: dt.date, limit: int = 5):
    query = QUERY_BY_DAY.get(day.weekday(), "dijital pazarlama")
    q = urllib.parse.quote(query)
    url = f'https://news.google.com/rss/search?q={q}&hl=tr&gl=TR&ceid=TR:tr'
    try:
        # We explicitly check the HTTP status rather than relying on feedparser's HTTP handling.
        response = requests.get(url, timeout=12, headers={"User-Agent": "SemtasSocialBot/1.0 (+public RSS research)"})
        response.raise_for_status()
        root = ET.fromstring(response.content)
        out = []
        for entry in root.findall('.//item'):
            title = (entry.findtext('title') or '').strip()[:220]
            link = (entry.findtext('link') or '').strip()
            if title and link.startswith('https://'):
                out.append({"title": title, "url": link})
            if len(out) == limit:
                break
        return out
    except (requests.RequestException, ValueError, ET.ParseError) as exc:
        print(f"[research] RSS erişilemedi, evergreen içerikle devam: {type(exc).__name__}")
        return []
