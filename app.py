"""
Türkiye Saatlik Elektrik Tüketim Tahmini - Streamlit Demo
"""
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Sayfa ayarları
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Türkiye Elektrik Tüketim Tahmini",
    page_icon="⚡",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Veri ve model yükleme (bir kez yüklenip önbelleğe alınır)
# ---------------------------------------------------------------------------
@st.cache_resource
def model_yukle():
    return joblib.load("model/model.pkl")

@st.cache_data
def veri_yukle():
    df = pd.read_csv("model/test_verisi.csv", index_col=0, parse_dates=True)
    return df

@st.cache_data
def ozellik_yukle():
    with open("model/ozellikler.json", "r", encoding="utf-8") as f:
        return json.load(f)

model = model_yukle()
test_df = veri_yukle()
ozellikler = ozellik_yukle()

# ---------------------------------------------------------------------------
# Başlık
# ---------------------------------------------------------------------------
st.title("⚡ Türkiye Saatlik Elektrik Tüketim Tahmini")
st.markdown(
    "10 yıllık gerçek EPİAŞ verisi, hava sıcaklığı ve resmi tatil bilgisiyle "
    "eğitilmiş bir **LightGBM** modeli. Test setinde **%1.62 MAPE** ve **0.979 R²**."
)

# ---------------------------------------------------------------------------
# Sekmeler
# ---------------------------------------------------------------------------
sekme1, sekme2, sekme3 = st.tabs(["🔮 Tahmin", "📊 Model Performansı", "🔍 Veri Analizi"])

# ===========================================================================
# SEKME 1: TAHMİN
# ===========================================================================
with sekme1:
    st.subheader("Bir gün seç, modelin tahminini gör")
    st.caption(
        "Test setinden (2025–2026, modelin eğitimde görmediği veri) bir gün seçin. "
        "Model o günün 24 saatini tahmin eder; gerçek değerlerle karşılaştırılır."
    )

    # Test setindeki mevcut günleri bul
    mevcut_gunler = sorted(test_df.index.normalize().unique())
    ilk_gun = mevcut_gunler[0].date()
    son_gun = mevcut_gunler[-1].date()
    varsayilan = mevcut_gunler[min(40, len(mevcut_gunler) - 1)].date()

    kol_tarih, kol_bilgi = st.columns([1, 2])
    with kol_tarih:
        secilen_gun = st.date_input(
            "Tarih seçin:",
            value=varsayilan,
            min_value=ilk_gun,
            max_value=son_gun,
            format="DD.MM.YYYY",
        )
    with kol_bilgi:
        st.info(
            f"Seçilebilir aralık: **{ilk_gun.strftime('%d.%m.%Y')}** – "
            f"**{son_gun.strftime('%d.%m.%Y')}**  \n"
            "Takvimden istediğiniz günü seçin."
        )

    # Seçilen günün verisini al
    gun_str = secilen_gun.strftime("%Y-%m-%d")
    if gun_str in test_df.index.normalize().strftime("%Y-%m-%d"):
        gun_verisi = test_df.loc[gun_str].copy()
    else:
        gun_verisi = pd.DataFrame()

    if len(gun_verisi) > 0:
        # Tahmin yap
        X_gun = gun_verisi[ozellikler]
        tahmin = model.predict(X_gun)
        gercek = gun_verisi["tuketim_mwh"].values

        # Metrikler (o gün için)
        mae_gun = np.mean(np.abs(gercek - tahmin))
        mape_gun = np.mean(np.abs((gercek - tahmin) / gercek)) * 100

        kol1, kol2, kol3 = st.columns(3)
        kol1.metric("Ortalama Gerçek Tüketim", f"{gercek.mean():,.0f} MWh")
        kol2.metric("Ortalama Tahmin", f"{tahmin.mean():,.0f} MWh")
        kol3.metric("O günkü hata (MAPE)", f"%{mape_gun:.2f}")

        # Grafik: o günün 24 saati
        fig, ax = plt.subplots(figsize=(10, 4.5))
        saatler = range(len(gercek))
        ax.plot(saatler, gercek, label="Gerçek", linewidth=2.5, color="#1a1a1a", marker="o", markersize=4)
        ax.plot(saatler, tahmin, label="Tahmin", linewidth=2, linestyle="--", color="#e63946", marker="s", markersize=4)
        ax.set_xlabel("Saat")
        ax.set_ylabel("Tüketim (MWh)")
        ax.set_title(f"{secilen_gun.strftime('%d.%m.%Y')} — Saatlik Tahmin vs Gerçek")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xticks(range(0, 24, 2))
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)

        # Sıcaklık bilgisi
        st.caption(
            f"O günün ortalama sıcaklığı: **{gun_verisi['sicaklik'].mean():.1f}°C** "
            f"(min {gun_verisi['sicaklik'].min():.1f}°C, max {gun_verisi['sicaklik'].max():.1f}°C)"
        )
    else:
        st.warning("Bu gün için veri bulunamadı. Başka bir gün seçin.")

