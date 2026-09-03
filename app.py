import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import base64
import re

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
    
    /* STYLE UNTUK BADGE ALERT HEALTH STATUS (POIN 4) */
    .status-alert-box {
        padding: 15px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .alert-critical { background-color: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; color: #FCA5A5; }
    .alert-warning { background-color: rgba(245, 158, 11, 0.15); border: 1px solid #F59E0B; color: #FCD34D; }
    .alert-ok { background-color: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; color: #6EE7B7; }
    </style>
""", unsafe_allow_html=True)

# 2. DATABASE REKAP TAHUNAN OTOMATIS
SUMMARY_FILE = "oee_monthly_summary.csv"

def load_or_init_monthly_summary():
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if os.path.exists(SUMMARY_FILE):
        return pd.read_csv(SUMMARY_FILE)
    else:
        df_init = pd.DataFrame({"Bulan": months, "OEE_Aktual": [None]*12})
        df_init.to_csv(SUMMARY_FILE, index=False)
        return df_init

# 3. KAMUS TARGET SPESIFIK LINE
LINE_STANDARDS = {
    "BTP":        {"avail": 99.0, "perf": 98.0, "qual": 100.00, "oee": 96.74},
    "BTP MIX":    {"avail": 98.0, "perf": 99.0, "qual": 100.00, "oee": 96.74},
    "DFOAM 1":   {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "DFOAM 2":   {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "DFOAM 3":   {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "DFOAM 4":   {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "PP NOU":    {"avail": 80.0, "perf": 100.0, "qual": 100.00, "oee": 80.00},
    "PP PUNCH":  {"avail": 100.0, "perf": 98.0, "qual": 100.00, "oee": 97.83},
    "PP PUNCH 1":{"avail": 100.0, "perf": 98.0, "qual": 100.00, "oee": 97.83},
    "PVC 1":     {"avail": 93.0, "perf": 99.0, "qual": 99.95, "oee": 92.35},
    "PVC 2":     {"avail": 93.0, "perf": 99.0, "qual": 99.95, "oee": 92.35},
    "SMS 1":     {"avail": 93.0, "perf": 100.0, "qual": 100.00, "oee": 93.48},
    "SMS 2":     {"avail": 93.0, "perf": 100.0, "qual": 100.00, "oee": 93.48},
    "STF EXT 1": {"avail": 90.0, "perf": 100.0, "qual": 100.00, "oee": 90.00},
    "STF EXT 2": {"avail": 90.0, "perf": 100.0, "qual": 100.00, "oee": 90.00},
    "STF MIX":   {"avail": 92.0, "perf": 100.0, "qual": 100.00, "oee": 92.00},
}

DEFAULT_OVERALL_STD = {"avail": 90.0, "perf": 95.0, "qual": 99.0, "oee": 94.00}

# FUNGSI PENCOCOKAN NAMA LINE CERDAS
def get_target_by_line(line_name):
    if not isinstance(line_name, str):
        return DEFAULT_OVERALL_STD
    clean_name = line_name.upper().strip()
    if clean_name in LINE_STANDARDS:
        return LINE_STANDARDS[clean_name]
    cleaned = re.sub(r'\bSHIFT\s*\d+\b', '', clean_name)
    cleaned = cleaned.replace("EXTRUDING", "EXT").strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    if cleaned in LINE_STANDARDS:
        return LINE_STANDARDS[cleaned]
    for key in LINE_STANDARDS:
        if key in clean_name or clean_name in key:
            return LINE_STANDARDS[key]
    return DEFAULT_OVERALL_STD

# Header & Sidebar Logo
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    st.sidebar.markdown(f'<div style="background-color:#FFF;padding:10px;border-radius:12px;text-align:center;width:140px;margin:0 auto 20px auto;"><img src="data:image/png;base64,{img_b64}" style="width:100%;"></div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown("<h2 style='text-align: center; color: #38BDF8;'>PT. ARGAPURA</h2>", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color: #818CF8;'>Control Panel</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Unggah Data Excel OEE Bulanan", type=["xlsx", "xls"])

# Header Dashboard Utama
st.markdown("""
    <div class="dashboard-header">
        <div><h1>OEE Executive Analytics & Control</h1><p>System Control & Improvement Execution Platform</p></div>
        <div style="text-align:right;"><h3 style="color:#38BDF8;margin:0;">PT. ARGAPURA</h3><p style="color:#94A3B8;margin:0;">ESTABLISHED 1954</p></div>
    </div>
""", unsafe_allow_html=True)

df_summary = load_or_init_monthly_summary()

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='Data Daily')
        
        required_cols = ['Tgl', 'LineID', 'OEE', 'Avail', '% Performance', 'Quality']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Format Excel Tidak Sesuai! Kolom berikut tidak ditemukan: {', '.join(missing_cols)}")
            st.stop()

        df['Tgl'] = pd.to_datetime(df['Tgl'], errors='coerce')
        df = df.dropna(subset=['Tgl']).sort_values(by='Tgl')
        df['OEE_pct'] = df['OEE'].apply(lambda x: x * 100 if x <= 1.0 else x)
        df['Avail_pct'] = df['Avail'].apply(lambda x: x * 100 if x <= 1.0 else x)
        df['Perf_pct'] = df['% Performance'].apply(lambda x: x * 100 if x <= 1.0 else x)
        df['Qual_pct'] = df['Quality'].apply(lambda x: x * 100 if x <= 1.0 else x)

        # Hitung Minggu ke-N untuk Time Filter
        df['Minggu'] = "Minggu " + df['Tgl'].dt.isocalendar().week.astype(str)

        current_month_name = df['Tgl'].dt.strftime('%b').iloc[0]
        avg_monthly_all_lines = df['OEE_pct'].mean()
        
        df_summary.loc[df_summary['Bulan'] == current_month_name, 'OEE_Aktual'] = avg_monthly_all_lines
        df_summary.to_csv(SUMMARY_FILE, index=False)

        # ---------------------------------------------------------------------
        # POIN 5: DYNAMIC TIME FILTER & LINE FILTER IN SIDEBAR
        # ---------------------------------------------------------------------
        st.sidebar.markdown("---")
        st.sidebar.markdown("<h4 style='color: #E2E8F0;'>Filter Control</h4>", unsafe_allow_html=True)
        
        sorted_lines = sorted(list(df["LineID"].dropna().unique()))
        lines = ["Semua Line"] + sorted_lines
        selected_line = st.sidebar.selectbox("Pilih Production Line:", lines)

        # Filter Periode Waktu Dinamis
        time_mode = st.sidebar.radio("Rentang Waktu:", ["Satu Bulan Full", "Filter Mingguan", "Custom Date Range"])
        
        df_filtered = df.copy()
        if selected_line != "Semua Line":
            df_filtered = df_filtered[df_filtered["LineID"] == selected_line]

        if time_mode == "Filter Mingguan":
            available_weeks = sorted(list(df['Minggu'].unique()))
            selected_week = st.sidebar.selectbox("Pilih Minggu:", available_weeks)
            df_filtered = df_filtered[df_filtered['Minggu'] == selected_week]
        elif time_mode == "Custom Date Range":
            min_date = df['Tgl'].min().date()
            max_date = df['Tgl'].max().date()
            date_range = st.sidebar.date_input("Pilih Rentang Tanggal:", [min_date, max_date], min_value=min_date, max_value=max_date)
            if len(date_range) == 2:
                df_filtered = df_filtered[(df_filtered['Tgl'].dt.date >= date_range[0]) & (df_filtered['Tgl'].dt.date <= date_range[1])]

        # Target Active Standard
        active_std = DEFAULT_OVERALL_STD if selected_line == "Semua Line" else get_target_by_line(selected_line)

        # ---------------------------------------------------------------------
        # BOARD TOP: EXECUTIVE SUMMARY TAHUNAN
        # ---------------------------------------------------------------------
        st.markdown('<div class="section-title">A. Executive Summary — Pencapaian OEE Tahunan (Jan - Des)</div>', unsafe_allow_html=True)
        
        fig_trend_year = go.Figure()
        bar_colors = []
        for v in df_summary['OEE_Aktual']:
            if pd.notnull(v):
                bar_colors.append('#3B82F6' if v >= 94.0 else '#F87171')
            else:
                bar_colors.append('#1F2937')

        fig_trend_year.add_trace(go.Bar(
            x=df_summary['Bulan'], y=df_summary['OEE_Aktual'],
            text=[f"{v:.1f}%" if pd.notnull(v) else "" for v in df_summary['OEE_Aktual']],
            textposition='outside', marker_color=bar_colors, name="Aktual OEE"
        ))

        fig_trend_year.add_hline(
            y=94.0, line_color="#EF4444", line_width=3,
            annotation_text="Target: 94%", annotation_position="top right",
            annotation_font=dict(color="#EF4444", size=12, family="Arial Black")
        )

        fig_trend_year.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#9CA3AF'), yaxis=dict(title="[%]", range=[70, 105]),
            xaxis=dict(title="Bulan Produksi"), height=320, showlegend=False
        )
        st.plotly_chart(fig_trend_year, use_container_width=True)

        st.markdown("---")

        # ---------------------------------------------------------------------
        # POIN 4: MANAGEMENT ALERT & HEALTH STATUS BADGE
        # ---------------------------------------------------------------------
        avg_oee = df_filtered['OEE_pct'].mean()
        avg_avail = df_filtered['Avail_pct'].mean()
        avg_perf = df_filtered['Perf_pct'].mean()
        avg_qual = df_filtered['Qual_pct'].mean()

        gap_oee = avg_oee - active_std['oee']

        # Kategori Status Kesehatan
        if gap_oee < -3.0:
            status_class = "alert-critical"
            status_label = "🔴 CRITICAL ALERT: OEE Sangat Di Bawah Target!"
            action_req = "Eskalasi Segera ke Manajer Produksi & Engineering untuk Intervensi Darurat."
        elif gap_oee < 0:
            status_class = "alert-warning"
            status_label = "🟡 WARNING: OEE Belum Mencapai Target Spesifik"
            action_req = "Dibutuhkan Perhatian Supervisor & Review Action Plan Harian."
        else:
            status_class = "alert-ok"
            status_label = "🟢 ON TRACK: Performa Line Memenuhi Target"
            action_req = "Pertahankan Ritme Operasional & Jalankan Preventive Maintenance Standar."

        st.markdown(f"""
        <div class="status-alert-box {status_class}">
            <div>
                <h4 style="margin:0; font-size: 1.1rem;">{status_label}</h4>
                <p style="margin: 4px 0 0 0; font-size: 0.9rem;"><strong>Mandat Manajemen:</strong> {action_req}</p>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 1.4rem; font-weight: bold;">{avg_oee:.2f}%</span> / Target: {active_std['oee']:.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # METRIK TAMPILAN KPI
        # ---------------------------------------------------------------------
        diff_oee = avg_oee - active_std['oee']
        diff_avail = avg_avail - active_std['avail']
        diff_perf = avg_perf - active_std['perf']
        diff_qual = avg_qual - active_std['qual']

        def get_badge_html(diff, target_text):
            if diff >= 0:
                return f'<span class="metric-badge badge-success">+{diff:.2f}% vs {target_text}</span>'
            return f'<span class="metric-badge badge-danger">{diff:.2f}% vs {target_text}</span>'

        std_oee_txt = f"Target {active_std['oee']:.2f}%"
        std_avail_txt = f"Target {active_std['avail']:.1f}%"
        std_perf_txt = f"Target {active_std['perf']:.1f}%"
        std_qual_txt = f"Target {active_std['qual']:.2f}%"

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-title">Overall OEE</div><div class="metric-value">{avg_oee:.2f}%</div>{get_badge_html(diff_oee, std_oee_txt)}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-title">Availability</div><div class="metric-value">{avg_avail:.2f}%</div>{get_badge_html(diff_avail, std_avail_txt)}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-title">Performance</div><div class="metric-value">{avg_perf:.2f}%</div>{get_badge_html(diff_perf, std_perf_txt)}</div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-title">Quality Rate</div><div class="metric-value">{avg_qual:.2f}%</div>{get_badge_html(diff_qual, std_qual_txt)}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # STRATEGI MANAJEMEN & PARETO PROBLEM
        # ---------------------------------------------------------------------
        st.markdown('<div class="section-title">Peta Strategi Manajemen (KPI Alignment)</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background-color: #1E2640; border-left: 4px solid #3B82F6; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="color: #60A5FA; margin-top: 0;">🎯 Alignment Strategi Pencapaian Target OEE</h4>
            <p style="margin-bottom: 8px;"><strong>1. Main KPI (Perusahaan):</strong> Mencapai Overall OEE Minimum <strong>94.00%</strong>.</p>
            <p style="margin-bottom: 8px;"><strong>2. Sub KPI (Lini Produksi):</strong> Memastikan seluruh Production Line mencapai target OEE spesifik masing-masing.</p>
            <p style="margin-bottom: 0;"><strong>3. Proses KPI (Operasional Harian):</strong> Menjaga 3 faktor utama (Availability, Performance, Quality Rate) agar tidak mengalami defisit dari standar line.</p>
        </div>
        """, unsafe_allow_html=True)

        # AI PARETO & SPESIFIK TEMA IMPROVEMENT
        st.markdown('<div class="section-title">AI Pareto Recommendation & Specific Improvement Theme</div>', unsafe_allow_html=True)
        
        factor_details = {
            "Availability": {
                "defisit": active_std['avail'] - avg_avail, 
                "actual": avg_avail, 
                "target": active_std['avail'], 
                "loss_category": "Breakdown & Setup Losses (Downtime)",
                "theme_template": "Penerapan Autonomous Maintenance & Reduksi Breakdown pada Engine / Mold Line",
                "action_steps": [
                    "Lakukan analisis Root Cause (5-Why Analysis) pada penyebab utama unplanned breakdown.",
                    "Terapkan metode SMED (Single-Minute Exchange of Die) untuk memotong waktu pergantian cetakan.",
                    "Buat Standard Operating Procedure (SOP) pelumasan & inspeksi harian oleh operator."
                ]
            },
            "Performance": {
                "defisit": active_std['perf'] - avg_perf, 
                "actual": avg_perf, 
                "target": active_std['perf'], 
                "loss_category": "Speed Loss & Micro Stoppages (Minor Stops)",
                "theme_template": "Eliminasi Speed Loss & Penyetelan Standar Parameter Kecepatan Mesin",
                "action_steps": [
                    "Identifikasi titik bottle-neck atau gesekan mekanis yang menyebabkan mesin diturunkan kecepatannya.",
                    "Lakukan pembersihan dan pencatatan riwayat minor stops (>5 detik hingga 5 menit).",
                    "Kunci (*lock*) parameter kecepatan ideal pada layar control panel agar tidak diubah tanpa otorisasi."
                ]
            },
            "Quality": {
                "defisit": active_std['qual'] - avg_qual, 
                "actual": avg_qual, 
                "target": active_std['qual'], 
                "loss_category": "Defect & Scrap Losses (Reject Rate)",
                "theme_template": "Peningkatan Quality Rate Melalui Kontrol Parameter Input Material & Mold Setup",
                "action_steps": [
                    "Tingkatkan standar penerimaan inspeksi bahan baku sebelum masuk ke saluran feeder.",
                    "Lakukan kalibrasi ulang pada temperatur dan tekanan proses secara berkala.",
                    "Terapkan mekanisme Poka-Yoke (sistem anti-salah) pada stasiun kerja utama."
                ]
            }
        }

        problem_factors = [(name, data) for name, data in factor_details.items() if data["defisit"] > 0.001]
        problem_factors.sort(key=lambda x: x[1]["defisit"], reverse=True)

        if problem_factors:
            top_problem_name, top_problem_data = problem_factors[0]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #2D1522 0%, #111827 100%); border: 1px solid #EF4444; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="color: #F87171; margin-top:0;">🔥 PARETO PROBLEM UTAMA: {top_problem_name.upper()}</h3>
                <p style="font-size: 1.05rem; color: #F3F4F6;">
                    Faktor <strong>{top_problem_name}</strong> memberikan dampak penurunan OEE terbesar pada <strong>{selected_line}</strong> dengan defisit sebesar <strong style="color:#F87171;">-{top_problem_data['defisit']:.2f}%</strong> (Aktual: {top_problem_data['actual']:.2f}% vs Target: {top_problem_data['target']:.2f}%).
                </p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <h4 style="color: #38BDF8; margin-bottom: 8px;">💡 REKOMENDASI TEMA IMPROVEMENT SPESIFIK (QCC / KAIZEN):</h4>
                <p style="font-size: 1.2rem; font-weight: bold; color: #FACC15;">
                    "<u>{top_problem_data['theme_template']} pada {selected_line}</u>"
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 📌 Langkah-Langkah Eksekusi Improvement (Action Plan):")
            for i, step in enumerate(top_problem_data['action_steps'], start=1):
                st.markdown(f"**{i}.** {step}")
        else:
            st.success(f"🎉 **Tidak Ada Pareto Problem!** Seluruh faktor OEE pada **{selected_line}** sudah memenuhi atau melebihi target spesifik.")

        with st.expander("Lihat Data Excel Mentah Detail"):
            st.dataframe(df_filtered, use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {str(e)}")

else:
    st.info("Silakan unggah file Excel data OEE harian di sidebar untuk membuka dashboard analytics.")

st.markdown('<div class="footer">copyright ardha_dyota - PT. ARGAPURA 2026</div>', unsafe_allow_html=True)
