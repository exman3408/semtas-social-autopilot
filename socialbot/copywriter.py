"""AI generates structured copy. Production fails closed without a working key."""
import json
import os
import re
import requests
from .brand import BRAND_NAME, CTA, DOMAIN

MODEL_API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

class GenerationError(RuntimeError):
    pass

def _validate(obj):
    if not isinstance(obj, dict):
        raise GenerationError("AI JSON nesne döndürmedi")
    expected = ("headline", "subheadline", "instagram", "facebook", "linkedin")
    for field in expected:
        if not isinstance(obj.get(field), str) or not obj[field].strip():
            raise GenerationError(f"Alan eksik: {field}")
    obj = {key: obj[key].strip() for key in expected}
    if len(obj['headline']) > 90 or len(obj['subheadline']) > 170:
        raise GenerationError("Görsel yazısı çok uzun")
    if any(len(obj[p]) > 1800 for p in ('instagram', 'facebook', 'linkedin')):
        raise GenerationError("Paylaşım açıklaması çok uzun")
    if any('semtasdijital.com' not in obj[p].lower() for p in ('instagram', 'facebook', 'linkedin')):
        raise GenerationError('Metinlerde web sitesi/çağrı eksik')
    # Avoid unsupported exaggerated quantitative claims in autonomous content.
    if re.search(r'(?<!\w)%\s*\d+|\d+\s*%', ' '.join(obj.values())):
        raise GenerationError("Doğrulanmamış yüzde ifade bulundu")
    return obj

def demo_copy(topic):
    headline = "Web siteniz sadece güzel mi, yoksa işe yarıyor mu?"
    subheadline = "Ziyaretçinin ilk birkaç adımda ne yapacağını anlaması önemli."
    body = ("Modern bir web sitesi, yalnızca iyi görünmekten ibaret değil. "
            "Net bir teklif, kolay anlaşılır yönlendirme ve hızlı bir deneyim de gerekir. "
            f"\n\n{CTA}")
    return _validate({"headline": headline, "subheadline": subheadline,
                      "instagram": body + "\n\n#WebTasarım #DijitalPazarlama #SemtasDijital",
                      "facebook": body,
                      "linkedin": body})

def generate(topic, sources):
    if os.getenv('DEMO_MODE', 'false').lower() == 'true':
        return demo_copy(topic)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise GenerationError("GEMINI_API_KEY yok; canlı içerik oluşturma durduruldu")
    model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip()
    prompt = f'''Türkçe B2B sosyal medya stratejisti ve kıdemli kreatif metin yazarı olarak davran.
Marka: {BRAND_NAME}; Hizmetler: WordPress / kurumsal web tasarım, Shopify e-ticaret tasarımı, teknik SEO, Google ve Meta reklam yönetimi.
Marka sitesi: {DOMAIN}; Amaç: Türkiye'de bütçeli karar vericilere, ajans hizmetleri için nitelikli talep oluşturmak.
Konu: {topic['seed']}. İçerik açısı: {topic['angle']}. Kategori: {topic['category']}.
Haber başlıkları sadece fikir kaynağıdır; linkleri okuyamadığın için oradan doğrulanmış bilgi gibi alıntı yapma: {json.dumps(sources, ensure_ascii=False)}.
5 alanlı JSON nesnesi üret: headline (maksimum 90 karakter, tek ve vurucu), subheadline (maksimum 170 karakter),
instagram (70-150 kelime, en çok 4 hashtag), facebook (60-130 kelime), linkedin (100-170 kelime; profesyonel ve iş değeri odaklı).
Hedef kitle işletme sahipleri, pazarlama yöneticileri. Samimi ama premium; klişe ajans dili, yapay abartı, agresif reklam yok.
Sahte referans, başarı öyküsü, istatistik, yüzde, "garanti", uydurma araştırma veya hizmet vaadi kesinlikle yazma.
Her platform metninin sonunda doğal biçimde "{CTA}" olsun. Emoji en fazla 1, tercihen hiç.
Sadece JSON üret; Markdown çitleri yok.'''
    try:
        resp = requests.post(MODEL_API.format(model=model),
            headers={'x-goog-api-key': key, 'Content-Type': 'application/json'},
            json={'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'responseMimeType': 'application/json', 'temperature': 0.55}},
            timeout=55)
        resp.raise_for_status()
        data = resp.json()
        raw = data['candidates'][0]['content']['parts'][0]['text']
        obj = json.loads(raw)
        return _validate(obj)
    except (requests.RequestException, KeyError, IndexError, ValueError, TypeError) as exc:
        raise GenerationError(f"AI içerik üretimi başarısız: {type(exc).__name__}: {str(exc)[:150]}") from exc