# ===========================================================================
# SEKME 2: MODEL PERFORMANSI
# ===========================================================================
with sekme2:
    st.subheader("Modelin genel performansı")
    st.caption("Test seti: 2025 Temmuz – 2026 Temmuz (modelin eğitimde görmediği 1 yıl).")

    # Tüm test seti üzerinde tahmin
    X_test = test_df[ozellikler]
    y_test = test_df["tuketim_mwh"].values
    y_pred = model.predict(X_test)

    mae = np.mean(np.abs(y_test - y_pred))
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    ss_res = np.sum((y_test - y_pred) ** 2)
    ss_tot = np.sum((y_test - y_test.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("MAE", f"{mae:,.0f} MWh")
    k2.metric("RMSE", f"{rmse:,.0f} MWh")
    k3.metric("MAPE", f"%{mape:.2f}")
    k4.metric("R²", f"{r2:.4f}")

    st.markdown("---")

    # Kesit seçici
    st.markdown("**Belirli bir dönemi yakından incele:**")
    hafta_sayisi = st.slider("Kaç günlük kesit gösterilsin?", 3, 30, 14)

    baslangic_idx = st.slider(
        "Başlangıç noktası (test seti içinde)",
        0, max(0, len(test_df) - hafta_sayisi * 24), 720
    )

    kesit = slice(baslangic_idx, baslangic_idx + hafta_sayisi * 24)
    fig2, ax2 = plt.subplots(figsize=(11, 4.5))
    ax2.plot(test_df.index[kesit], y_test[kesit], label="Gerçek", linewidth=2, color="#1a1a1a")
    ax2.plot(test_df.index[kesit], y_pred[kesit], label="Tahmin", linewidth=1.5, linestyle="--", color="#e63946")
    ax2.set_xlabel("Tarih")
    ax2.set_ylabel("Tüketim (MWh)")
    ax2.set_title(f"{hafta_sayisi} Günlük Kesit — Tahmin vs Gerçek")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    fig2.tight_layout()
    st.pyplot(fig2, use_container_width=True)

# ===========================================================================
# SEKME 3: VERİ ANALİZİ
# ===========================================================================
with sekme3:
    st.subheader("Veriden çıkan içgörüler")

    kol_a, kol_b = st.columns(2)

    with kol_a:
        st.markdown("**Saatlere göre ortalama tüketim**")
        saatlik = test_df.groupby(test_df.index.hour)["tuketim_mwh"].mean()
        fig3, ax3 = plt.subplots(figsize=(5, 3.5))
        ax3.bar(saatlik.index, saatlik.values, color="#457b9d")
        ax3.set_xlabel("Saat")
        ax3.set_ylabel("Ort. Tüketim (MWh)")
        ax3.grid(True, alpha=0.3, axis="y")
        fig3.tight_layout()
        st.pyplot(fig3, use_container_width=True)
        st.caption("Gece dip, gündüz plato — günlük tüketim döngüsü.")

    with kol_b:
        st.markdown("**Sıcaklık vs Tüketim ilişkisi**")
        fig4, ax4 = plt.subplots(figsize=(5, 3.5))
        ax4.scatter(test_df["sicaklik"], test_df["tuketim_mwh"], alpha=0.15, s=5, color="#e63946")
        ax4.set_xlabel("Sıcaklık (°C)")
        ax4.set_ylabel("Tüketim (MWh)")
        ax4.grid(True, alpha=0.3)
        fig4.tight_layout()
        st.pyplot(fig4, use_container_width=True)
        st.caption("U şekli: hem soğukta (ısıtma) hem sıcakta (klima) tüketim artar.")

    st.markdown("---")
    st.markdown("**Haftanın günlerine göre ortalama tüketim**")
    gun_isimleri = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
    gunluk = test_df.groupby(test_df.index.dayofweek)["tuketim_mwh"].mean()
    fig5, ax5 = plt.subplots(figsize=(9, 3.5))
    ax5.bar([gun_isimleri[i] for i in gunluk.index], gunluk.values, color="#2a9d8f")
    ax5.set_ylabel("Ort. Tüketim (MWh)")
    ax5.grid(True, alpha=0.3, axis="y")
    fig5.tight_layout()
    st.pyplot(fig5, use_container_width=True)
    st.caption("Hafta sonu tüketimi hafta içine göre belirgin düşük.")

# ---------------------------------------------------------------------------
# Alt bilgi
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Veri: EPİAŞ Şeffaflık Platformu (tüketim) + Open-Meteo (sıcaklık). "
    "Model: LightGBM. | [GitHub](https://github.com/mustafaadalan/turkey-electricity-forecast)"
)