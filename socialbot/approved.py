"""One-time publication-approved artwork. No invented performance numbers are published."""
from pathlib import Path

ASSETS = {
    'WEB TASARIM': ('approved-web.png', 'Web Siteniz Neden Müşteri Getirmiyor?',
                    'Görsellik kadar hızlı ve anlaşılır bir ziyaretçi deneyimi de gerekir.'),
    'REKLAM YÖNETİMİ': ('approved-ads.png', 'Reklam Bütçesini Boşa Harcayan 3 Hata',
                       'Ölçüm, hedefleme ve optimizasyonu birlikte ele alın.'),
    'E-TİCARET': ('approved-shopify.png', 'Markaya Özel Shopify Tasarımı',
                  'Markanın hikâyesini yansıtan, hızlı ve alışverişi kolaylaştıran arayüzler.'),
}

BODY = {
    'WEB TASARIM': ("Web sitenize trafik geliyor ama ziyaretçiler iletişime geçmiyorsa tasarımın sadece estetik tarafına bakmak yetmez. "
      "İlk ekranda ne sunduğunuz anlaşılır mı? Mobilde hız ve okunabilirlik iyi mi? İletişim çağrısı doğru yerde mi? "
      "Bu üç sorunun yanıtı, kullanıcı yolculuğunun başlangıcıdır. Semtaş Dijital'de web tasarımını yalnızca görünüm değil, kullanıcı deneyimi olarak ele alıyoruz."),
    'REKLAM YÖNETİMİ': ("Reklam bütçesi neden verimsiz kullanılır? Üç kontrol noktası: 1) Ölçümleme eksikliği: dönüşüm gerçekleştiğinde hangi reklamın katkıda bulunduğunu görememek. "
      "2) Yanlış hedefleme: doğru mesajı yanlış kitleye göstermek. 3) Açılış sayfası sorunu: reklam vaadiyle sayfadaki deneyimin uyuşmaması. "
      "Kampanyayı büyütmeden önce ölçüm, hedef kitle ve açılış sayfasını birlikte değerlendirin."),
    'E-TİCARET': ("Hazır bir tema mağazanızı yayına almak için iyi bir başlangıç olabilir. Ancak büyüyen bir marka için özgün görsel dil, hızlı ürün keşfi "
      "ve kolay satın alma deneyimi rekabette farklılaşmanın parçalarıdır. Markaya özel Shopify tasarımında koleksiyon yapısını, mobil deneyimi "
      "ve sayfa performansını aynı çerçevede ele alıyoruz. Mesele sadece farklı görünmek değil; müşteriye doğru yolu göstermek."),
}

def get_first_use(category, posts_dir):
    """Return artwork only if the topic has never been prepared in this repository."""
    if category not in ASSETS:
        return None
    for item in Path(posts_dir).glob('*.json'):
        try:
            import json
            data = json.loads(item.read_text(encoding='utf-8'))
            if data.get('category') == category:
                return None
        except (OSError, ValueError):
            continue
    return ASSETS[category]

def seeded_copy(category):
    image, headline, subheadline = ASSETS[category]
    base=BODY[category]
    ending='\n\nProjeniz için görüşelim: semtasdijital.com'
    return {
      'headline': headline, 'subheadline': subheadline,
      'instagram': base + ending + '\n\n#SemtasDijital #DijitalPazarlama',
      'facebook': base + ending,
      'linkedin': base + '\n\nSizin ekibiniz bu sürecin hangi aşamasını önceliklendiriyor?' + ending
    }
