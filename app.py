import base64
import os
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# 1. KONFIGURASI HALAMAN DAN STYLES
st.set_page_config(
    page_title="OEE Executive Analytics - PT. ARGAPURA",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .metric-card {
        background: linear-gradient(135deg, #1E2640 0%, #111827 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .status-card-critical {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid #EF4444;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .status-card-warning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid #F59E0B;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .status-card-ontrack {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid #10B981;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .sim-card {
        background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin-top: 10px;
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
""",
    unsafe_allow_html=True,
)

# 2. DATABASE REKAP TAHUNAN & PDCA ACTION PLAN
SUMMARY_FILE = "oee_monthly_summary.csv"
ACTION_PLAN_FILE = "action_plan_pdca.csv"


def load_or_init_monthly_summary():
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    if os.path.exists(SUMMARY_FILE):
        return pd.read_csv(SUMMARY_FILE)
    else:
        df_init = pd.DataFrame({"Bulan": months, "OEE_Aktual": [None] * 12})
        df_init.to_csv(SUMMARY_FILE, index=False)
        return df_init


def load_or_init_action_plan():
    cols = [
        "Tanggal Inisiasi",
        "Line Produksi",
        "Tema Improvement",
        "PIC",
        "Target Selesai",
        "Status",
    ]
    if os.path.exists(ACTION_PLAN_FILE):
        try:
            df = pd.read_csv(ACTION_PLAN_FILE, dtype=str).fillna("")
            for col in cols:
                if col not in df.columns:
                    df[col] = ""
            return df[cols]
        except Exception:
            pass

    df_init = pd.DataFrame(columns=cols)
    df_init.to_csv(ACTION_PLAN_FILE, index=False)
    return df_init


def get_health_status(oee_actual, oee_target):
    if oee_actual < (oee_target - 5.0):
        return "🔴 Critical Alert", "critical"
    elif oee_actual < oee_target:
        return "🟡 Warning", "warning"
    else:
        return "🟢 On Track", "ontrack"


LINE_STANDARDS = {
    "BUTYL TAPE LINE 1": {"avail": 99.0, "perf": 98.0, "qual": 100.00, "oee": 96.74},
    "BUTYL TAPE LINE 2": {"avail": 99.0, "perf": 98.0, "qual": 100.00, "oee": 96.74},
    "BUTYL TAPE LINE 3": {"avail": 99.0, "perf": 98.0, "qual": 100.00, "oee": 96.74},
    "BUTYL TAPE LINE 4": {"avail": 99.0, "perf": 98.0, "qual": 100.00, "oee": 96.74},
    "BUTYL TAPE LINE 5": {"avail": 99.0, "perf": 98.0, "qual": 100.00, "oee": 96.74},
    "BTP MIXING": {"avail": 98.0, "perf": 99.0, "qual": 100.00, "oee": 96.74},
    "DFOAM ASSY 1": {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "DFOAM ASSY 2": {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "DFOAM ASSY 3": {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "DFOAM ASSY 4": {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "PAD PILLAR NOUTONG": {"avail": 80.0, "perf": 100.0, "qual": 100.00, "oee": 80.00},
    "STF PUNCHING": {"avail": 100.0, "perf": 98.0, "qual": 100.00, "oee": 97.83},
    "STF PUNCHING 1": {"avail": 100.0, "perf": 98.0, "qual": 100.00, "oee": 97.83},
    "PVC LINE MC 1": {"avail": 93.0, "perf": 99.0, "qual": 99.95, "oee": 92.35},
    "PVC LINE MC 2": {"avail": 93.0, "perf": 99.0, "qual": 99.95, "oee": 92.35},
    "SPOT MASTIC MIX. 1": {"avail": 93.0, "perf": 100.0, "qual": 100.00, "oee": 93.48},
    "SPOT MASTIC MIX. 2": {"avail": 93.0, "perf": 100.0, "qual": 100.00, "oee": 93.48},
    "STF EXTRUDING SHIFT 1": {"avail": 90.0, "perf": 100.0, "qual": 100.00, "oee": 90.00},
    "STF EXTRUDING SHIFT 2": {"avail": 90.0, "perf": 100.0, "qual": 100.00, "oee": 90.00},
    "STF MIXING ": {"avail": 92.0, "perf": 100.0, "qual": 100.00, "oee": 92.00},
}

DEFAULT_OVERALL_STD = {"avail": 90.0, "perf": 95.0, "qual": 99.0, "oee": 94.00}


def get_target_by_line(line_name):
    if not isinstance(line_name, str):
        return DEFAULT_OVERALL_STD

    clean_name = line_name.upper().strip()
    if clean_name in LINE_STANDARDS:
        return LINE_STANDARDS[clean_name]

    cleaned = re.sub(r"\bSHIFT\s*\d+\b", "", clean_name)
    cleaned = cleaned.replace("EXTRUDING", "EXT").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)

    if cleaned in LINE_STANDARDS:
        return LINE_STANDARDS[cleaned]

    for key in LINE_STANDARDS:
        if key in clean_name or clean_name in key:
            return LINE_STANDARDS[key]

    return DEFAULT_OVERALL_STD


# FUNGSI AI EXECUTIVE INSIGHTS (LOGIKA BARU DENGAN DETEKSI LOSS TIME)
def render_ai_executive_insights(df_filtered, active_std, avg_avail, avg_perf, avg_qual, selected_line):
    st.markdown(
        '<div class="section-title">H. AI Executive Insights dan Diagnosis Performa Spesifik Line</div>',
        unsafe_allow_html=True,
    )

    factor_details = {
        "Availability": {
            "defisit": active_std["avail"] - avg_avail,
            "actual": avg_avail,
            "target": active_std["avail"],
            "action": "Fokus pada pengurangan unplanned breakdown dan optimasi waktu pergantian cetakan (SMED).",
        },
        "Performance": {
            "defisit": active_std["perf"] - avg_perf,
            "actual": avg_perf,
            "target": active_std["perf"],
            "action": "Analisis penurunan speed operasional mesin serta kurangi frekuensi henti singkat (minor stops).",
        },
        "Quality": {
            "defisit": active_std["qual"] - avg_qual,
            "actual": avg_qual,
            "target": active_std["qual"],
            "action": "Tingkatkan inspeksi material awal dan evaluasi ulang setelan standar parameter proses.",
        },
    }

    problem_factors = [
        (name, data)
        for name, data in factor_details.items()
        if data["defisit"] > 0.001
    ]
    problem_factors.sort(key=lambda x: x[1]["defisit"], reverse=True)

    # ANALISIS LOSS TIME (Pencegah Blind Spot Target Rendah)
    loss_setup = df_filtered["Setup & Adjustment"].sum() if "Setup & Adjustment" in df_filtered.columns else 0
    loss_downtime = df_filtered["Unplanned Downtime"].sum() if "Unplanned Downtime" in df_filtered.columns else 0
    loss_stops = df_filtered["Idling & Minor Stops"].sum() if "Idling & Minor Stops" in df_filtered.columns else 0

    slow_col = "Slow Cycles" if "Slow Cycles" in df_filtered.columns else "Reduced Speed"
    loss_slow = df_filtered[slow_col].sum() if slow_col in df_filtered.columns else 0

    loss_summary = {
        "Setup & Adjustment": loss_setup,
        "Unplanned Downtime": loss_downtime,
        "Idling & Minor Stops": loss_stops,
        "Slow Cycles": loss_slow,
    }

    top_loss_type = max(loss_summary, key=loss_summary.get)
    top_loss_minutes = loss_summary[top_loss_type]

    if top_loss_type in df_filtered.columns:
        line_loss = df_filtered.groupby("LineID")[top_loss_type].sum().sort_values(ascending=False)
        worst_line = line_loss.index[0] if not line_loss.empty else "-"
        worst_line_minutes = line_loss.iloc[0] if not line_loss.empty else 0
    else:
        worst_line, worst_line_minutes = "-", 0

    if top_loss_minutes > 120 and not problem_factors:
        st.error(f"⚠️ **Rekomendasi Utama: Terdeteksi Pemborosan Waktu Signifikan ({top_loss_minutes:.0f} Menit)!**")
        st.markdown(
            f"""
            Meskipun persentase OEE saat ini pada **{selected_line}** telah mencapai target, terdapat potensi efisiensi besar yang terbuang pada kategori **{top_loss_type}** sebesar **{top_loss_minutes:.0f} menit**.

            **Langkah Perbaikan Prioritas AI:**
            * **Fokus Utama Line:** Line **{worst_line}** menyumbang kerugian terbesar yaitu **{worst_line_minutes:.0f} menit**.
            * **Saran Aksional:** Terapkan metode *Single-Minute Exchange of Die* (SMED) untuk mereduksi waktu persiapan/pergantian cetakan (*setup*) hingga di bawah 10 menit.
            * **Evaluasi Target OEE:** Target OEE saat ini terlalu rendah/longgar. Naikkan target bertahap sebesar **5% - 10%** untuk menekan pemborosan waktu henti.
            """
        )
    elif problem_factors:
        p1_name, p1_val = problem_factors[0]
        st.warning(f"⚠️ **Fokus Perbaiki {p1_name} Terlebih Dahulu!**")
        st.write(factor_details[p1_name]["action"])
    else:
        st.success("✅ **Rekomendasi Utama: Proses Produksi Sangat Efisien!**")
        st.write("Total waktu terbuang di seluruh line sangat minim. Pertahankan performa ini!")


# SIDEBAR LOGO & CONTROLS
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    st.sidebar.markdown(
        f'<div style="background-color:#FFF;padding:10px;border-radius:12px;text-align:center;width:140px;margin:0 auto 20px auto;"><img src="data:image/png;base64,{img_b64}" style="width:100%;"></div>',
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        "<h2 style='text-align: center; color: #38BDF8;'>PT. ARGAPURA</h2>",
        unsafe_allow_html=True,
    )

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<h3 style='color: #818CF8;'>Control Panel</h3>", unsafe_allow_html=True
)
uploaded_file = st.sidebar.file_uploader(
    "Unggah Data Excel OEE Bulanan", type=["xlsx", "xls"]
)

st.markdown(
    """
    <div class="dashboard-header">
        <div><h1>OEE Executive Analytics</h1><p>Monitoring Performa Line Produksi & Status Operasional</p></div>
        <div style="text-align:right;"><h3 style="color:#38BDF8;margin:0;">PT. ARGAPURA</h3><p style="color:#94A3B8;margin:0;">ESTABLISHED 1954</p></div>
    </div>
""",
    unsafe_allow_html=True,
)

df_summary = load_or_init_monthly_summary()

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Data Daily")
        df.columns = [str(c).strip() for c in df.columns]

        required_cols = [
            "Tgl",
            "LineID",
            "OEE",
            "Avail",
            "% Performance",
            "Quality",
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(
                f"Format Excel Tidak Sesuai! Kolom berikut tidak ditemukan: {', '.join(missing_cols)}"
            )
            st.stop()

        df["Tgl"] = pd.to_datetime(df["Tgl"], errors="coerce")
        df = df.dropna(subset=["Tgl"]).sort_values(by="Tgl")

        for col in ["OEE", "Avail", "% Performance", "Quality"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df["OEE_pct"] = df["OEE"].apply(lambda x: x * 100 if x <= 1.0 else x)
        df["Avail_pct"] = df["Avail"].apply(
            lambda x: x * 100 if x <= 1.0 else x
        )
        df["Perf_pct"] = df["% Performance"].apply(
            lambda x: x * 100 if x <= 1.0 else x
        )
        df["Qual_pct"] = df["Quality"].apply(
            lambda x: x * 100 if x <= 1.0 else x
        )

        current_month_name = df["Tgl"].dt.strftime("%b").iloc[0]
        avg_monthly_all_lines = df["OEE_pct"].mean()

        df_summary.loc[
            df_summary["Bulan"] == current_month_name, "OEE_Aktual"
        ] = avg_monthly_all_lines
        df_summary.to_csv(SUMMARY_FILE, index=False)

        st.sidebar.markdown("---")
        st.sidebar.markdown(
            "<h4 style='color: #E2E8F0;'>Filter Data</h4>",
            unsafe_allow_html=True,
        )

        sorted_lines = sorted(list(df["LineID"].dropna().unique()))
        lines = ["Semua Line"] + sorted_lines
        selected_line = st.sidebar.selectbox("Pilih Production Line:", lines)

        time_filter_option = st.sidebar.radio(
            "Mode Periode Waktu:",
            ["Semua Periode (1 Bulan)", "Mingguan (Week 1 - Week 4)", "Custom Range Tanggal"]
        )

        min_data_date = df["Tgl"].min().date()
        max_data_date = df["Tgl"].max().date()

        filtered_df_time = df.copy()

        if time_filter_option == "Mingguan (Week 1 - Week 4)":
            week_choice = st.sidebar.selectbox(
                "Pilih Minggu:",
                ["Week 1 (Tgl 1 - 7)", "Week 2 (Tgl 8 - 14)", "Week 3 (Tgl 15 - 21)", "Week 4 (Tgl 22 - End)"]
            )
            if "Week 1" in week_choice:
                filtered_df_time = df[df["Tgl"].dt.day <= 7]
            elif "Week 2" in week_choice:
                filtered_df_time = df[(df["Tgl"].dt.day >= 8) & (df["Tgl"].dt.day <= 14)]
            elif "Week 3" in week_choice:
                filtered_df_time = df[(df["Tgl"].dt.day >= 15) & (df["Tgl"].dt.day <= 21)]
            elif "Week 4" in week_choice:
                filtered_df_time = df[df["Tgl"].dt.day >= 22]

        elif time_filter_option == "Custom Range Tanggal":
            date_range = st.sidebar.date_input(
                "Rentang Tanggal (Evaluasi Kaizen):",
                value=(min_data_date, max_data_date),
                min_value=min_data_date,
                max_value=max_data_date
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_d, end_d = date_range
                filtered_df_time = df[(df["Tgl"].dt.date >= start_d) & (df["Tgl"].dt.date <= end_d)]

        if filtered_df_time.empty:
            st.warning("⚠️ Tidak ada data untuk rentang tanggal yang dipilih. Silakan sesuaikan kembali filter periode waktu di sidebar.")
            st.stop()

        df_filtered = (
            filtered_df_time.copy()
            if selected_line == "Semua Line"
            else filtered_df_time[filtered_df_time["LineID"] == selected_line]
        )

        # SEKSI A: EXECUTIVE SUMMARY
        st.markdown(
            '<div class="section-title">A. Executive Summary — Status Line & Pencapaian Tahunan</div>',
            unsafe_allow_html=True,
        )

        filtered_df_time["Target_Line"] = filtered_df_time["LineID"].apply(
            lambda x: get_target_by_line(x)["oee"]
        )

        all_line_summary = (
            filtered_df_time.groupby("LineID")
            .agg({"OEE_pct": "mean", "Target_Line": "first"})
            .reset_index()
        )

        all_line_summary["Status_Label"], all_line_summary["Status_Type"] = (
            zip(
                *all_line_summary.apply(
                    lambda r: get_health_status(r["OEE_pct"], r["Target_Line"]),
                    axis=1,
                )
            )
        )

        count_critical = (all_line_summary["Status_Type"] == "critical").sum()
        count_warning = (all_line_summary["Status_Type"] == "warning").sum()
        count_ontrack = (all_line_summary["Status_Type"] == "ontrack").sum()

        m1, m2, m3 = st.columns(3)
        m1.markdown(
            f'<div class="status-card-critical"><h4 style="color:#EF4444;margin:0;">🔴 Critical Alert</h4><h2 style="color:#FFF;margin:5px 0;">{count_critical} Line</h2><p style="font-size:0.8rem;color:#9CA3AF;margin:0;">OEE &lt; Target - 5% (Intervensi Manajer/Direksi)</p></div>',
            unsafe_allow_html=True,
        )
        m2.markdown(
            f'<div class="status-card-warning"><h4 style="color:#F59E0B;margin:0;">🟡 Warning Zone</h4><h2 style="color:#FFF;margin:5px 0;">{count_warning} Line</h2><p style="font-size:0.8rem;color:#9CA3AF;margin:0;">OEE &lt; Target (Perhatian Supervisor)</p></div>',
            unsafe_allow_html=True,
        )
        m3.markdown(
            f'<div class="status-card-ontrack"><h4 style="color:#10B981;margin:0;">🟢 On Track</h4><h2 style="color:#FFF;margin:5px 0;">{count_ontrack} Line</h2><p style="font-size:0.8rem;color:#9CA3AF;margin:0;">OEE &ge; Target (Sesuai Standar Operasional)</p></div>',
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        fig_trend_year = go.Figure()
        bar_colors = [
            "#3B82F6" if pd.notnull(v) and v >= 94.0 else ("#F87171" if pd.notnull(v) else "#1F2937")
            for v in df_summary["OEE_Aktual"]
        ]

        fig_trend_year.add_trace(
            go.Bar(
                x=df_summary["Bulan"],
                y=df_summary["OEE_Aktual"],
                text=[f"{v:.1f}%" if pd.notnull(v) else "" for v in df_summary["OEE_Aktual"]],
                textposition="outside",
                marker_color=bar_colors,
                name="Aktual OEE",
            )
        )

        fig_trend_year.add_hline(
            y=94.0,
            line_color="#EF4444",
            line_width=3,
            annotation_text="Target: 94%",
            annotation_position="top right",
            annotation_font=dict(color="#EF4444", size=12, family="Arial Black"),
        )

        fig_trend_year.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"),
            yaxis=dict(title="[%]", range=[70, 105]),
            xaxis=dict(title="Bulan Produksi"),
            height=320,
            showlegend=False,
        )
        st.plotly_chart(fig_trend_year, use_container_width=True)

        st.markdown("---")

        active_std = (
            DEFAULT_OVERALL_STD
            if selected_line == "Semua Line"
            else get_target_by_line(selected_line)
        )

        avg_oee = df_filtered["OEE_pct"].mean()
        avg_avail = df_filtered["Avail_pct"].mean()
        avg_perf = df_filtered["Perf_pct"].mean()
        avg_qual = df_filtered["Qual_pct"].mean()

        def get_badge_html(diff, target_text):
            if diff >= 0:
                return f'<span class="metric-badge badge-success">+{diff:.2f}% vs {target_text}</span>'
            return f'<span class="metric-badge badge-danger">{diff:.2f}% vs {target_text}</span>'

        diff_oee = avg_oee - active_std["oee"]
        diff_avail = avg_avail - active_std["avail"]
        diff_perf = avg_perf - active_std["perf"]
        diff_qual = avg_qual - active_std["qual"]

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-title">Overall OEE</div><div class="metric-value">{avg_oee:.2f}%</div>{get_badge_html(diff_oee, f"Target {active_std[\'oee\']:.2f}%")}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-title">Availability</div><div class="metric-value">{avg_avail:.2f}%</div>{get_badge_html(diff_avail, f"Target {active_std[\'avail\']:.1f}%")}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-title">Performance</div><div class="metric-value">{avg_perf:.2f}%</div>{get_badge_html(diff_perf, f"Target {active_std[\'perf\']:.1f}%")}</div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-title">Quality Rate</div><div class="metric-value">{avg_qual:.2f}%</div>{get_badge_html(diff_qual, f"Target {active_std[\'qual\']:.2f}%")}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # SEKSI H: AI EXECUTIVE INSIGHTS
        render_ai_executive_insights(df_filtered, active_std, avg_avail, avg_perf, avg_qual, selected_line)

        st.markdown("---")

        # SEKSI I: PDCA ACTION PLAN TRACKER
        st.markdown(
            '<div class="section-title">I. PDCA & Monitoring Improvement</div>',
            unsafe_allow_html=True,
        )

        if "df_action" not in st.session_state:
            st.session_state.df_action = load_or_init_action_plan()

        with st.expander("➕ Tambah Rencana PDCA Baru", expanded=False):
            with st.form("add_action_form"):
                f_date = st.date_input("Tanggal Inisiasi")
                f_line = st.selectbox("Line Produksi", sorted_lines)
                f_tema = st.text_input("Tema / Judul Improvement")
                f_pic = st.text_input("PIC (Penanggung Jawab)")
                f_target = st.date_input("Target Selesai")
                f_status = st.selectbox("Status", ["Plan", "Do", "Check", "Action", "Closed"])

                submitted = st.form_submit_button("Simpan Action Plan")
                if submitted:
                    new_row = pd.DataFrame([{
                        "Tanggal Inisiasi": f_date.strftime("%Y-%m-%d"),
                        "Line Produksi": f_line,
                        "Tema Improvement": f_tema,
                        "PIC": f_pic,
                        "Target Selesai": f_target.strftime("%Y-%m-%d"),
                        "Status": f_status
                    }])
                    st.session_state.df_action = pd.concat([st.session_state.df_action, new_row], ignore_index=True)
                    st.session_state.df_action.to_csv(ACTION_PLAN_FILE, index=False)
                    st.success("Rencana aksi berhasil disimpan!")
                    st.rerun()

        df_editor_input = st.session_state.df_action.copy()
        df_editor_input.insert(0, "No", range(1, len(df_editor_input) + 1))

        edited_df = st.data_editor(
            df_editor_input,
            hide_index=True,
            column_config={
                "No": st.column_config.NumberColumn("No", disabled=True, width="small"),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    help="Pilih status PDCA",
                    options=["Plan", "Do", "Check", "Action", "Closed"],
                    required=True,
                )
            },
            num_rows="dynamic",
            use_container_width=True,
            key="pdca_editor",
        )

        df_edited_raw = edited_df.drop(columns=["No"]).reset_index(drop=True)
        
        if not df_edited_raw.equals(st.session_state.df_action.reset_index(drop=True)):
            st.session_state.df_action = df_edited_raw
            st.session_state.df_action.to_csv(ACTION_PLAN_FILE, index=False)
            st.toast("Perubahan data berhasil disimpan!")
            st.rerun()

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")

else:
    st.info("💡 Silakan unggah berkas Excel data harian OEE melalui panel kontrol di sebelah kiri untuk memulai analisis.")

# FOOTER
st.markdown(
    '<div class="footer">PT. ARGAPURA — Operational Excellence & Executive Dashboard &copy;ardha.2026</div>',
    unsafe_allow_html=True,
)
