# Semtaş Dijital otomasyonunu etkinleştirme — 3 aşama

1. **Buffer Free hesabında** Semtaş Instagram profesyonel hesabı, Facebook Sayfası ve LinkedIn hesabını bağla. Buffer > Settings > API altında kişisel API anahtarı oluştur.
2. **GitHub'da `semtas-social-autopilot` adlı boş public depo oluştur** ve ZIP içindeki klasörü git ile yükle (ayrıntılar `README.md`). Settings > Pages > Source: GitHub Actions.
3. **GitHub Secrets'a** `BUFFER_API_KEY`, `GEMINI_API_KEY`; **GitHub Variables'a** `BUFFER_ORG_ID`, üç `BUFFER_*_CHANNEL_ID`, `MEDIA_BASE_URL`, `PUBLISH_ENABLED=false` gir. Actions `0 - Test ...` ile bağlantı ve ID'leri gör. Önce `1 - İçerik hazırla`, sonra `2 - Buffer'a ekle` testlerini tamamla. Kontrol ettikten sonra `PUBLISH_ENABLED=true` yap.

**Güvenlik:** Anahtarları sohbette paylaşma. `PUBLISH_ENABLED=false` güvenli varsayılandır, hesapların bağlanmadan yayınlama başlamaz. API'lerin ücretsiz kotaları ayrıca geçerlidir.
