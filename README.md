# SEMTAŞ DİJİTAL — SOCIAL AUTOPILOT V2

**Durum: Çalıştırılabilir paket, henüz hesaba bağlı / canlı değil.** Varsayılan `PUBLISH_ENABLED=false`. Hiçbir hesabın anahtarı bu paket içinde bulunmaz. Canlı yayınlama ancak kullanıcı Buffer + Gemini + GitHub bağlayıp bu anahtarı etkinleştirdikten sonra başlar. GitHub Actions zamanlama ve üçüncü taraf servis çalışırlığı nedeniyle yüzde yüz kesintisiz yayın garantisi yoktur.

## Neler var?

- Semtaş'ın **kullanıcı tarafından sağlanan gerçek siyah ve beyaz logosu** (`assets/brand/`). Logoyu her yeni tasarımın içine orantılı yerleştirir.
- Önceden onaylanan **web tasarım, reklam yönetimi ve Shopify** postları (`docs/media/approved-*.png`). Bu üç görsel, ilgili konu ilk kez hazırlandığında bir defaya mahsus kullanılır. Web görselindeki doğrulanmamış `+%187` ve `100+ marka` rakamları *yayınlanan sürümde* kaldırıldı. Orijinaller yalnızca `assets/approved/` içinde referans olarak tutulur.
- Sonraki günlerde **Google News RSS araştırması + Gemini 3.5 Flash-Lite ücretsiz API katmanı** ile Türkçe konu/metin üretimi. RSS yalnızca fikir sağlar; kaynaklar doğrulanmış iddia gibi kullanılmaz. API kullanımı ChatGPT Plus'a dahil değildir.
- Takip eden içerikler için **Pillow ile marka renklerinde fotoğrafsız, premium tipografik PNG şablonları**. Bunlar görsel üretim modeli ile sinematik fotoğraf üretmez; üretilen yeni tasarımlar, onaylı üç posterin bire bir kopyası değildir.
- **Buffer GraphQL API** ile Instagram, Facebook ve LinkedIn için ilgili metin ve PNG'yi otomatik **Buffer yayın kuyruğuna ekleme** (Buffer daha sonra otomatik yayınlar).
- Haftalık gerçek Buffer API metriklerinden rapor. API'nin sağlamadığı istatistikler üretilmez.
- Tekrar gönderim kontrolü, doğrulanmamış sosyal hesap/erişilemeyen görsel için güvenli durdurma, varsayılan kapalı yayın.

## Yayın akışı (Europe/Istanbul)

| Gün | Konu | Kanal |
|---|---|---|
| Pazartesi | Web tasarım / dönüşüm | Instagram, Facebook |
| Salı | Google & Meta Ads | LinkedIn |
| Çarşamba | Teknik SEO | Instagram, Facebook |
| Perşembe | Premium Shopify | LinkedIn |
| Cuma | Dijital strateji | Instagram, Facebook |

Her iş günü **08:10** içerik hazırlanır, GitHub Pages'de kamuya açık HTTPS medya bağlantısı oluşturulur. **11:10** yayına uygun medya Buffer'ın **sıradaki yayın saatine** eklenir; gerçek paylaşım saatini Buffer'da her hesap için ayrı tanımlamalısınız. Pazartesi **12:00** rapor oluşturulur (GitHub Actions > artifacts). GitHub zamanlanmış işlerde gecikmeler yaşanabilir.

## 0. Hesapları ücretsiz seçenekleriyle aç

1. **Buffer Free**: https://buffer.com (3 kanal; her kanalda sırada en fazla 10 post; Buffer API erişimi var). Bağlanacak üç hesap Semtaş Dijital Instagram profesyonel hesabı, Facebook Sayfası ve LinkedIn hesabı/Şirket Sayfası olmalı. İşletme sayfasını tercih edin.
2. **Google AI Studio**: https://aistudio.google.com/apikey , ücretsiz model kotanızı kontrol edip API anahtarı oluşturun. Bu modelin ücretsiz kotası ve ülke uygunluğu değişebilir; ücretli faturalandırma açmanız gerekmez, ama ücretsiz sınırı aşınca otomasyon metin üretmeyi durdurur. Google ücretsiz API katmanındaki gönderimleri hizmetlerini geliştirmek amacıyla kullanabilir: müşteri sırrı/kişisel veri göndermeyin.
3. **GitHub**: https://github.com/new üzerinden **public** `semtas-social-autopilot` reposu oluşturun, boş tutun (**README oluşturma**). GitHub Pages'i ücretsiz kullanmak için public repo seçtik. Bu repodaki kaynak ve içerikler kamuya açık olacaktır; gizli müşteri bilgileri eklemeyin.

**ÖNEMLİ:** API anahtarlarını hiçbir zaman ChatGPT konuşmasına, commit'e, ekran görüntüsüne veya `content/posts` içine koymayın. Yalnızca GitHub **Secrets** bölümüne girin.

## 1. GitHub'a dosyaları aktar (Windows PowerShell)

V2 ZIP içindeki `semtas-social-autopilot` klasörünü çıkartın, klasörde PowerShell açın:

```powershell
git init
git add .
git commit -m "Semtas Social Autopilot V2"
git branch -M main
git remote add origin https://github.com/GITHUB_KULLANICI/semtas-social-autopilot.git
git push -u origin main
```

`GITHUB_KULLANICI` yerini gerçek kullanıcı adınızla değiştirin. Git yüklü değilse https://git-scm.com/downloads/win . `.env` varsa `.gitignore` onu dışarıda tutar.

## 2. GitHub Secrets ve Variables gir

Repo -> **Settings > Secrets and variables > Actions**:

**Secrets (gizli):**

