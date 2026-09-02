import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import base64

# 1. KONFIGURASI HALAMAN DAN STYLES
st.set_page_config(
    page_title="OEE Executive Analytics - PT. ARGAPURA",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .metric-card {
        background: linear-gradient(135deg, #1E2640 0%, #111827 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .metric-title { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; color: #9CA3AF; margin-bottom: 6px; }
    .metric-value { font-size: 2rem; font-weight: 700; color: #FFFFFF; margin-bottom: 4px; }
    .metric-badge { display: inline-block; font-size: 0.78rem; font-weight: 600; padding: 3px 8px; border-radius: 6px; }
    .badge-success { background-color: rgba(16, 185, 129, 0.15); color: #10B981; }
    .badge-danger { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; }
    .dashboard-header {
        background: linear-gradient(90deg, #1E1B4B 0%, #0F172A 100%);
        padding: 24px 28px;
        border-radius: 14px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .section-title { font-size: 1.2rem; font-weight: 600; color: #F3F4F6; margin: 15px 0; }
    .footer { text-align: center; font-size: 0.8rem; color: #6B7280; padding: 20px 0; border-top: 1px solid rgba(255, 255, 255, 0.05); margin-top: 40px; }
    </style>
""", unsafe_allow_html=True)

# File Penyimpanan Rekap Tahunan (Sangat Ringan)
SUMMARY_FILE = "oee_monthly_summary.csv"

# Inisialisasi Rekap 12 Bulan (Jan - Des)
def load_or_init_monthly_summary():
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if os.path.exists(SUMMARY_FILE):
        return pd.read_csv(SUMMARY_FILE)
    else:
        df_init = pd.DataFrame({"Bulan": months, "OEE_Aktual": [None]*12})
        df_init.to_csv(SUMMARY_FILE, index=False)
        return df_init

# STANDAR 3 FAKTOR & TARGET OEE SPESIFIK PER LINE
LINE_STANDARDS = {
    "BTP":        {"avail": 99.0, "perf": 98.0, "qual": 100.0, "oee": 96.74},
    "BTP MIX":    {"avail": 98.0, "perf": 99.0, "qual": 100.0, "oee": 96.74},
    "DFOAM 1":   {"avail": 98.0, "perf": 100.0, "qual": 100.0, "oee": 98.00},
    "DFOAM 2":   {"avail": 98.0, "perf": 100.0, "qual": 100.0, "oee": 98.00},
    "DFOAM 3":   {"avail": 98.0, "perf": 100.0, "qual": 100.0, "oee": 98.00},
    "DFOAM 4":   {"avail": 98.0, "perf": 100.0, "qual": 100.0, "oee": 98.00},
    "PP NOU":    {"avail": 80.0, "perf": 100.0, "qual": 100.0, "oee": 80.00},
    "PP PUNCH":  {"avail": 100.0, "perf": 98.0, "qual": 100.0, "oee": 97.83},
    "PP PUNCH 1":{"avail": 100.0, "perf": 98.0, "qual": 100.0, "oee": 97.83},
    "PVC 1":     {"avail": 93.0, "perf": 99.0, "qual": 99.95, "oee": 92.35},
    "PVC 2":     {"avail": 93.0, "perf": 99.0, "qual": 99.95, "oee": 92.35},
    "SMS 1":     {"avail": 93.0, "perf": 100.0, "qual": 100.0, "oee": 93.48},
    "SMS 2":     {"avail": 93.0, "perf": 100.0, "qual": 100.0, "oee": 93.48},
    "STF EXT 1": {"avail": 90.0, "perf": 100.0, "qual": 100.0, "oee": 90.00},
    "STF EXT 2": {"avail": 90.0, "perf": 100.0, "qual": 100.0, "oee": 90.00},
    "STF MIX":   {"avail": 92.0, "perf": 100.0, "qual": 100.0, "oee": 92.00},
}

DEFAULT_OVERALL_STD = {"avail": 90.0, "perf": 95.0, "qual": 99.0, "oee": 94.00}

# Header & Sidebar Logo
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    st.sidebar.markdown(f'<div style="background-color:#FFF;padding:10px;border-radius:12px;text-align:center;width:140px;margin:0 auto 20px auto;"><img src="data:image/png;base64,{img_b64}" style="width:100%;"></div>', unsafe_allow_html=True)

st.sidebar.markdown("<h3 style='color: #818CF8;'>Control Panel</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Unggah Data Excel OEE Bulanan", type=["xlsx", "xls"])

# Header Dashboard Utama
st.markdown("""
    <div class="dashboard-header">
        <div><h1>OEE Executive Analytics</h1><p>Monitoring Pencapaian Tren OEE Tahunan dan Performa Line Produksi</p></div>
        <div style="text-align:right;"><h3 style="color:#38BDF8;margin:0;">PT. ARGAPURA</h3><p style="color:#94A3B8;margin:0;">ESTABLISHED 1954</p></div>
    </div>
""", unsafe_allow_html=True)

df_summary = load_or_init_monthly_summary()

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='Data Daily')
        df['Tgl'] = pd.to_datetime(df['Tgl'], errors='coerce')
        df = df.dropna(subset=['Tgl']).sort_values(by='Tgl')
        df['OEE_pct'] = df['OEE'].apply(lambda x: x * 100 if x <= 1.0 else x)
        df['Avail_pct'] = df['Avail'].apply(lambda x: x * 100 if x <= 1.0 else x)
        df['Perf_pct'] = df['% Performance'].apply(lambda x: x * 100 if x <= 1.0 else x)
        df['Qual_pct'] = df['Quality'].apply(lambda x: x * 100 if x <= 1.0 else x)

        # Update Otomatis Nilai OEE Bulan Ini ke Summary Tahunan
        current_month_name = df['Tgl'].dt.strftime('%b').iloc[0]
        avg_monthly_all_lines = df['OEE_pct'].mean()
        
        df_summary.loc[df_summary['Bulan'] == current_month_name, 'OEE_Aktual'] = avg_monthly_all_lines
        df_summary.to_csv(SUMMARY_FILE, index=False)

        # ---------------------------------------------------------------------
        # BOARD TOP: EXECUTIVE SUMMARY (TREND OEE 1 TAHUN JAN - DES)
        # ---------------------------------------------------------------------
        st.markdown('<div class="section-title">A. Executive Summary — Tren Pencapaian OEE Tahunan (Jan - Des)</div>', unsafe_allow_html=True)
        
        fig_trend_year = go.Figure()

        # Warna Bar: Biru Terang jika Capai Target (>=94), Merah/Soft Blue jika Belum
        colors = ['#3B82F6' if (v is not None and v >= 94.0) else '#60A5FA' if v is not None else '#1F2937' for v in df_summary['OEE_Aktual']]

        fig_trend_year.add_trace(go.Bar(
            x=df_summary['Bulan'],
            y=df_summary['OEE_Aktual'],
            text=[f"{v:.1f}" if pd.notnull(v) else "" for v in df_summary['OEE_Aktual']],
            textposition='outside',
            marker_color=colors,
            name="Aktual OEE"
        ))

        # Target Line Fixed 94%
        fig_trend_year.add_hline(
            y=94.0, line_color="red", line_width=3,
            annotation_text="Target: 94%", annotation_position="top right",
            annotation_font=dict(color="red", size=12, family="Arial Black")
        )

        fig_trend_year.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#9CA3AF'),
            yaxis=dict(title="[%]", range=[70, 105]),
            xaxis=dict(title="Bulan Produksi"),
            height=350, showlegend=False
        )
        st.plotly_chart(fig_trend_year, use_container_width=True)

        st.markdown("---")

        # ---------------------------------------------------------------------
        # DETAIL BREAKDOWN BULANAN (FILTER LINE & HARI)
        # ---------------------------------------------------------------------
        df['Target_Line'] = df['LineID'].apply(lambda x: LINE_STANDARDS.get(x, DEFAULT_OVERALL_STD)['oee'])
        
        sorted_lines = sorted(list(df["LineID"].dropna().unique()))
        lines = ["Semua Line"] + sorted_lines
        selected_line = st.sidebar.selectbox("Pilih Production Line:", lines)
        
        df_filtered = df.copy() if selected_line == "Semua Line" else df[df["LineID"] == selected_line]
        active_std = DEFAULT_OVERALL_STD if selected_line == "Semua Line" else LINE_STANDARDS.get(selected_line, DEFAULT_OVERALL_STD)

        # Summary Cards
        avg_oee = df_filtered['OEE_pct'].mean()
        avg_avail = df_filtered['Avail_pct'].mean()
        avg_perf = df_filtered['Perf_pct'].mean()
        avg_qual = df_filtered['Qual_pct'].mean()

        diff_oee = avg_oee - active_std['oee']
        diff_avail = avg_avail - active_std['avail']
        diff_perf = avg_perf - active_std['perf']
        diff_qual = avg_qual - active_std['qual']

        def get_badge_html(diff, target_text):
            return f'<span class="metric-badge badge-success">+{diff:.2f}% vs {target_text}</span>' if diff >= 0 else f'<span class="metric-badge badge-danger">{diff:.2f}% vs {target_text}</span>'

        std_oee_txt = f"Std {active_std['oee']:.2f}%"
        std_avail_txt = f"Std {active_std['avail']:.1f}%"
        std_perf_txt = f"Std {active_std['perf']:.1f}%"
        std_qual_txt = f"Std {active_std['qual']:.2f}%"

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-title">Overall OEE</div><div class="metric-value">{avg_oee:.2f}%</div>{get_badge_html(diff_oee, std_oee_txt)}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-title">Availability</div><div class="metric-value">{avg_avail:.2f}%</div>{get_badge_html(diff_avail, std_avail_txt)}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-title">Performance</div><div class="metric-value">{avg_perf:.2f}%</div>{get_badge_html(diff_perf, std_perf_txt)}</div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-title">Quality Rate</div><div class="metric-value">{avg_qual:.2f}%</div>{get_badge_html(diff_qual, std_qual_txt)}</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {str(e)}")
else:
    # Tampilkan Chart Tren Tahunan Meskipun Belum Upload Data Baru
    st.markdown('<div class="section-title">A. Executive Summary — Tren Pencapaian OEE Tahunan (Jan - Des)</div>', unsafe_allow_html=True)
    fig_trend_year = go.Figure()
    fig_trend_year.add_trace(go.Bar(
        x=df_summary['Bulan'], y=df_summary['OEE_Aktual'],
        text=[f"{v:.1f}" if pd.notnull(v) else "" for v in df_summary['OEE_Aktual']],
        textposition='outside', marker_color='#3B82F6'
    ))
    fig_trend_year.add_hline(y=94.0, line_color="red", line_width=3, annotation_text="Target: 94%", annotation_position="top right")
    fig_trend_year.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#9CA3AF'), yaxis=dict(title="[%]", range=[70, 105]), height=350)
    st.plotly_chart(fig_trend_year, use_container_width=True)
    
    st.info("Silakan unggah file Excel data OEE harian di sidebar untuk memperbarui analisis bulan aktif.")

st.markdown('<div class="footer">copyright ardha_dyota - PT. ARGAPURA 2026</div>', unsafe_allow_html=True)
