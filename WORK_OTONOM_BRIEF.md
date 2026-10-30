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

## 30 Ekim 2026 API ve revizyon motoru güncellemesi
- Gemini API anahtarı `socialbot.keycheck` ile ücretli üretim yapmadan `GET /v1beta/models` üzerinden doğrulanır. Anahtarın model listesini göstermesi ilgili modelin ücretsiz olduğunu **kanıtlamaz**.
- Resmi Gemini API fiyatlandırmasında `gemini-nano-banana-2.1`, `gemini-3-pro-image`, `gemini-3.1-flash-image` görüntü çıkışı için **ücretsiz katman bulunmuyor**. Google AI Pro aboneliği API faturalandırması değildir.
- Güvenli ücretsiz varsayılan `IMAGE_ENGINE=premium_pillow`. Bu, gerçek logo ile grafik üretir ama Nano Banana veya ChatGPT görsel oluşturma düzeyinde fotoğraf/3D üretimi **değildir**.
- `IMAGE_ENGINE=gemini` istenirse `ALLOW_PAID_GEMINI_IMAGE_API=true` onayı gerekir; mevcut GitHub Actions iş akışları değeri **false** olarak kilitler. Ücretli çağrı kullanıcı izni olmadan yapılmaz.
- `socialbot.creative`: isteğe bağlı Nano Banana 2.1/Pro entegrasyonu, üç onaylı referans görseli aktarımı, gerçek Semtaş logosunu ve Türkçe metinleri sonradan birebir kompozit eder.
- `socialbot.revise`: her `/revize ...` için yeni dosya (ör. `semtas-YYYY-MM-DD-r2.png`), Pages dağıtımı ve yeni GitHub Mobile onay Issue'su oluşturma.
- İkinci onay gelmeden Buffer kuyruğuna yeni içerik eklenmez. Önceki Issue kapatılır; eski `/onayla` yalnızca eski sürümde kalır ve geçersizdir.
- `socialbot.keycheck` yalnızca API anahtarını kontrol eder, **ücretli görüntü API çağrısı yapmaz**.
- İlk revizyon başlatıcısı: `.github/workflows/revise.yml`. Sonraki revizyonlar: `.github/workflows/approve.yml`.
- Medya servisi ve GitHub Issues canlıda ayrıca doğrulanmalıdır; test veya API hazır olması, Nano Banana görüntüsü üretildiği anlamına gelmez.


## Kalite kararı — 30 Ekim 2026 (en güncel)
Kullanıcı V2 ve V3 çizim/şablon çıktılarından açıkça memnun değil. Bu tasarımlar kabul edilmedi; V3 GitHub onayı iptal edildi. Kullanıcı yalnızca fotoğrafik, sinematik, kreatif ajans seviyesinde gerçek görseller istiyor. Gerçek logoyu birebir kullan, Photoshop/retouch düzeyinde kaliteli sayfa yapısı, Türkçe kusursuz tipografi uygula. Doğrulanmamış başarı sayısı, yüzde, ROAS, müşteri logosu veya teklif uydurma. Basit çizim, wireframe, browser kutusu, soyut circle pattern kesinlikle kullanma.
- Tüm otomatik görsel iş akışları `IMAGE_ENGINE=gemini`, `REQUIRE_GENERATIVE_IMAGE=true` ile çalışmalıdır.
- `ALLOW_PAID_GEMINI_IMAGE_API=false` varsayılan. Nano Banana API için **ücretsiz görüntü üretim katmanı yoktur**; Google AI Pro uygulama aboneliği API erişim maliyetini karşılamaz.
- Kullanıcı açık ücret onayı vermeden faturalandırılabilecek bir görsel isteği yapma. Anahtarın model listesini döndürmesi ücretsiz üretime izin verildiği anlamına gelmez.
- Model erişimi/izin eksikse taslak üretimini güvenle durdur ve kullanıcıya engeli bildir. Düşük kaliteli Pillow fallback kesinlikle kullanma.
- Mobil onay yalnızca üretilmiş ve doğru kalite kontrolünden geçmiş **yeni** görsel dosyası için açılmalı.