| Ad | Değer |
|---|---|
| `BUFFER_API_KEY` | Buffer > Settings > API'de oluşturulan kişisel API key |
| `GEMINI_API_KEY` | AI Studio'daki anahtar |

**Variables (gizli değil):**

| Ad | Değer |
|---|---|
| `BUFFER_ORG_ID` | Semtaş Buffer organization ID |
| `BUFFER_INSTAGRAM_CHANNEL_ID` | Semtaş Instagram ID |
| `BUFFER_FACEBOOK_CHANNEL_ID` | Semtaş Facebook Sayfası ID |
| `BUFFER_LINKEDIN_CHANNEL_ID` | Semtaş LinkedIn ID |
| `MEDIA_BASE_URL` | `https://GITHUB_KULLANICI.github.io/semtas-social-autopilot/media` |
| `PUBLISH_ENABLED` | `false` *(ilk testte mutlaka!)* |

Önce **BUFFER_API_KEY** secret'ı girin. **Actions > 0 - Test ve Buffer baglanti kontrolu > Run workflow** çalıştırın. Logda kendi Buffer organization ve kanal ID'lerinizi göreceksiniz. Bunları yukarıdaki variable'lara girin. Başka müşterilerin kanallarını kesinlikle kopyalamayın. Ayrıca yayın akışında kanal adı içinde güvenlik amacıyla `semtas`/`semtaş` kontrolü yapılır. Hesap adı bambaşka ise hatayla durur; önce doğru hesabı doğrulayın.

## 3. GitHub Pages ve yayın öncesi test

- Repo **Settings > Pages > Build and deployment > Source: GitHub Actions** olarak ayarlayın.
- Repo **Settings > Actions > General > Workflow permissions** içinde içerik commit etmek için uygun izinleri sağlayın. `prepare` ve `queue` iş akışları zaten `contents: write` ilan eder.
- **Actions > 1 - Semtas icerik hazirla** çalıştırın. Hafta içiyse bugün için içerik hazırlar; hafta sonu içerik oluşturmaz. İçerik ilgili konu için ilk kez hazırlanmıyorsa **GEMINI_API_KEY** gerekir.
- **Actions > 2 - Semtas Buffer kuyruguna ekle** çalıştırın. `PUBLISH_ENABLED=false` olduğu sürece hiçbir Buffer isteği ile paylaşım gönderilmez.
- `https://GITHUB_KULLANICI.github.io/semtas-social-autopilot/media/approved-web.png` URL'sini gizli sekmede açın. Görsel doğrudan görüntülenmeli. Buffer görsele paylaşım günü de ulaşabilmelidir; GitHub Pages'i silmeyin/kapatmayın.
- Buffer üzerinde Instagram/Facebook ve LinkedIn kanallarını, hesap adlarını, yayın saatlerini ve ilk içerikleri kontrol edin.
- **Yalnızca kontroller tamamlandıktan sonra** `PUBLISH_ENABLED=true` yapın. Sonraki `queue` iş akışı görselleri Buffer kuyruğuna ekler; gerçek yayın Buffer'ın saatlerine göre olur.
- `PUBLISH_ENABLED=false` yapmak yeni eklemeleri durdurur, **Buffer'da daha önce sıraya eklenmiş gönderileri silmez**. Bunları Buffer'dan ayrıca duraklatın/silin.

## 4. Yerel test

```powershell
py -m pip install -r requirements.txt
py -m unittest discover -s tests -v
py -m socialbot demo
```

Bu komutlar API gerektirmez. `demo/semtas-sample.png` otomatik logo kullanan görsel şablonunu verir. Gerçek hesap bağlantısı için `.env.example` dosyasını `.env` adıyla kopyalayıp anahtar ve ID'leri yazın; bu dosya git'e eklenmez.

Diğer komutlar: `py -m socialbot channels`, `prepare`, `queue`, `status`, `report`.

## Format, güvenlik ve gerçekçi sınırlamalar

- **Tek görselli PNG** yayını tam otomatik. Reels, Story, 4:5 çoklu karusel, videolu sinematik üretim henüz otomatik değil.
- AI yalnızca profesyonel reklam / eğitim önerileri yazar; kaynak doğrulanmadan güncel istatistik, yorum, vaka çalışması, başarı sonucu, alıntı veya kampanya vaatlerini paylaşmaz. Metin kontrolü yüzde gibi sayıları engeller, ama bu tam bir doğruluk garantisi değildir. Düzenli insan denetimi önerilir.
- **Buffer** API yalnızca dışarıdan erişilebilir HTTPS görsellerini kabul eder. Bu nedenle `docs/media` GitHub Pages üzerinden public sunulur. Varsa bot engeli/Pages sorunu yayınlamayı durdurur.
- **Gizlilik:** GitHub public repo `content/posts` metinlerini ve görselleri kamuya açar. API anahtarları secret olarak tutulur. Buffer gönderisini kuyruğa ekleme/silinme hataları loglarda görünür; otomatik durum eşleme/silah olmayan ufak arızalar insan denetimi gerektirebilir.
- **Plus** ayrı OpenAI API kredisi vermez. Bu paket Gemini'nin ücretsiz katmanını kullanır. Ücret gerektirmeden çalışması ilgili servislerin ücretsiz kotalarına bağlıdır.

## Resmi teknik referanslar

- https://buffer.com/pricing
- https://developers.buffer.com/examples/create-image-post.html
- https://developers.buffer.com/guides/hosting-media.html
- https://developers.buffer.com/guides/posts-and-scheduling.html
- https://developers.buffer.com/guides/post-metrics
- https://ai.google.dev/gemini-api/docs/pricing
- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
