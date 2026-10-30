"""Brand rules and publishing cadence. Update these to match approved brand book."""
from datetime import date

BRAND_NAME = "SEMTAŞ DİJİTAL"
DOMAIN = "https://semtasdijital.com"
CTA = "Projenizi konuşalım: semtasdijital.com"
PRIMARY = "#0C1526"       # Geçici başlangıç renkleri: marka rehberi ile değiştirin.
ACCENT = "#52B2FA"
SECONDARY = "#E7EDF4"

# Weekday Monday=0 ... Sunday=6; deliberately limited to a small weekly cadence.
TOPICS = {
    0: {"category": "WEB TASARIM", "seed": "Bir işletmenin web sitesinde ziyaretçinin müşteri olmamasına yol açan 3 kullanılabilirlik hatası", "channels": ["instagram", "facebook"]},
    1: {"category": "REKLAM YÖNETİMİ", "seed": "Google ve Meta reklamlarında bütçeyi boşa harcamamak için ölçüm ve dönüşüm takibi", "channels": ["linkedin"]},
    2: {"category": "SEO", "seed": "Teknik SEO denetiminde sık atlanan önemli kontroller", "channels": ["instagram", "facebook"]},
    3: {"category": "E-TİCARET", "seed": "Premium Shopify mağazalarında güven, performans ve satın alma deneyimi", "channels": ["linkedin"]},
    4: {"category": "DİJİTAL STRATEJİ", "seed": "Kurumsal web sitesi ile reklam ve SEO çalışmalarının birbiriyle bağlantısı", "channels": ["instagram", "facebook"]},
}

def topic_for(day: date):
    if day.weekday() not in TOPICS:
        return None
    entry = dict(TOPICS[day.weekday()])
    # Alternating angle adds variety while the same pillar remains consistent.
    angles = ["Sorunu tanımla ve çözüm öner", "Sık yapılan yanlışlar", "Basit bir kontrol listesi", "Karar vericiler için pratik öneriler"]
    entry["angle"] = angles[(day.toordinal() // 7) % len(angles)]
    return entry
