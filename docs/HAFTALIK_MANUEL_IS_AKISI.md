# Semtaş Dijital — Haftalık manuel içerik / otomatik onay ve sıra modeli

## 2–6 Kasım 2026 ilk paket
- Plan ve özgün Instagram + LinkedIn metinleri: `content/weeks/2026-11-02.json`
- Beş günlük ayrı kayıt: `content/posts/YYYY-MM-DD.json`
- Görsel dosyaları `docs/media/` altında; üç önceki premium tasarım + iki fotoğrafik editoryal yeni kompozisyon
- Beş GitHub Mobile onay kaydı: Issues #4–#8
- Tasarım ve yayınlama için **ücretli Gemini API çağrısı yapılmaz**.

## Haftalık operasyon
1. Kullanıcı her hafta ChatGPT sohbetinde haftalık planını ve görsellerini ister.
2. Editör beş içerik, Türkçe caption, doğru logo, 4:5 görsel ve tarihleri hazırlar; GitHub'a koyar.
3. Her gönderi için ayrı GitHub Issue oluşturulur; sahibi `exman3408` görseli ve caption'ı mobilde inceler.
4. `/onayla` yalnızca o Issue'nun ilgili içerik sürümünü onaylar. `/reddet` yayın iznini reddeder.
5. `/revize <talimat>` onayı iptal eder ve revize notunu kaydeder; **tasarımı bu haftalık manuel modelde ChatGPT sohbeti üzerinden editör yeniden hazırlar**. Şu anda GitHub Actions tek başına ücretli görsel API kullanmaz.
6. `queue.yml` hafta içi İstanbul saatiyle 11:10'da yalnızca **o güne gelmiş** ve GitHub sahibi tarafından onaylanmış gönderileri Buffer kuyruğuna alabilir.
7. `PUBLISH_ENABLED=false` kaldığında hiçbir içerik Buffer kuyruğuna gitmez; yayına geçmek için kullanıcı bir defa **GitHub Settings > Secrets and variables > Actions > Variables > PUBLISH_ENABLED=true** seçmelidir. Bu global anahtar **onay gerekliliğini kaldırmaz**, sadece onaylananlar için Buffer gönderimini etkinleştirir.
8. Buffer, içeriği kendi hesap için belirlenen yayın saatlerinde paylaşabilir. Buffer takvim saatleri ayrıca kontrol edilmelidir.

## Yayın güvenliği ve hesaplar
- Anahtarlar yalnızca GitHub Secrets'ta kalır.
- Mevcut Instagram ve LinkedIn kanal bilgileri doğrulanmıştır; Facebook bu pakette hedeflenmez.
- Buffer kuyruğuna yanlışlıkla alınmaması için onaysız / revize bekleyen durumları `socialbot.__main__.queue` kontrol eder.
- Görsellerde iddia edilen gerçek olmayan metrikler, logo taklitleri ve sahte müşteri referansları kullanılmaz.
- Haftalık içerik hazırlama GitHub Actions cron'u kapalıdır; bu iş kullanıcı isteği üzerine yapılır. Eski ChatGPT saatlik revize izleme otomasyonu manuel modele geçildiğinden duraklatılmıştır.
