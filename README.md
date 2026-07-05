# Türkiye Saatlik Elektrik Tüketim Tahmini

Türkiye'nin ülke geneli saatlik elektrik tüketimini, geçmiş tüketim verisi ve hava sıcaklığı bilgisiyle tahmin eden bir makine öğrenmesi projesi. Model, LightGBM ile kurulmuş olup test setinde **%1.66 MAPE** ve **0.977 R²** başarıya ulaşmaktadır.

## İçindekiler
- [Problem](#problem)
- [Veri](#veri)
- [Yaklaşım](#yaklaşım)
- [Özellik Mühendisliği](#özellik-mühendisliği)
- [Model ve Sonuçlar](#model-ve-sonuçlar)
- [Bulgular](#bulgular)
- [Kurulum ve Çalıştırma](#kurulum-ve-çalıştırma)
- [Gelecek İyileştirmeler](#gelecek-iyileştirmeler)

## Problem

Elektrik tüketiminin doğru tahmini, şebeke operatörleri için üretim planlaması ve arz-talep dengesi açısından kritik önem taşır. Bu projede amaç, Türkiye'nin ülke geneli saatlik elektrik tüketimini geçmiş verilere dayanarak tahmin eden bir model geliştirmektir. Tahmin ufku bir sonraki saattir ve model yalnızca tahmin anında bilinebilecek geçmiş bilgileri kullanır (veri sızıntısı — data leakage — önlenmiştir).

## Veri

- **Tüketim verisi:** [EPİAŞ Şeffaflık Platformu](https://seffaflik.epias.com.tr) — Gerçek Zamanlı Tüketim (kaynak: TEİAŞ). 2015 sonundan 2026 Temmuz'a kadar saatlik veri, yıllık dosyalar halinde indirilip birleştirilmiştir.
- **Sıcaklık verisi:** [Open-Meteo Historical Weather API](https://open-meteo.com) — İstanbul, Ankara ve İzmir için saatlik 2m sıcaklık verisi. Üç şehrin ortalaması, ülke geneli sıcaklığı temsil etmek üzere kullanılmıştır.

Toplam **~92.000 saatlik gözlem** (yaklaşık 10,5 yıl).

> **Not:** Ham veri dosyaları boyutları nedeniyle bu repoda tutulmamaktadır. Verinin nasıl indirileceği [`data/README.md`](data/README.md) dosyasında açıklanmıştır.

## Yaklaşım

Proje uçtan uca şu adımlardan oluşur:

1. **Veri toplama:** 11 yıllık tüketim verisi EPİAŞ'tan yıllık dosyalar halinde indirildi.
2. **Veri temizleme:**
   - Yıllık dosyalar birleştirildi; dosya sınırlarındaki çakışan (mükerrer) kayıtlar temizlendi.
   - 2016 yaz saati geçişinden (27 Mart 2016) kaynaklanan bir eksik ve bir sıfır değer tespit edilip zaman bazlı interpolasyonla düzeltildi.
   - Sonuç: tekrarsız, eksiksiz, kesintisiz saatlik seri.
3. **Keşifçi veri analizi (EDA):** Trend, mevsimsellik (yıllık/haftalık/günlük) ve korelasyon incelendi.
4. **Özellik mühendisliği:** Gecikme (lag), hareketli ortalama (rolling), döngüsel zaman kodlaması ve sıcaklık özellikleri üretildi.
5. **Modelleme:** LightGBM ile, zamana göre bölünmüş (kronolojik) train/test setleri üzerinde eğitim ve değerlendirme.
6. **İyileştirme:** Sıcaklık verisi eklenerek ve hiperparametre ayarı yapılarak model geliştirildi.

## Özellik Mühendisliği

Ham veride yalnızca tüketim değeri vardı. Modelin öğrenebilmesi için aşağıdaki özellikler üretildi:

| Özellik | Açıklama |
|---|---|
| `saat`, `gun`, `ay`, `haftanin_gunu`, `yil` | Temel takvim bilgileri |
| `lag_24` | 24 saat (1 gün) önceki tüketim |
| `lag_168` | 168 saat (1 hafta) önceki tüketim |
| `rolling_mean_24` | Son 24 saatin ortalama tüketimi (sızıntı önlemek için `shift(1)` ile) |
| `rolling_std_24` | Son 24 saatin oynaklığı (standart sapma) |
| `saat_sin`, `saat_cos` | Saatin döngüsel (sin/cos) kodlaması |
| `ay_sin`, `ay_cos` | Ayın döngüsel (sin/cos) kodlaması |
| `sicaklik` | Üç büyük şehrin ortalama saatlik sıcaklığı |

**Döngüsel kodlama neden?** Saat ve ay döngüsel değişkenlerdir (23:00'ten sonra 00:00, Aralık'tan sonra Ocak gelir). Düz sayı olarak verilirse model 23:00 ile 00:00'ı birbirine uzak sanar. Sin/cos dönüşümü, bu değerleri bir daire üzerine yerleştirerek komşuluk ilişkisini korur.

**Veri sızıntısının önlenmesi:** Rolling özellikler `shift(1)` ile hesaplanmıştır; böylece bir saati tahmin ederken o saatin kendi değeri ortalamaya dahil edilmez. Ayrıca train/test ayrımı rastgele değil **kronolojik** yapılmıştır (geçmişle eğit, gelecekte test et) — bu, gerçek kullanım senaryosunu yansıtır.

## Model ve Sonuçlar

**Model:** LightGBM Regressor (`n_estimators=1000`, `learning_rate=0.05`)
**Train/Test ayrımı:** ~2016–2025 Temmuz eğitim, son 1 yıl (2025 Temmuz – 2026 Temmuz) test.

### Performans karşılaştırması

| Model | MAE (MWh) | RMSE (MWh) | MAPE | R² |
|---|---|---|---|---|
| Temel model (sıcaklıksız, 500 ağaç) | 752 | 1.131 | %1.86 | 0.9704 |
| + Sıcaklık | 697 | 1.038 | %1.73 | 0.9751 |
| + Hiperparametre ayarı (final) | **667** | **995** | **%1.66** | **0.9771** |

Sıcaklık özelliğinin eklenmesi RMSE'yi ~%8 iyileştirmiştir; iyileşme özellikle yaz aylarındaki tepe (klima kaynaklı) tüketim noktalarında belirgindir.

## Bulgular

![Genel Trend](images/genel_trend.png)

*2015-2026 arası saatlik tüketim: belirgin yükseliş trendi, yıllık mevsimsellik ve 2020 (Covid) döneminde düşüş görülüyor.*

![Aylık Mevsimsellik](images/mevsimsellik.png)

*Aylara göre ortalama tüketim: yaz (klima) ve kış (ısıtma) aylarında zirve, geçiş mevsimlerinde düşüş.*

![Sıcaklık-Tüketim İlişkisi](images/sicaklik_iliskisi.png)

*Sıcaklık-tüketim ilişkisi U şeklindedir: hem soğukta hem sıcakta tüketim artar. Yaz klima etkisi daha güçlüdür.*

![Tahmin vs Gerçek](images/tahmin_vs_gercek.png)

*Final modelin test setindeki tahminleri (kırmızı) gerçek değerlerle (siyah) karşılaştırması — 2 haftalık kesit.*

### Öne çıkan bulgular

- **Güçlü mevsimsellik:** Tüketim yaz (klima) ve kış (ısıtma) aylarında zirve yapar; geçiş mevsimlerinde düşer. Günlük döngüde gece dip, gündüz plato görülür. Hafta sonu tüketimi hafta içine göre belirgin düşüktür.
- **Sıcaklık–tüketim ilişkisi U şeklindedir:** Hem düşük hem yüksek sıcaklıklarda tüketim artar. Doğrusal korelasyon (0.25) bu ilişkiyi yakalayamaz; ancak ağaç tabanlı model yakalayabilir. Yaz klima etkisi, kış etkisinden belirgin şekilde daha güçlüdür.
- **En güçlü tahmin edici geçmiş tüketimdir:** `lag_24` ve `lag_168`, tüketimin güçlü günlük ve haftalık otokorelasyonu sayesinde modelin en değerli girdileridir.
- **Modelin sınırı:** Sıcaklık eklenmeden önce model, aşırı sıcak günlerdeki tepe tüketimleri eksik tahmin ediyordu. Bu, hava bilgisinin eksikliğinden kaynaklanıyordu ve sıcaklık özelliğiyle giderildi.

## Kurulum ve Çalıştırma

```bash
# Depoyu klonlayın
git clone https://github.com/KULLANICI_ADI/turkey-electricity-forecast.git
cd turkey-electricity-forecast

# Gerekli kütüphaneleri kurun
pip install -r requirements.txt

# Notebook'u açın
jupyter notebook notebooks/elektrik_tuketim_tahmini.ipynb
```

Veriyi indirmek için [`data/README.md`](data/README.md) dosyasındaki adımları izleyin.

## Gelecek İyileştirmeler

- **Resmi tatil ve bayram günleri özelliği:** Bayramlarda tüketim belirgin düşer (ör. 2020 Ramazan Bayramı verideki en düşük değerlerden bazılarını içerir). Bir "tatil mi?" özelliği modeli güçlendirebilir.
- **Çok adımlı tahmin:** Yalnızca bir sonraki saat yerine, önümüzdeki 24 saati tahmin etme.
- **Ek hava değişkenleri:** Nem, rüzgâr, güneşlenme gibi değişkenlerin etkisi araştırılabilir.
- **Model karşılaştırması / stacking:** XGBoost, CatBoost gibi modellerle karşılaştırma ve topluluk (ensemble) yöntemleri.
- **Streamlit demo:** Modeli etkileşimli bir web arayüzüyle yayınlama.

---

*Bu proje, veri toplama, temizleme, özellik mühendisliği, modelleme ve iyileştirme adımlarını içeren uçtan uca bir zaman serisi çalışmasıdır.*