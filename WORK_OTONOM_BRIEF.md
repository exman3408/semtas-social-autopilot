# SEMTAŞ DİJİTAL — OTONOM TASARIM VE YAYIN ÇALIŞMA BRİFİ

## Amaç
Semtaş Dijital’in mevcut otomasyonunu devral. GitHub Issues üzerinden taslakları kontrol et, sadece sahibi **exman3408** tarafından girilmiş revize komutlarını işleme al. Yüksek kaliteli, premium, marka kimliğini koruyan yeni görsel taslakları oluştur; yeni görseli GitHub reposuna kaydet ve tekrar mobil onaya gönder. Onay almadan Buffer’a yayınlama yapma.

## Bağlantılar
- GitHub: https://github.com/exman3408/semtas-social-autopilot
- Revizyon Issue: https://github.com/exman3408/semtas-social-autopilot/issues/1
- Taslak kayıtları: `content/posts/YYYY-MM-DD.json`
- Görsellerin yayınlandığı kaynak: `docs/media/`
- Gerçek marka logoları: `assets/brand/`
- Önceden beğenilen örnekler: `assets/approved/` ve `docs/media/approved-*.png`
- Onay işleyici: `socialbot/review.py`
- Buffer koruma: `socialbot/__main__.py` (review.status + PUBLISH_ENABLED)

## Güncel durum
- 30 Ekim 2026 taslağının önceki /onayla komutu **test** amaçlıydı.
- Bu gönderinin review.status alanı `revision_requested` olarak değiştirildi ve yayın izni iptal edildi.
- Kullanıcı onayladığı 3 premium posterin gerçek tasarım düzeyini istiyor; mevcut Pillow şablonları kalite açısından yeterli değil.
- `/revize ...` komutu, yorumun kaynağı ve talep metni GitHub Actions ile kayıt altına alınır.
- ChatGPT’nin saatlik revizyon takip görevi var, ancak otomatik görsel üretip GitHub’a ikili dosya yükleyebilme yetkisi çalışma ortamına göre değişir. Yapılamayan işlemi yapıldı gibi gösterme.

## Tasarım standartları
- 1080x1350 (Instagram 4:5), LinkedIn için 1200x1200 gerekirse.
- Gerçek logo dosyasını yerleştir; soyut AI uydurma logo üretme. Açık zemin siyah, koyu zemin beyaz versiyon.
- Premium, yüksek kontrastlı ama dengeli tipografi; kreatif reklam ajansı düzeyinde görsel kompozisyon; konuya uygun zengin sahne ve somut metaforlar.
- Yalnızca onaylanmış gerçek verileri kullan; uydurma yüzde, müşteri referansı ve rakam yazma.
- Görseldeki Türkçe metni kontrol et; kırpılma, bozuk karakter, yanlış logo olmasın.

## Yeni revizyonu yayınlamak için güvenli protokol
1. Yalnızca owner'ın /revize yorumundan veya review.status=revision_requested durumundan iş al.
2. Talebi okuyup görseli oluştur. Görsel üretimi için ayrı ücretli API gerektiğinde kullanıcı onayı olmadan faturalandırma açma.
3. Yeni görseli `docs/media/` altına **yeni dosya adıyla** yükle. Mevcut imajın üstüne yazma. GitHub Pages URL'sini doğrula.
4. `content/posts/YYYY-MM-DD.json` içinde `media_file`i yeni sürüme geçir; `review` alanını `status=pending`, `issue_number` yeni oluşturulmuş Issue numarası, `requested_at` yeni zaman ile güncelle; eski test onayı taşınmasın.
5. Yeni Issue içinde orijinal marka görselini ve tüm platform metinlerini göster. Konuyu owner'a ata ve etiketle.
6. Buffer'a otomatik gönderim yapma. Sadece kullanıcının bu yeni Issue'da /onayla yorumu sonrasında ve PUBLISH_ENABLED=true iken Buffer sırasına alınabilir.
7. Erişilemeyen araç, özel anahtar veya gerekli kullanıcı onayı varsa dur ve net blocker bildir. Hiçbir onayı atlama.

## Takip yöntemi
Yeni GitHub Issues /revize yorumlarını periyodik izle. GitHub Work olay tetikleyicileri yalnızca desteklenen olayları dinleyebilir; doğrudan GitHub Issue yorumu tetiklenmiyorsa zamanlanmış saatlik kontrol kullan. Aynı comment_id'yi ikinci kez işleme alma.
