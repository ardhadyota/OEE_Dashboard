import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import base64

# 1. KONFIGURASI HALAMAN DAN CUSTOM CSS
st.set_page_config(
    page_title="OEE Executive Analytics - PT. ARGAPURA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk Dashboard
st.markdown("""
    <style>
    /* Styling utama area dashboard */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* Custom Card Metric */
    .metric-card {
        background: linear-gradient(135deg, #1E2640 0%, #111827 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #9CA3AF;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 4px;
    }
    .metric-badge {
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .badge-success { background-color: rgba(16, 185, 129, 0.15); color: #10B981; }
    .badge-danger { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; }
    
    /* Header Container */
    .dashboard-header {
        background: linear-gradient(90deg, #1E1B4B 0%, #0F172A 100%);
        padding: 24px 28px;
        border-radius: 14px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
    }
    .dashboard-header-left h1 {
        color: #FFFFFF;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }
    .dashboard-header-left p {
        color: #94A3B8;
        margin: 4px 0 0 0;
        font-size: 0.95rem;
    }
    .dashboard-header-right {
        text-align: right;
        border-left: 2px solid rgba(255, 255, 255, 0.1);
        padding-left: 20px;
    }
    .dashboard-header-right h3 {
        color: #38BDF8;
        margin: 0;
        font-weight: 800;
        letter-spacing: 1px;
    }
    .dashboard-header-right p {
        color: #94A3B8;
        margin: 0;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 2px;
    }

    /* Section Header */
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #F3F4F6;
        margin-top: 15px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Footer Styling */
    .footer {
        text-align: center;
        font-size: 0.8rem;
        color: #6B7280;
        padding: 20px 0 10px 0;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 40px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. DEFINISI TARGET SPESIFIK LINE
DEFAULT_TARGETS = {
    "BTP MIXING": 95.0,
    "BUTYL TAPE LINE 1": 92.0,
    "BUTYL TAPE LINE 2": 94.0,
    "BUTYL TAPE LINE 3": 90.0,
    "BUTYL TAPE LINE 5": 93.0,
    "OROTEX 5001-ID": 96.0,
    "PAD PILLAR NOUTONG": 91.0,
    "PEREDAM-REPACKING": 95.0,
    "PVC LINE MC 1": 94.0,
    "PVC LINE MC 2": 94.0,
    "STF EXTRUDING SHIFT 1": 95.0,
    "STF EXTRUDING SHIFT 2": 93.0,
    "STF MIXING": 96.0,
    "STF PUNCHING 1": 92.0,
    "STF PUNCHING 2": 90.0,
    "STF PUNCHING 3": 90.0
}

TARGET_OVERALL_DEFAULT = 94.0

# Logo Sidebar
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    st.sidebar.markdown(f"""
        <div style="
            background-color: #FFFFFF;
            padding: 10px;
            border-radius: 12px;
            text-align: center;
            width: 140px;
            margin: 10px auto 20px auto;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        ">
            <img src="data:image/png;base64,{img_b64}" style="width: 100%; height: auto; display: block;">
        </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("<h2 style='text-align: center; color: #38BDF8;'>PT. ARGAPURA</h2>", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color: #818CF8;'>Control Panel</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Unggah Data Excel OEE", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='Data Daily')
        
        # Transformasi Data
        df['Tgl'] = pd.to_datetime(df['Tgl'])
        df = df.sort_values(by='Tgl')

        df['OEE_pct'] = df['OEE'] * 100 if df['OEE'].max() <= 1.0 else df['OEE']
        df['Avail_pct'] = df['Avail']
        df['Perf_pct'] = df['% Performance'] * 100 if df['% Performance'].max() <= 1.0 else df['% Performance']
        df['Qual_pct'] = df['Quality'] * 100 if df['Quality'].max() <= 1.0 else df['Quality']
        df['Target_Line'] = df['LineID'].map(DEFAULT_TARGETS).fillna(TARGET_OVERALL_DEFAULT)

        # Filters
        st.sidebar.markdown("---")
        st.sidebar.markdown("<h4 style='color: #E2E8F0;'>Filter Data</h4>", unsafe_allow_html=True)
        min_date, max_date = df['Tgl'].min().date(), df['Tgl'].max().date()
        selected_date_range = st.sidebar.date_input(
            "Rentang Tanggal Production:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
            start_date, end_date = selected_date_range
            df = df[(df['Tgl'].dt.date >= start_date) & (df['Tgl'].dt.date <= end_date)]

        sorted_lines = sorted(list(df["LineID"].dropna().unique()))
        lines = ["Semua Line"] + sorted_lines
        selected_line = st.sidebar.selectbox("Pilih Production Line:", lines)
        
        df_filtered = df.copy() if selected_line == "Semua Line" else df[df["LineID"] == selected_line]
        active_target = TARGET_OVERALL_DEFAULT if selected_line == "Semua Line" else DEFAULT_TARGETS.get(selected_line, TARGET_OVERALL_DEFAULT)
        overall_avg_oee = df['OEE_pct'].mean()

        # 3. HEADER DAN SUMMARY METRICS
        st.markdown("""
            <div class="dashboard-header">
                <div class="dashboard-header-left">
                    <h1>OEE Analytics & Performance Dashboard</h1>
                    <p>Monitoring Efisiensi Mesin, Analisis Gap Target, dan Evaluasi Indikator Produksi</p>
                </div>
                <div class="dashboard-header-right">
                    <h3>PT. ARGAPURA</h3>
                    <p>ESTABLISHED 1954</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        avg_oee = df_filtered['OEE_pct'].mean()
        avg_avail = df_filtered['Avail_pct'].mean()
        avg_perf = df_filtered['Perf_pct'].mean()
        avg_qual = df_filtered['Qual_pct'].mean()

        STD_AVAIL, STD_PERF, STD_QUAL = 90.0, 95.0, 99.0
        diff_oee = avg_oee - active_target
        diff_avail = avg_avail - STD_AVAIL
        diff_perf = avg_perf - STD_PERF
        diff_qual = avg_qual - STD_QUAL

        def get_badge_html(diff, target_text):
            if diff >= 0:
                return f'<span class="metric-badge badge-success">+{diff:.2f}% vs {target_text}</span>'
            return f'<span class="metric-badge badge-danger">{diff:.2f}% vs {target_text}</span>'

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-title">Overall OEE</div><div class="metric-value">{avg_oee:.2f}%</div>{get_badge_html(diff_oee, f"Target {active_target:.1f}%")}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-title">Availability</div><div class="metric-value">{avg_avail:.2f}%</div>{get_badge_html(diff_avail, "Std 90%")}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-title">Performance</div><div class="metric-value">{avg_perf:.2f}%</div>{get_badge_html(diff_perf, "Std 95%")}</div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-title">Quality Rate</div><div class="metric-value">{avg_qual:.2f}%</div>{get_badge_html(diff_qual, "Std 99%")}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 4. CHART SECTION 1
        col_left, col_right = st.columns([1, 1.2])

        with col_left:
            st.markdown('<div class="section-title">Benchmark Overall Target vs Aktual</div>', unsafe_allow_html=True)
            df_overall_comp = pd.DataFrame({"Kategori": ["Target Rata-Rata", "Aktual OEE"], "Nilai": [TARGET_OVERALL_DEFAULT, overall_avg_oee]})
            fig_overall = px.bar(
                df_overall_comp, x="Kategori", y="Nilai", text="Nilai", color="Kategori",
                color_discrete_map={"Target Rata-Rata": "#3B82F6", "Aktual OEE": "#10B981" if overall_avg_oee >= TARGET_OVERALL_DEFAULT else "#EF4444"}
            )
            fig_overall.update_traces(texttemplate='%{text:.2f}%', textposition='outside', marker_line_width=0)
            fig_overall.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#9CA3AF'), yaxis=dict(range=[0, 115], gridcolor='rgba(255,255,255,0.05)', title=""), xaxis=dict(title=""), showlegend=False, height=340, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_overall, use_container_width=True)

        with col_right:
            st.markdown('<div class="section-title">Daftar Line di Bawah Target Urut Gap</div>', unsafe_allow_html=True)
            if selected_line != "Semua Line":
                if avg_oee < active_target:
                    st.error(f"Line {selected_line} tidak mencapai target. Kekurangan: {(active_target - avg_oee):.2f} percent.")
                else:
                    st.success(f"Line {selected_line} berhasil memenuhi atau melampaui target yang ditentukan.")
            else:
                line_summary = df.groupby("LineID").agg({'OEE_pct': 'mean', 'Target_Line': 'first', 'Avail_pct': 'mean', 'Perf_pct': 'mean', 'Qual_pct': 'mean'}).reset_index()
                problem_list = [{"Nama Line": row['LineID'], "Target": f"{row['Target_Line']:.1f}%", "Aktual OEE": f"{row['OEE_pct']:.2f}%", "Gap": row['Target_Line'] - row['OEE_pct'], "Kekurangan": f"-{(row['Target_Line'] - row['OEE_pct']):.2f}%", "Availability": f"{row['Avail_pct']:.1f}%", "Performance": f"{row['Perf_pct']:.1f}%", "Quality": f"{row['Qual_pct']:.1f}%"} for idx, row in line_summary.iterrows() if row['Target_Line'] - row['OEE_pct'] > 0]
                if problem_list:
                    df_problems = pd.DataFrame(problem_list).sort_values(by="Gap", ascending=False).drop(columns=["Gap"])
                    df_problems.index = range(1, len(df_problems) + 1)
                    st.dataframe(df_problems, height=270, use_container_width=True)
                else:
                    st.success("Luar biasa! Seluruh Line produksi berhasil mencapai target OEE spesifik.")

        st.markdown("---")

        # 5. CHART SECTION 2: BATANG AKTUAL + GARIS TARGET (COMBO CHART)
        st.markdown('<div class="section-title">Perbandingan Target vs Pencapaian OEE Setiap Line</div>', unsafe_allow_html=True)
        
        df_line_oee = df.groupby("LineID").agg({'Target_Line': 'first', 'OEE_pct': 'mean'}).reset_index().sort_values(by="OEE_pct", ascending=False)
        
        # Penentuan Warna Batang Berdasarkan Pencapaian Target
        colors = ['#10B981' if oee >= tgt else '#EF4444' for oee, tgt in zip(df_line_oee['OEE_pct'], df_line_oee['Target_Line'])]
        
        fig_bar_compare = go.Figure()

        # 1. Grafik Batang untuk Aktual OEE
        fig_bar_compare.add_trace(go.Bar(
            x=df_line_oee['LineID'],
            y=df_line_oee['OEE_pct'],
            name='Aktual OEE',
            marker_color=colors,
            text=[f"{val:.1f}%" for val in df_line_oee['OEE_pct']],
            textposition='outside'
        ))

        # 2. Grafik Garis untuk Target Line
        fig_bar_compare.add_trace(go.Scatter(
            x=df_line_oee['LineID'],
            y=df_line_oee['Target_Line'],
            name='Target Line',
            mode='lines+markers',
            line=dict(color='#6366F1', width=3, dash='dash'),
            marker=dict(size=8, color='#818CF8'),
            text=[f"{val:.1f}%" for val in df_line_oee['Target_Line']],
            textposition='top center'
        ))

        fig_bar_compare.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#9CA3AF'),
            yaxis=dict(range=[0, 115], gridcolor='rgba(255,255,255,0.05)', title="OEE (%)"),
            xaxis=dict(title="", tickangle=-45),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""),
            height=430,
            margin=dict(l=10, r=10, t=20, b=80)
        )
        st.plotly_chart(fig_bar_compare, use_container_width=True)

        st.markdown("---")

        # Tren Pergerakan Harian
        st.markdown(f'<div class="section-title">Tren Pergerakan OEE Harian Line {selected_line}</div>', unsafe_allow_html=True)
        if selected_line == "Semua Line":
            df_daily_trend = df.groupby("Tgl")["OEE_pct"].mean().reset_index()
            fig_line = px.line(df_daily_trend, x="Tgl", y="OEE_pct", markers=True)
        else:
            fig_line = px.line(df_filtered, x="Tgl", y="OEE_pct", markers=True)
        
        fig_line.update_traces(line_color="#10B981", line_width=3, marker=dict(size=8, color="#34D399"))
        fig_line.add_hline(y=active_target, line_dash="dash", line_color="#EF4444", annotation_text=f"Target ({active_target:.1f}%)", annotation_position="bottom right")
        fig_line.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#9CA3AF'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="OEE (%)"), xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Tanggal"), height=380, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_line, use_container_width=True)

        # 6. AI ANALYSIS ENGINE
        st.markdown('<div class="section-title">AI Executive Insights dan Diagnosis Performa</div>', unsafe_allow_html=True)
        
        factor_details = {
            "Availability": {"gap": STD_AVAIL - avg_avail, "actual": avg_avail, "target": STD_AVAIL, "loss_type": "Downtime Losses Breakdown dan Setup", "action": "Percepat waktu pergantian cetakan SMED dan kurangi waktu mesin mati akibat kerusakan unplanned breakdown."},
            "Performance": {"gap": STD_PERF - avg_perf, "actual": avg_perf, "target": STD_PERF, "loss_type": "Speed Losses dan Micro Stoppages", "action": "Analisis penyebab penurunan kecepatan operasional mesin, kurangi henti singkat minor stops, serta kalibrasi siklus standar."},
            "Quality": {"gap": STD_QUAL - avg_qual, "actual": avg_qual, "target": STD_QUAL, "loss_type": "Defect Losses Reject dan Rework", "action": "Perketat inspeksi material awal, tingkatkan kendali proses visual, dan evaluasi ulang setelan standar produksi."}
        }

        sorted_factors = sorted(factor_details.items(), key=lambda item: item[1]["gap"], reverse=True)
        p1_name, p1_val = sorted_factors[0]
        p2_name, p2_val = sorted_factors[1]
        p3_name, p3_val = sorted_factors[2]

        st.markdown(f"""
### Laporan Evaluasi AI: {selected_line}
Berdasarkan evaluasi tren data harian, pencapaian OEE berada pada tingkat {avg_oee:.2f}% (Target: {active_target:.1f}%).

---

#### Rekomendasi Utama: Fokus Perbaiki {p1_name} Terlebih Dahulu!
Indikator {p1_name} mengalami penyimpangan kerugian paling dominan dengan gap sebesar {abs(p1_val['gap']):.2f}% di bawah standar (Aktual: {p1_val['actual']:.2f}% vs Standar: {p1_val['target']:.1f}%). Kerugian ini terutama dipicu oleh {p1_val['loss_type']}.

#### Urutan Matriks Prioritas Perbaikan Roadmap:
1. Prioritas 1 — {p1_name} (Gap: {p1_val['gap']:.2f}% | Aktual: {p1_val['actual']:.2f}%)
   Tindakan: {p1_val['action']}
2. Prioritas 2 — {p2_name} (Gap: {p2_val['gap']:.2f}% | Aktual: {p2_val['actual']:.2f}%)
   Tindakan: {p2_val['action']}
3. Prioritas 3 — {p3_name} (Gap: {p3_val['gap']:.2f}% | Aktual: {p3_val['actual']:.2f}%)
   Tindakan: Indikator ini relatif stabil, pertahankan performa operasional.
""")

        st.info(f"Catatan Sistem: Menyelesaikan permasalahan pada Prioritas 1 ({p1_name}) akan memberikan dampak kenaikan OEE yang paling signifikan terhadap total produktivitas.")

        with st.expander("Lihat Mentah Data Excel Detail"):
            st.dataframe(df_filtered, use_container_width=True)

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")

else:
    st.info("Silakan unggah file Excel OEE di sidebar sebelah kiri untuk mulai menampilkan analisis dashboard.")

# 7. FOOTER COPYRIGHT
st.markdown('<div class="footer">copyright ardha_dyota - PT. ARGAPURA 2026</div>', unsafe_allow_html=True)
