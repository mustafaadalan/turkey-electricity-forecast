# Veri

Bu projede kullanılan ham veri dosyaları boyutları nedeniyle bu depoda tutulmamaktadır. Aşağıdaki adımlarla veriyi kendiniz indirebilirsiniz.

## 1. Tüketim Verisi (EPİAŞ)

1. [EPİAŞ Şeffaflık Platformu](https://seffaflik.epias.com.tr)'na girin (veri indirmek için ücretsiz üyelik gerekir).
2. Sol menüden **Elektrik → Elektrik Tüketim → Gerçekleşen Tüketim → Gerçek Zamanlı Tüketim** yolunu izleyin.
3. Tarih aralığını seçip (sistem tek seferde en fazla ~1 yıl verir) verileri yıllık dosyalar halinde CSV olarak indirin.
4. İndirdiğiniz CSV dosyalarını bu `data/` klasörüne yerleştirin.

Dosya formatı: noktalı virgül (`;`) ayraçlı, Türkçe sayı formatı (binlik `.`, ondalık `,`), UTF-8-BOM kodlaması. Sütunlar: `Tarih`, `Saat`, `Tüketim Miktarı(MWh)`.

## 2. Sıcaklık Verisi (Open-Meteo)

Sıcaklık verisi, notebook içinde [Open-Meteo Historical Weather API](https://open-meteo.com) üzerinden otomatik olarak çekilir — ayrıca indirmeye gerek yoktur. API anahtarı gerektirmez.

İstanbul, Ankara ve İzmir için saatlik 2m sıcaklık verisi alınır ve üç şehrin ortalaması hesaplanır.

## Notlar

- Tüm veri işleme adımları (birleştirme, temizleme, özellik üretimi) notebook içinde yer alır.
- Notebook'u çalıştırdığınızda, temizlenmiş veri `elektrik_tuketimi_temiz.csv` olarak kaydedilir.
