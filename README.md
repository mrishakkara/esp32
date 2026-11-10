# CLOUD CODE — Browser Cloud Compiler

Tarayıcı tabanlı C++ ve ESP32 Arduino derleyici prototipi.

## Özellikler
- Tarayıcı editörü (dosyayı bilgisayarına kaydetmeden kod yazma)
- C++ kodunu Wandbox'ın izole derleme/çalıştırma servisiyle deneme
- Windows `.exe` üretimi (sunucuda MinGW-w64 varsa)
- ESP32-WROOM-32 için Arduino `.bin` üretimi (sunucuda Arduino CLI + ESP32 core varsa)
- Derleme çıktısı ve hata konsolu

## Yerel başlatma
Python 3.11+ gerekir.

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```
Tarayıcıda `http://127.0.0.1:8000` aç.

Sadece C++ çalıştırma özelliği Wandbox API ile kullanılabilir. EXE ve ESP32 BIN için Docker imajında bulunan derleyiciler gerekir:

```bash
docker build -t cloud-code .
docker run --rm -p 10000:10000 cloud-code
```
Ardından `http://localhost:10000` aç.

## Ücretsiz yayınlama
1. Bu klasörü bir GitHub deposuna yükle.
2. Render'da **New → Web Service → Connect repository** seç.
3. Runtime Docker olarak algılanır; planı Free seç.
4. Deploy tamamlanınca verilen `onrender.com` adresini aç.

### Ücretsiz katman uyarısı
Ücretsiz web sunucuları 15 dakika trafik olmazsa uykuya geçebilir ve yeniden açılırken yaklaşık bir dakika bekletebilir. Dosya sistemi kalıcı değildir. Ücretsiz kaynaklarda ESP32 toolchain kurulumu veya derlemesi bellek/zaman sınırına takılabilir. Bu nedenle bu sürüm bir prototiptir; sürekli ve güvenilir derleme garantisi vermez. C++ çalıştırma Wandbox'ın ücretsiz, üçüncü taraf API'sine bağlıdır.

## Güvenlik notu
Bu proje herkese açık üretim hizmeti olarak kullanılmaya hazır değildir. Kod uzunluğu ve süre sınırları vardır; EXE derlenir ama sunucuda çalıştırılmaz. ESP32 derlemesi de sunucuda geçici dosyalar oluşturur. Genel kullanıma açmadan önce ayrı, güçlü izolasyonlu derleme işçileri, oran sınırlama, kimlik doğrulama ve kaynak kotaları eklenmelidir.

## ESP32 hedef kartı
Varsayılan hedef `esp32:esp32:esp32` (ESP32 Dev Module / klasik ESP32-WROOM-32).
