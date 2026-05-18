import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Konfigurasi halaman dashboard
st.set_page_config(page_title="Dashboard Prospek Zakat Sukses & Sahabat Berbagi", layout="wide")

st.title("📊 Dashboard Manajemen Prospek")
st.markdown("Dashboard terintegrasi untuk memantau data prospek dari CRM Zakat Sukses dan Sahabat Berbagi.")

# ==========================================
# 1. URL DATA DARI GOOGLE SHEETS (sudah di-publish sebagai CSV)
# ==========================================
URL_CRM = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRByEPfHBgayEt6jScTScQiRj2btiQyxPscPWReBfsjP3CaklIqey8B1gVolV_zwsbgg0HxNaZfDP1S/pub?output=csv"
URL_SAHABAT = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQWsTWy5bw_4srWlE85bSBaMY5coGcVS58nXyGVzlgNeuY82JrRr2u2pbnACbxcjg/pub?output=csv"

# ==========================================
# 2. FUNGSI LOAD DATA DENGAN CACHING
# ==========================================
@st.cache_data
def load_data_crm():
    """Memuat dan membersihkan data dari Google Sheets CRM Zakat Sukses."""
    try:
        df = pd.read_csv(URL_CRM)
        # Bersihkan kolom nominal (karena ada "Rp" dan titik)
        df['nominal_bersih'] = (
            df['nominal']
            .astype(str)
            .str.replace('Rp', '')
            .str.replace('.', '')
            .str.replace(',', '')
            .str.extract(r'(\d+)')
            .fillna(0)
            .astype(int)
        )
        # Tambahkan kolom sumber
        df['sumber'] = 'CRM Zakat Sukses'
        return df
    except Exception as e:
        st.error(f"Gagal memuat data CRM: {e}")
        return pd.DataFrame()

@st.cache_data
def load_data_sahabat():
    """Memuat dan membersihkan data dari Google Sheets Sahabat Berbagi."""
    try:
        df = pd.read_csv(URL_SAHABAT)
        # Coba bersihkan kolom nominal jika ada
        if 'nominal' in df.columns:
            df['nominal_bersih'] = (
                df['nominal']
                .astype(str)
                .str.replace('Rp', '')
                .str.replace('.', '')
                .str.replace(',', '')
                .str.extract(r'(\d+)')
                .fillna(0)
                .astype(int)
            )
        else:
            df['nominal_bersih'] = 0
        df['sumber'] = 'Sahabat Berbagi'
        return df
    except Exception as e:
        st.warning(f"Data Sahabat Berbagi belum bisa dimuat: {e}")
        return pd.DataFrame()

# ==========================================
# 3. MEMUAT DATA
# ==========================================
df_crm = load_data_crm()
df_sahabat = load_data_sahabat()

# ==========================================
# 4. SIDEBAR: PILIH SUMBER DATA
# ==========================================
with st.sidebar:
    st.header("⚙️ Navigasi")
    sumber_terpilih = st.radio(
        "Pilih Sumber Data Prospek:",
        options=["CRM Zakat Sukses", "Sahabat Berbagi"],
        captions=["Data dari Tim CRM", "Data dari Tim Digital Sahabat Berbagi"]
    )

# Tentukan dataframe aktif
if sumber_terpilih == "CRM Zakat Sukses":
    df = df_crm
    if df.empty:
        st.error("Data CRM Zakat Sukses kosong. Periksa koneksi atau URL.")
        st.stop()
else:
    df = df_sahabat
    if df.empty:
        st.info("Data Sahabat Berbagi belum tersedia. Pastikan URL benar dan file CSV dapat diakses.")
        st.stop()

# ==========================================
# 5. TAMPILAN DASHBOARD
# ==========================================
st.header(f"📊 Data Prospek: {sumber_terpilih}")

# Filter di sidebar (khusus untuk CRM)
if sumber_terpilih == "CRM Zakat Sukses":
    with st.sidebar:
        st.subheader("🔍 Filter Data")
        if 'Prioritas' in df.columns:
            prioritas_list = df['Prioritas'].dropna().unique().tolist()
            if prioritas_list:
                pilih_prioritas = st.multiselect("Prioritas", prioritas_list, default=prioritas_list)
                df = df[df['Prioritas'].isin(pilih_prioritas)]
        if 'Status Resume' in df.columns:
            status_list = df['Status Resume'].dropna().unique().tolist()
            if status_list:
                pilih_status = st.multiselect("Status Resume", status_list, default=status_list)
                df = df[df['Status Resume'].isin(pilih_status)]

# Metrik Utama
col1, col2, col3 = st.columns(3)
total_nominal = df['nominal_bersih'].sum() if 'nominal_bersih' in df.columns else 0
total_prospek = len(df)
rata_nominal = total_nominal / total_prospek if total_prospek > 0 else 0

col1.metric("Total Prospek", f"{total_prospek:,}")
col2.metric("Total Nominal", f"Rp {total_nominal:,.0f}")
col3.metric("Rata-rata Nominal", f"Rp {rata_nominal:,.0f}")

# Visualisasi (khusus untuk CRM karena punya kolom program)
if sumber_terpilih == "CRM Zakat Sukses" and 'program' in df.columns:
    st.subheader("🏷️ Top 10 Program Berdasarkan Total Nominal")
    prog_sum = df.groupby('program')['nominal_bersih'].sum().sort_values(ascending=False).head(10)
    if not prog_sum.empty:
        fig = px.bar(x=prog_sum.values, y=prog_sum.index, orientation='h',
                     title="Total Nominal per Program",
                     labels={'x': 'Total Nominal (Rp)', 'y': 'Program'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📌 Status Prospek")
    if 'Status Donatur Prospek' in df.columns:
        status_counts = df['Status Donatur Prospek'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Jumlah']
        if not status_counts.empty:
            fig_status = px.pie(status_counts, values='Jumlah', names='Status', title="Distribusi Status Prospek")
            st.plotly_chart(fig_status, use_container_width=True)

# Tabel Preview Data
st.subheader("📋 Preview Data")
kolom_tampil = [
    kol for kol in ['donatur', 'program', 'nominal', 'Prioritas', 'Status Donatur Prospek', 'channel']
    if kol in df.columns
]
if kolom_tampil:
    st.dataframe(df[kolom_tampil].head(100), use_container_width=True)
else:
    st.dataframe(df.head(100), use_container_width=True)

# Tombol Download
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Download Data (CSV)",
    data=csv,
    file_name=f"data_{sumber_terpilih.replace(' ', '_')}.csv",
    mime="text/csv"
)