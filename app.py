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

# 2. INISIALISASI DATABASE RINGAN REKAP BULANAN
SUMMARY_FILE = "oee_monthly_summary.csv"

def load_or_init_monthly_summary():
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if os.path.exists(SUMMARY_FILE):
        return pd.read_csv(SUMMARY_FILE)
    else:
        df_init = pd.DataFrame({"Bulan": months, "OEE_Aktual": [None]*12})
        df_init.to_csv(SUMMARY_FILE, index=False)
        return df_init

# 3. STANDAR 3 FAKTOR & TARGET OEE SPESIFIK PER LINE
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
else:
    st.sidebar.markdown("<h2 style='text-align: center; color: #38BDF8;'>PT. ARGAPURA</h2>", unsafe_allow_html=True)

st.sidebar.markdown("---")
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

        # Update Rekap Tahunan Otomatis
        current_month_name = df['Tgl'].dt.strftime('%b').iloc[0]
        avg_monthly_all_lines = df['OEE_pct'].mean()
        
        df_summary.loc[df_summary['Bulan'] == current_month_name, 'OEE_Aktual'] = avg_monthly_all_lines
        df_summary.to_csv(SUMMARY_FILE, index=False)

        # ---------------------------------------------------------------------
        # BOARD TOP: EXECUTIVE SUMMARY (TREND 1 TAHUN JAN - DES)
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
            x=df_summary['Bulan'],
            y=df_summary['OEE_Aktual'],
            text=[f"{v:.1f}%" if pd.notnull(v) else "" for v in df_summary['OEE_Aktual']],
            textposition='outside',
            marker_color=bar_colors,
            name="Aktual OEE"
        ))

        fig_trend_year.add_hline(
            y=94.0, line_color="#EF4444", line_width=3,
            annotation_text="Target: 94%", annotation_position="top right",
            annotation_font=dict(color="#EF4444", size=12, family="Arial Black")
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
        # METRIK & ANALYSIS BREAKDOWN BULAN AKTIF
        # ---------------------------------------------------------------------
        df['Target_Line'] = df['LineID'].apply(lambda x: LINE_STANDARDS.get(x, DEFAULT_OVERALL_STD)['oee'])
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("<h4 style='color: #E2E8F0;'>Filter Data</h4>", unsafe_allow_html=True)
        sorted_lines = sorted(list(df["LineID"].dropna().unique()))
        lines = ["Semua Line"] + sorted_lines
        selected_line = st.sidebar.selectbox("Pilih Production Line:", lines)
        
        df_filtered = df.copy() if selected_line == "Semua Line" else df[df["LineID"] == selected_line]
        active_std = DEFAULT_OVERALL_STD if selected_line == "Semua Line" else LINE_STANDARDS.get(selected_line, DEFAULT_OVERALL_STD)

        avg_oee = df_filtered['OEE_pct'].mean()
        avg_avail = df_filtered['Avail_pct'].mean()
        avg_perf = df_filtered['Perf_pct'].mean()
        avg_qual = df_filtered['Qual_pct'].mean()

        diff_oee = avg_oee - active_std['oee']
        diff_avail = avg_avail - active_std['avail']
        diff_perf = avg_perf - active_std['perf']
        diff_qual = avg_qual - active_std['qual']

        def get_badge_html(diff, target_text):
            if diff >= 0:
                return f'<span class="metric-badge badge-success">+{diff:.2f}% vs {target_text}</span>'
            return f'<span class="metric-badge badge-danger">{diff:.2f}% vs {target_text}</span>'

        std_oee_txt = f"Std {active_std['oee']:.2f}%"
        std_avail_txt = f"Std {active_std['avail']:.1f}%"
        std_perf_txt = f"Std {active_std['perf']:.1f}%"
        std_qual_txt = f"Std {active_std['qual']:.2f}%"

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-title">Overall OEE</div><div class="metric-value">{avg_oee:.2f}%</div>{get_badge_html(diff_oee, std_oee_txt)}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-title">Availability</div><div class="metric-value">{avg_avail:.2f}%</div>{get_badge_html(diff_avail, std_avail_txt)}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-title">Performance</div><div class="metric-value">{avg_perf:.2f}%</div>{get_badge_html(diff_perf, std_perf_txt)}</div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-title">Quality Rate</div><div class="metric-value">{avg_qual:.2f}%</div>{get_badge_html(diff_qual, std_qual_txt)}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # CHART BENCHMARK & LINE DI BAWAH TARGET
        col_left, col_right = st.columns([1, 1.2])

        with col_left:
            st.markdown('<div class="section-title">Benchmark Target vs Aktual</div>', unsafe_allow_html=True)
            df_overall_comp = pd.DataFrame({"Kategori": ["Target Line", "Aktual OEE"], "Nilai": [active_std['oee'], avg_oee]})
            fig_overall = px.bar(
                df_overall_comp, x="Kategori", y="Nilai", text="Nilai", color="Kategori",
                color_discrete_map={"Target Line": "#3B82F6", "Aktual OEE": "#10B981" if avg_oee >= active_std['oee'] else "#EF4444"}
            )
            fig_overall.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_overall.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#9CA3AF'), yaxis=dict(range=[0, 115]), showlegend=False, height=340)
            st.plotly_chart(fig_overall, use_container_width=True)

        with col_right:
            st.markdown('<div class="section-title">Daftar Line di Bawah Target Urut Gap</div>', unsafe_allow_html=True)
            if selected_line != "Semua Line":
                if avg_oee < active_std['oee']:
                    st.error(f"Line {selected_line} tidak mencapai target. Kekurangan: {(active_std['oee'] - avg_oee):.2f}%.")
                else:
                    st.success(f"Line {selected_line} berhasil memenuhi atau melampaui target yang ditentukan ({active_std['oee']:.2f}%).")
            else:
                line_summary = df.groupby("LineID").agg({'OEE_pct': 'mean', 'Target_Line': 'first', 'Avail_pct': 'mean', 'Perf_pct': 'mean', 'Qual_pct': 'mean'}).reset_index()
                problem_list = [{"Nama Line": row['LineID'], "Target": f"{row['Target_Line']:.2f}%", "Aktual OEE": f"{row['OEE_pct']:.2f}%", "Gap": row['Target_Line'] - row['OEE_pct'], "Kekurangan": f"-{(row['Target_Line'] - row['OEE_pct']):.2f}%", "Availability": f"{row['Avail_pct']:.1f}%", "Performance": f"{row['Perf_pct']:.1f}%", "Quality": f"{row['Qual_pct']:.1f}%"} for idx, row in line_summary.iterrows() if row['Target_Line'] - row['OEE_pct'] > 0]
                if problem_list:
                    df_problems = pd.DataFrame(problem_list).sort_values(by="Gap", ascending=False).drop(columns=["Gap"])
                    df_problems.index = range(1, len(df_problems) + 1)
                    st.dataframe(df_problems, height=270, use_container_width=True)
                else:
                    st.success("Luar biasa! Seluruh Line produksi berhasil mencapai target OEE spesifik.")

        st.markdown("---")

        # RATIO PENCAPAIAN PER LINE
        st.markdown('<div class="section-title">Ratio Pencapaian per Line [Ratio]</div>', unsafe_allow_html=True)
        df_line_ratio = df.groupby("LineID").agg({'Target_Line': 'first', 'OEE_pct': 'mean'}).reset_index()
        df_line_ratio['Target_Line'] = df_line_ratio['Target_Line'].replace(0, 1)
        df_line_ratio['Ratio'] = df_line_ratio['OEE_pct'] / df_line_ratio['Target_Line']
        df_line_ratio['Selisih_pct'] = df_line_ratio['OEE_pct'] - df_line_ratio['Target_Line']
        df_line_ratio = df_line_ratio.sort_values(by="Ratio", ascending=False)
        
        ratio_colors = ['#60A5FA' if r >= 1.0 else '#F87171' for r in df_line_ratio['Ratio']]
        
        fig_ratio = go.Figure()
        hover_texts = [
            f"<b>{line}</b><br>Target: {tgt:.2f}%<br>Aktual: {oee:.2f}%<br>Selisih: {sel:+.2f}%<br>Ratio: {r:.3f}"
            for line, tgt, oee, sel, r in zip(
                df_line_ratio['LineID'], df_line_ratio['Target_Line'], df_line_ratio['OEE_pct'], df_line_ratio['Selisih_pct'], df_line_ratio['Ratio']
            )
        ]

        fig_ratio.add_trace(go.Bar(
            x=df_line_ratio['LineID'], y=df_line_ratio['Ratio'], marker_color=ratio_colors,
            text=[f"{r:.3f}" for r in df_line_ratio['Ratio']], textposition='outside', hoverinfo='text', hovertext=hover_texts
        ))
        fig_ratio.add_shape(type="line", x0=-0.5, x1=len(df_line_ratio['LineID']) - 0.5, y0=1.0, y1=1.0, line=dict(color="#EF4444", width=3))
        fig_ratio.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#9CA3AF'), yaxis=dict(title="[Ratio]", range=[0, max(df_line_ratio['Ratio'].max() * 1.15, 1.3)]), xaxis=dict(title="", tickangle=-45), height=430, showlegend=False)
        st.plotly_chart(fig_ratio, use_container_width=True)

        st.markdown("---")

        # TREN HARIAN
        st.markdown(f'<div class="section-title">Tren Pergerakan OEE Harian Line {selected_line}</div>', unsafe_allow_html=True)
        df_daily = df_filtered.groupby("Tgl")["OEE_pct"].mean().reset_index()
        df_daily['Tgl_Str'] = df_daily['Tgl'].dt.strftime('%d %b %Y')

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=df_daily['Tgl_Str'], y=df_daily['OEE_pct'], mode='lines+markers',
            line=dict(color='#10B981', width=3), marker=dict(size=8, color='#34D399'),
            text=[f"{val:.1f}%" for val in df_daily['OEE_pct']], hoverinfo='x+text'
        ))
        fig_line.add_hline(y=active_std['oee'], line_dash="dash", line_color="#EF4444", line_width=2, annotation_text=f"Target Line ({active_std['oee']:.2f}%)", annotation_position="top right")
        fig_line.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#9CA3AF'), yaxis=dict(title="OEE (%)"), xaxis=dict(title="Tanggal Produksi", type='category', tickangle=-45), height=420, showlegend=False)
        st.plotly_chart(fig_line, use_container_width=True)

        # AI ANALYSIS ENGINE
        st.markdown('<div class="section-title">AI Executive Insights dan Diagnosis Performa</div>', unsafe_allow_html=True)
        factor_details = {
            "Availability": {"gap": active_std['avail'] - avg_avail, "actual": avg_avail, "target": active_std['avail'], "loss_type": "Downtime Losses Breakdown dan Setup", "action": "Percepat waktu pergantian cetakan SMED dan kurangi waktu mesin mati akibat kerusakan unplanned breakdown."},
            "Performance": {"gap": active_std['perf'] - avg_perf, "actual": avg_perf, "target": active_std['perf'], "loss_type": "Speed Losses dan Micro Stoppages", "action": "Analisis penyebab penurunan kecepatan operasional mesin, kurangi henti singkat minor stops, serta kalibrasi siklus standar."},
            "Quality": {"gap": active_std['qual'] - avg_qual, "actual": avg_qual, "target": active_std['qual'], "loss_type": "Defect Losses Reject dan Rework", "action": "Perketat inspeksi material awal, tingkatkan kendali proses visual, dan evaluasi ulang setelan standar produksi."}
        }

        sorted_factors = sorted(factor_details.items(), key=lambda item: item[1]["gap"], reverse=True)
        p1_name, p1_val = sorted_factors[0]
        p2_name, p2_val = sorted_factors[1]
        p3_name, p3_val = sorted_factors[2]

        if p1_val['gap'] > 0:
            header_status = f"Fokus Perbaiki {p1_name} Terlebih Dahulu!"
            desc_status = f"Indikator **{p1_name}** mengalami penyimpangan kerugian paling dominan dengan gap sebesar **{p1_val['gap']:.2f}%** di bawah standar (Aktual: {p1_val['actual']:.2f}% vs Standar Line: {p1_val['target']:.2f}%). Kerugian ini terutama dipicu oleh {p1_val['loss_type']}."
        else:
            header_status = "Seluruh Indikator Berada di Atas Standar!"
            desc_status = f"Luar biasa! Seluruh indikator (Availability, Performance, Quality) pada **{selected_line}** telah memenuhi atau melebihi standar operasional spesifik yang ditentukan."

        st.markdown(f"""
### Laporan Evaluasi AI: {selected_line}
Berdasarkan evaluasi tren data harian, pencapaian OEE berada pada tingkat **{avg_oee:.2f}%** (Target Line: **{active_std['oee']:.2f}%**).

---

#### Rekomendasi Utama: {header_status}
{desc_status}

#### Urutan Matriks Prioritas Perbaikan Roadmap:
1. **Prioritas 1 — {p1_name}** (Gap: {p1_val['gap']:+.2f}% | Aktual: {p1_val['actual']:.2f}% vs Standar Line: {p1_val['target']:.2f}%)  
   *Tindakan:* {p1_val['action']}
2. **Prioritas 2 — {p2_name}** (Gap: {p2_val['gap']:+.2f}% | Aktual: {p2_val['actual']:.2f}% vs Standar Line: {p2_val['target']:.2f}%)  
   *Tindakan:* {p2_val['action']}
3. **Prioritas 3 — {p3_name}** (Gap: {p3_val['gap']:+.2f}% | Aktual: {p3_val['actual']:.2f}% vs Standar Line: {p3_val['target']:.2f}%)  
   *Tindakan:* {p3_val['action']}
""")

        with st.expander("Lihat Mentah Data Excel Detail"):
            st.dataframe(df_filtered, use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {str(e)}")

else:
    # Tampilan Standby Jika Belum Upload File Bulanan
    st.markdown('<div class="section-title">A. Executive Summary — Pencapaian OEE Tahunan (Jan - Des)</div>', unsafe_allow_html=True)
    fig_trend_year = go.Figure()
    
    bar_colors = ['#3B82F6' if (v is not None and v >= 94.0) else '#F87171' if v is not None else '#1F2937' for v in df_summary['OEE_Aktual']]
    
    fig_trend_year.add_trace(go.Bar(
        x=df_summary['Bulan'], y=df_summary['OEE_Aktual'],
        text=[f"{v:.1f}%" if pd.notnull(v) else "" for v in df_summary['OEE_Aktual']],
        textposition='outside', marker_color=bar_colors
    ))
    fig_trend_year.add_hline(y=94.0, line_color="#EF4444", line_width=3, annotation_text="Target: 94%", annotation_position="top right")
    fig_trend_year.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#9CA3AF'), yaxis=dict(title="[%]", range=[70, 105]), height=350)
    st.plotly_chart(fig_trend_year, use_container_width=True)
    
    st.info("Silakan unggah file Excel data OEE harian di sidebar untuk menganalisis per line dan memperbarui tren bulanan.")

st.markdown('<div class="footer">copyright ardha_dyota - PT. ARGAPURA 2026</div>', unsafe_allow_html=True)
