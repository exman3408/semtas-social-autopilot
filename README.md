# Semtaş Dijital — Social Autopilot

Bu depo Semtaş Dijital'in sosyal medya otomasyon kurulumu içindir.

## Kurulum (V2)

1. ChatGPT'te hazırlanan **Semtas_Dijital_Tam_Otomasyon_V2.zip** arşivini bilgisayarına indirip aç.
2. Açılan `semtas-social-autopilot` klasörünün **içindeki tüm dosyaları ve gizli `.github` klasörünü** bu deponun köküne yükle. GitHub **Add file > Upload files** ile yüklenebilir. Arşivin kendisini yükleme.
3. `Settings > Pages > Build and deployment` içinden kaynağı **GitHub Actions** olarak ayarla.
4. `Settings > Secrets and variables > Actions` bölümünde:
   - Secrets: `BUFFER_API_KEY`, `GEMINI_API_KEY`
   - Variables: `BUFFER_ORG_ID`, `BUFFER_INSTAGRAM_CHANNEL_ID`, `BUFFER_FACEBOOK_CHANNEL_ID`, `BUFFER_LINKEDIN_CHANNEL_ID`, `MEDIA_BASE_URL=https://exman3408.github.io/semtas-social-autopilot/media`, `PUBLISH_ENABLED=false`.
5. `Actions` içinden `0 - Test ve Buffer baglanti kontrolu` işini çalıştır. Hesapları ve kanal kimliklerini doğrula.
6. `1 - Semtas icerik hazirla` ardından `2 - Semtas Buffer kuyruguna ekle` işlerini **test modunda** çalıştır.

**Güvenlik:** API anahtarlarını GitHub deposuna, sohbet içine veya ekran görüntüsüne yapıştırma. `PUBLISH_ENABLED=false` iken canlı Buffer kuyruğuna paylaşım gönderilmez. Canlıya alma öncesinde gerçek medya URL'lerinin erişimini ve Instagram/Facebook/LinkedIn hesap eşleştirmesini kontrol et. Yeni oluşturulan görseller şablon tabanlıdır; ilk üç premium görsel birebir kalitede otomatik olarak yeniden üretilmez.

**Durum:** Bu README hazırlanmıştır; V2 kaynak kodlarının ve görsellerin tamamı GitHub'a yüklenene dek otomasyon çalışmaz.
