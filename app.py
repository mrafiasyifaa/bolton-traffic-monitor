import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Bolton Traffic Forensics", layout="wide")

st.title("🚦 Bolton Traffic Risk Monitor")
st.markdown("""
**Dashboard Monitoring & Forensik Lalu Lintas Kota Bolton.**
Menggunakan *Unsupervised Machine Learning (K-Means)* untuk mendeteksi kegagalan struktural jalan.
""")

# 2. LOAD DATA
@st.cache_data
def load_data():
    # Pastikan file csv 'bolton_risk_data.csv' ada di folder yang sama
    df = pd.read_csv('bolton_risk_data.csv')
    return df

try:
    df = load_data()
except:
    st.error("File 'bolton_risk_data.csv' belum ditemukan! Silakan export dari Notebook dulu.")
    st.stop()

# ==========================================
# BAGIAN 1: GENERAL OVERVIEW (MACRO VIEW)
# ==========================================

st.sidebar.header("🔍 Filter Peta Umum")
pilihan_cluster = st.sidebar.multiselect(
    "Pilih Kategori Risiko:",
    options=df['risk_label'].unique(),
    default=df['risk_label'].unique()
)

# Filter data berdasarkan pilihan sidebar
df_filtered = df[df['risk_label'].isin(pilihan_cluster)]

# Metrik Utama
col1, col2, col3 = st.columns(3)
col1.metric("Total Sensor Terpantau", len(df_filtered))
col2.metric("Rata-rata Kecepatan", f"{df_filtered['avg_speed'].mean():.1f} km/h")
col3.metric("Titik Critical Bottleneck", len(df_filtered[df_filtered['speed_gap'] < -20]))

st.subheader("🗺️ Peta Sebaran Risiko (General Overview)")
st.markdown("Peta ini menunjukkan kondisi seluruh jaringan jalan berdasarkan hasil clustering.")

# Peta General (Bisa difilter)
fig_overview = px.scatter_map(
    df_filtered,
    lat="lat",
    lon="long",
    color="risk_label",
    size="avg_flow", 
    color_discrete_map={
        'HIGH RISK: Speeding Zone': 'red',
        'MEDIUM RISK: Unstable Flow': 'orange',
        'LOW RISK: Congestion/Slow': 'blue',
        'SAFE: Compliant & Stable': 'green'
    },
    zoom=11,
    height=500,
    hover_name="detid",
    hover_data=["fclass", "avg_speed", "limit", "speed_gap"]
)
fig_overview.update_layout(map_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_overview, use_container_width=True)

# ==========================================
# BAGIAN 2: FORENSIC INVESTIGATION (MICRO VIEW)
# ==========================================

st.markdown("---") # Garis pemisah
st.subheader("🕵️‍♂️ Studi Kasus: Investigasi Root Cause")
st.markdown("**Analisis Forensik pada Cluster 'Critical Bottleneck'**")

# Logika Investigasi (Hardcoded untuk N53311D)
root_cause_id = 'N53311D'
root_data = df[df['detid'] == root_cause_id]

if not root_data.empty:
    target_risk = root_data['risk_label'].iloc[0]
    
    # Ambil data investigasi (Root + Teman se-clusternya)
    # Kita pakai df asli (bukan df_filtered) agar temuan ini tetap muncul meski filter diubah
    df_investigasi = df[df['risk_label'] == target_risk].copy()
    
    # Bikin kolom Peran
    def assign_role(detid):
        if detid == root_cause_id:
            return "🔴 ROOT CAUSE (Sumber Masalah)"
        else:
            return "🟠 DOMINO EFFECT (Terdampak)"
    
    df_investigasi['Peran'] = df_investigasi['detid'].apply(assign_role)
    df_investigasi['size_marker'] = df_investigasi['Peran'].apply(lambda x: 30 if "ROOT" in x else 15)

    # Layout: Kiri Teks, Kanan Peta Zoom
    col_text, col_map = st.columns([1, 2])
    
    with col_text:
        st.error(f"### 🚨 Ditemukan Kegagalan Trunk Link")
        st.markdown(f"""
        **Lokasi:** Sensor **{root_cause_id}** (St. Peter's Way).
        
        **Fakta Data:**
        - **Limit:** {root_data['limit'].iloc[0]} km/h
        - **Kecepatan Aktual:** {root_data['avg_speed'].iloc[0]:.1f} km/h
        - **Flow:** {root_data['avg_flow'].iloc[0]:.0f} kendaraan/jam
        
        **Analisis:**
        Terjadi *Structural Bottleneck*. Jalan Trunk ini gagal mengalirkan arus, menyebabkan **{len(df_investigasi)-1} titik** jalan Primary di sekitarnya macet total (efek domino).
        """)
        
        st.info("💡 **Rekomendasi:** Terapkan Variable Speed Limit (VSL) di titik Merah.")

    with col_map:
        fig_investigasi = px.scatter_map(
            df_investigasi,
            lat="lat",
            lon="long",
            color="Peran",
            size="size_marker",
            color_discrete_map={
                "🔴 ROOT CAUSE (Sumber Masalah)": "red",
                "🟠 DOMINO EFFECT (Terdampak)": "orange"
            },
            zoom=13, # Zoom in otomatis
            center={"lat": root_data['lat'].iloc[0], "lon": root_data['long'].iloc[0]},
            height=450,
            title="Peta Forensik (Zoom View)",
            hover_name="detid",
            hover_data=["fclass", "avg_speed"]
        )
        fig_investigasi.update_layout(map_style="carto-positron", margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_investigasi, use_container_width=True)

else:
    st.warning("Data Forensik N53311D tidak ditemukan dalam dataset saat ini.")

# Footer
st.markdown("---")
st.caption("© 2024 Analisis Lalu Lintas Kota Bolton | Dibuat dengan Streamlit & Python")