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
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
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
        return pd.read_csv(ACTION_PLAN_FILE)
    else:
        df_init = pd.DataFrame(columns=cols)
        df_init.to_csv(ACTION_PLAN_FILE, index=False)
        return df_init


# FUNGSI PENENTU STATUS PENCAPAIAN LINE
def get_health_status(oee_actual, oee_target):
    if oee_actual < (oee_target - 5.0):
        return "🔴 Critical Alert", "critical"
    elif oee_actual < oee_target:
        return "🟡 Warning", "warning"
    else:
        return "🟢 On Track", "ontrack"


# 3. KAMUS TARGET SPESIFIK LINE
LINE_STANDARDS = {
    "BUTYL TAPE LINE 1": {
        "avail": 99.0,
        "perf": 98.0,
        "qual": 100.00,
        "oee": 96.74,
    },
    "BUTYL TAPE LINE 2": {
        "avail": 99.0,
        "perf": 98.0,
        "qual": 100.00,
        "oee": 96.74,
    },
    "BUTYL TAPE LINE 3": {
        "avail": 99.0,
        "perf": 98.0,
        "qual": 100.00,
        "oee": 96.74,
    },
    "BUTYL TAPE LINE 4": {
        "avail": 99.0,
        "perf": 98.0,
        "qual": 100.00,
        "oee": 96.74,
    },
    "BUTYL TAPE LINE 5": {
        "avail": 99.0,
        "perf": 98.0,
        "qual": 100.00,
        "oee": 96.74,
    },
    "BTP MIXING": {"avail": 98.0, "perf": 99.0, "qual": 100.00, "oee": 96.74},
    "DFOAM ASSY 1": {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "DFOAM ASSY 2": {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "DFOAM ASSY 3": {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "DFOAM ASSY 4": {"avail": 98.0, "perf": 100.0, "qual": 100.00, "oee": 98.00},
    "PAD PILLAR NOUTONG": {
        "avail": 80.0,
        "perf": 100.0,
        "qual": 100.00,
        "oee": 80.00,
    },
    "STF PUNCHING": {"avail": 100.0, "perf": 98.0, "qual": 100.00, "oee": 97.83},
    "STF PUNCHING 1": {
        "avail": 100.0,
        "perf": 98.0,
        "qual": 100.00,
        "oee": 97.83,
    },
    "PVC LINE MC 1": {"avail": 93.0, "perf": 99.0, "qual": 99.95, "oee": 92.35},
    "PVC LINE MC 2": {"avail": 93.0, "perf": 99.0, "qual": 99.95, "oee": 92.35},
    "SPOT MASTIC MIX. 1": {
        "avail": 93.0,
        "perf": 100.0,
        "qual": 100.00,
        "oee": 93.48,
    },
    "SPOT MASTIC MIX. 2": {
        "avail": 93.0,
        "perf": 100.0,
        "qual": 100.00,
        "oee": 93.48,
    },
    "STF EXTRUDING SHIFT 1": {
        "avail": 90.0,
        "perf": 100.0,
        "qual": 100.00,
        "oee": 90.00,
    },
    "STF EXTRUDING SHIFT 2": {
        "avail": 90.0,
        "perf": 100.0,
        "qual": 100.00,
        "oee": 90.00,
    },
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

        # -------------------------------------------------------------
        # SIDEBAR FILTER DATA (LINE & PERIODE WAKTU / KAIZEN ANALYTICS)
        # -------------------------------------------------------------
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            "<h4 style='color: #E2E8F0;'>Filter Data</h4>",
            unsafe_allow_html=True,
        )

        # 1. Filter Line
        sorted_lines = sorted(list(df["LineID"].dropna().unique()))
        lines = ["Semua Line"] + sorted_lines
        selected_line = st.sidebar.selectbox("Pilih Production Line:", lines)

        # 2. Filter Periode Waktu
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

        # Data yang sudah di-filter Line & Waktu untuk analisis detail
        df_filtered = (
            filtered_df_time.copy()
            if selected_line == "Semua Line"
            else filtered_df_time[filtered_df_time["LineID"] == selected_line]
        )

        # -------------------------------------------------------------
        # SEKSI A: EXECUTIVE SUMMARY & STATUS PENCAPAIAN LINE
        # -------------------------------------------------------------
        st.markdown(
            '<div class="section-title">A. Executive Summary — Status & Pencapaian Tahunan</div>',
            unsafe_allow_html=True,
        )

        # REKAP STATUS PENCAPAIAN SELURUH LINE BERDASARKAN PERIODE YANG DIPILIH
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
        bar_colors = []
        for v in df_summary["OEE_Aktual"]:
            if pd.notnull(v):
                bar_colors.append("#3B82F6" if v >= 94.0 else "#F87171")
            else:
                bar_colors.append("#1F2937")

        fig_trend_year.add_trace(
            go.Bar(
                x=df_summary["Bulan"],
                y=df_summary["OEE_Aktual"],
                text=[
                    f"{v:.1f}%" if pd.notnull(v) else ""
                    for v in df_summary["OEE_Aktual"]
                ],
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
            annotation_font=dict(
                color="#EF4444", size=12, family="Arial Black"
            ),
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

        df["Target_Avail"] = df["LineID"].apply(
            lambda x: get_target_by_line(x)["avail"]
        )
        df["Target_Perf"] = df["LineID"].apply(
            lambda x: get_target_by_line(x)["perf"]
        )
        df["Target_Qual"] = df["LineID"].apply(
            lambda x: get_target_by_line(x)["qual"]
        )

        active_std = (
            DEFAULT_OVERALL_STD
            if selected_line == "Semua Line"
            else get_target_by_line(selected_line)
        )

        avg_oee = df_filtered["OEE_pct"].mean()
        avg_avail = df_filtered["Avail_pct"].mean()
        avg_perf = df_filtered["Perf_pct"].mean()
        avg_qual = df_filtered["Qual_pct"].mean()

        status_text, status_type = get_health_status(avg_oee, active_std["oee"])

        if status_type == "critical":
            st.error(
                f"**STATUS PENCAPAIAN: {status_text} — Line: {selected_line}**\n\n"
                f"**Defisit OEE melebihi 5% dari Target** (Aktual: {avg_oee:.2f}% vs Target: {active_std['oee']:.2f}%)\n\n"
                f"Mandat Operasional: Eskalasi segera ke Manajer Produksi & Engineering untuk intervensi darurat."
            )
        elif status_type == "warning":
            st.warning(
                f"**STATUS PENCAPAIAN: {status_text} — Line: {selected_line}**\n\n"
                f"**OEE berada di bawah Target** (Aktual: {avg_oee:.2f}% vs Target: {active_std['oee']:.2f}%)\n\n"
                f"Mandat Operasional: Perhatian supervisor & evaluasi harian pada akar masalah utama."
            )
        else:
            st.success(
                f"**STATUS PENCAPAIAN: {status_text} — Line: {selected_line}**\n\n"
                f"**Performa Operasional Memenuhi / Melebihi Target** (Aktual: {avg_oee:.2f}% vs Target: {active_std['oee']:.2f}%)\n\n"
                f"Mandat Operasional: Pertahankan performa operasional & kepatuhan Preventive Maintenance."
            )

        st.markdown("---")

        def get_badge_html(diff, target_text):
            if diff >= 0:
                return f'<span class="metric-badge badge-success">+{diff:.2f}% vs {target_text}</span>'
            return f'<span class="metric-badge badge-danger">{diff:.2f}% vs {target_text}</span>'

        diff_oee = avg_oee - active_std["oee"]
        diff_avail = avg_avail - active_std["avail"]
        diff_perf = avg_perf - active_std["perf"]
        diff_qual = avg_qual - active_std["qual"]

        std_oee_txt = f"Target {active_std['oee']:.2f}%"
        std_avail_txt = f"Target {active_std['avail']:.1f}%"
        std_perf_txt = f"Target {active_std['perf']:.1f}%"
        std_qual_txt = f"Target {active_std['qual']:.2f}%"

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(
            f'<div class="metric-card"><div class="metric-title">Overall OEE</div><div class="metric-value">{avg_oee:.2f}%</div>{get_badge_html(diff_oee, std_oee_txt)}</div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="metric-card"><div class="metric-title">Availability</div><div class="metric-value">{avg_avail:.2f}%</div>{get_badge_html(diff_avail, std_avail_txt)}</div>',
            unsafe_allow_html=True,
        )
        c3.markdown(
            f'<div class="metric-card"><div class="metric-title">Performance</div><div class="metric-value">{avg_perf:.2f}%</div>{get_badge_html(diff_perf, std_perf_txt)}</div>',
            unsafe_allow_html=True,
        )
        c4.markdown(
            f'<div class="metric-card"><div class="metric-title">Quality Rate</div><div class="metric-value">{avg_qual:.2f}%</div>{get_badge_html(diff_qual, std_qual_txt)}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 1.2])

        with col_left:
            st.markdown(
                '<div class="section-title">Benchmark Target vs Aktual</div>',
                unsafe_allow_html=True,
            )
            df_overall_comp = pd.DataFrame(
                {
                    "Kategori": ["Target Line", "Aktual OEE"],
                    "Nilai": [active_std["oee"], avg_oee],
                }
            )
            fig_overall = px.bar(
                df_overall_comp,
                x="Kategori",
                y="Nilai",
                text="Nilai",
                color="Kategori",
                color_discrete_map={
                    "Target Line": "#3B82F6",
                    "Aktual OEE": (
                        "#10B981" if avg_oee >= active_std["oee"] else "#EF4444"
                    ),
                },
            )
            fig_overall.update_traces(
                texttemplate="%{text:.2f}%", textposition="outside"
            )
            fig_overall.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9CA3AF"),
                yaxis=dict(range=[0, 115]),
                showlegend=False,
                height=340,
            )
            st.plotly_chart(fig_overall, use_container_width=True)

        with col_right:
            st.markdown(
                '<div class="section-title">Daftar Status Pencapaian Line Produksi</div>',
                unsafe_allow_html=True,
            )
            if selected_line != "Semua Line":
                status_lbl, _ = get_health_status(avg_oee, active_std["oee"])
                st.info(
                    f"**Line:** {selected_line}\n\n"
                    f"**Status:** {status_lbl}\n\n"
                    f"**OEE:** {avg_oee:.2f}% | **Target:** {active_std['oee']:.2f}% | **Gap:** {(avg_oee - active_std['oee']):+.2f}%"
                )
            else:
                line_summary = (
                    filtered_df_time.groupby("LineID")
                    .agg(
                        {
                            "OEE_pct": "mean",
                            "Target_Line": "first",
                            "Avail_pct": "mean",
                            "Perf_pct": "mean",
                            "Qual_pct": "mean",
                        }
                    )
                    .reset_index()
                )

                line_summary["Status Pencapaian"], _ = zip(
                    *line_summary.apply(
                        lambda r: get_health_status(r["OEE_pct"], r["Target_Line"]),
                        axis=1,
                    )
                )

                line_summary["Gap"] = line_summary["OEE_pct"] - line_summary["Target_Line"]
                line_summary = line_summary.sort_values(by="Gap", ascending=True)

                display_tbl = line_summary[
                    ["Status Pencapaian", "LineID", "Target_Line", "OEE_pct", "Gap"]
                ].copy()
                display_tbl.columns = [
                    "Status",
                    "Nama Line",
                    "Target OEE",
                    "Aktual OEE",
                    "Deviasi Gap",
                ]
                display_tbl["Target OEE"] = display_tbl["Target OEE"].apply(
                    lambda x: f"{x:.2f}%"
                )
                display_tbl["Aktual OEE"] = display_tbl["Aktual OEE"].apply(
                    lambda x: f"{x:.2f}%"
                )
                display_tbl["Deviasi Gap"] = display_tbl["Deviasi Gap"].apply(
                    lambda x: f"{x:+.2f}%"
                )

                display_tbl.index = range(1, len(display_tbl) + 1)
                st.dataframe(display_tbl, height=270, use_container_width=True)

        st.markdown("---")

        # PARETO ANALYSIS GLOBAL
        st.markdown(
            '<div class="section-title">Breakdown Six Big Losses & Diagram Pareto Kerugian (Menit)</div>',
            unsafe_allow_html=True,
        )

        EXPLICIT_LOSS_COLS = [
            "Unplanned Downtime",
            "Setup & Adjustment",
            "Idling & Minor Stops",
            "Reduced Speed",
            "Process Defects",
            "Startup Losses",
            "Planned Shutdown (Non-OEE)",
        ]

        available_loss_cols = [
            col for col in EXPLICIT_LOSS_COLS if col in df.columns
        ]
        for col in available_loss_cols:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.replace(",", ".").str.strip()
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df_filtered_loss = df_filtered.copy()

        loss_data = {}
        for col in available_loss_cols:
            total_val = df_filtered_loss[col].sum()
            loss_data[col] = round(total_val)

        loss_sums = pd.DataFrame(
            list(loss_data.items()), columns=["Penyebab_Losses", "Menit"]
        )

        missing_explicit = [
            c for c in EXPLICIT_LOSS_COLS if c not in loss_sums["Penyebab_Losses"].values
        ]
        if missing_explicit:
            df_missing = pd.DataFrame(
                {"Penyebab_Losses": missing_explicit, "Menit": [0] * len(missing_explicit)}
            )
            loss_sums = pd.concat([loss_sums, df_missing], ignore_index=True)

        loss_sums = loss_sums.sort_values(by="Menit", ascending=False).reset_index(drop=True)

        loss_sums["Kumulatif_Menit"] = loss_sums["Menit"].cumsum()
        total_loss_min = loss_sums["Menit"].sum()

        if total_loss_min > 0:
            loss_sums["Kumulatif_Pct"] = (
                loss_sums["Kumulatif_Menit"] / total_loss_min
            ) * 100
        else:
            loss_sums["Kumulatif_Pct"] = 0.0

        top_5_losses = loss_sums.head(5)

        col_pareto_chart, col_pareto_table = st.columns([1.5, 1])

        with col_pareto_chart:
            fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])

            fig_pareto.add_trace(
                go.Bar(
                    x=loss_sums["Penyebab_Losses"],
                    y=loss_sums["Menit"],
                    name="Durasi (Menit)",
                    marker_color="#EF4444",
                    text=[f"{int(m):,}m" for m in loss_sums["Menit"]],
                    textposition="outside",
                ),
                secondary_y=False,
            )

            fig_pareto.add_trace(
                go.Scatter(
                    x=loss_sums["Penyebab_Losses"],
                    y=loss_sums["Kumulatif_Pct"],
                    name="Kumulatif (%)",
                    mode="lines+markers",
                    line=dict(color="#F59E0B", width=3),
                    marker=dict(size=7),
                ),
                secondary_y=True,
            )

            fig_pareto.add_hline(
                y=80,
                line_dash="dash",
                line_color="#10B981",
                annotation_text="Batas Pareto 80%",
                secondary_y=True,
            )

            fig_pareto.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9CA3AF"),
                height=380,
                showlegend=False,
                xaxis=dict(tickangle=-25),
            )
            fig_pareto.update_yaxes(
                title_text="Durasi Kerugian (Menit)", secondary_y=False
            )
            fig_pareto.update_yaxes(
                title_text="Kumulatif (%)",
                range=[0, 110],
                secondary_y=True,
            )

            st.plotly_chart(fig_pareto, use_container_width=True)

        with col_pareto_table:
            st.markdown(
                "<h4 style='color: #F3F4F6;'>Top 5 Akar Masalah Utama</h4>",
                unsafe_allow_html=True,
            )
            top_5_display = top_5_losses[
                ["Penyebab_Losses", "Menit", "Kumulatif_Pct"]
            ].copy()
            top_5_display.columns = [
                "Kategori Losses",
                "Durasi (Menit)",
                "Kumulatif (%)",
            ]
            top_5_display["Durasi (Menit)"] = top_5_display[
                "Durasi (Menit)"
            ].apply(lambda x: f"{int(x):,} menit")
            top_5_display["Kumulatif (%)"] = top_5_display[
                "Kumulatif (%)"
            ].apply(lambda x: f"{x:.1f}%")
            top_5_display.index = range(1, len(top_5_display) + 1)

            st.dataframe(top_5_display, use_container_width=True)

            if total_loss_min > 0:
                top3_pct = top_5_losses["Kumulatif_Pct"].iloc[
                    min(2, len(top_5_losses) - 1)
                ]
                st.caption(
                    f"**Total Kerugian Operasional:** {int(total_loss_min):,} Menit. Dengan mengatasi Top 3 penyebab teratas, tim dapat menyelesaikan **{top3_pct:.1f}%** dari total seluruh kendala lini produksi."
                )

        st.markdown("---")

        # BREAKDOWN SIX BIG LOSSES PER LINE
        st.markdown(
            '<div class="section-title">Matrix Breakdown Six Big Losses per Line & Prioritas Perbaikan</div>',
            unsafe_allow_html=True,
        )

        df_line_losses = filtered_df_time.groupby("LineID")[available_loss_cols].sum()
        df_line_losses = df_line_losses.round(0).astype(int)

        df_line_losses["TOTAL_LOSSES"] = df_line_losses.sum(axis=1)
        df_line_losses = df_line_losses.sort_values(
            by="TOTAL_LOSSES", ascending=False
        )

        top_cause_per_line = []
        for idx_line, row_l in df_line_losses.iterrows():
            causes_only = row_l.drop("TOTAL_LOSSES")
            if causes_only.max() > 0:
                top_cause_name = causes_only.idxmax()
                top_cause_val = causes_only.max()
                top_cause_per_line.append(
                    f"{top_cause_name} ({top_cause_val:,} min)"
                )
            else:
                top_cause_per_line.append("N/A")

        df_line_losses_display = df_line_losses.copy()
        df_line_losses_display["Penyebab Utama Dominan"] = top_cause_per_line

        for c_col in available_loss_cols + ["TOTAL_LOSSES"]:
            df_line_losses_display[c_col] = df_line_losses_display[c_col].apply(
                lambda x: f"{x:,}"
            )

        ordered_cols = (
            ["TOTAL_LOSSES", "Penyebab Utama Dominan"] + available_loss_cols
        )
        df_line_losses_display = df_line_losses_display[ordered_cols]

        col_matrix_tbl, col_priority_info = st.columns([1.6, 1])

        with col_matrix_tbl:
            st.markdown(
                "<h4 style='color: #F3F4F6;'>Matrix Total Waktu Hilang (Menit) per Line</h4>",
                unsafe_allow_html=True,
            )
            st.dataframe(df_line_losses_display, height=350, use_container_width=True)

        with col_priority_info:
            st.markdown(
                "<h4 style='color: #EF4444;'>Urutan Line Prioritas Perbaikan</h4>",
                unsafe_allow_html=True,
            )

            worst_3_lines = df_line_losses.head(3)

            priority_html = ""
            for i, (l_name, l_row) in enumerate(worst_3_lines.iterrows(), 1):
                tot_l = l_row["TOTAL_LOSSES"]
                causes_only = l_row.drop("TOTAL_LOSSES")
                main_l_name = causes_only.idxmax() if causes_only.max() > 0 else "-"
                main_l_val = causes_only.max()

                priority_html += f"""
                <div style="background-color: #1E293B; border-left: 4px solid #EF4444; padding: 10px 14px; margin-bottom: 10px; border-radius: 6px;">
                    <div style="font-weight: bold; color: #F8FAFC;">Prioritas #{i}: {l_name}</div>
                    <div style="font-size: 0.88rem; color: #94A3B8;">Total Kerugian: <b style="color:#F87171;">{tot_l:,} Menit</b></div>
                    <div style="font-size: 0.85rem; color: #F59E0B;">Fokus Utama: <b>{main_l_name}</b> ({main_l_val:,} Menit)</div>
                </div>
                """

            st.markdown(priority_html, unsafe_allow_html=True)

        st.markdown("---")

        # RATIO PENCAPAIAN
        st.markdown(
            '<div class="section-title">Ratio Pencapaian per Line [Ratio]</div>',
            unsafe_allow_html=True,
        )
        df_line_ratio = (
            filtered_df_time.groupby("LineID")
            .agg({"Target_Line": "first", "OEE_pct": "mean"})
            .reset_index()
        )
        df_line_ratio["Target_Line"] = df_line_ratio["Target_Line"].replace(
            0, 1
        )
        df_line_ratio["Ratio"] = (
            df_line_ratio["OEE_pct"] / df_line_ratio["Target_Line"]
        )
        df_line_ratio["Selisih_pct"] = (
            df_line_ratio["OEE_pct"] - df_line_ratio["Target_Line"]
        )
        df_line_ratio = df_line_ratio.sort_values(by="Ratio", ascending=False)

        ratio_colors = [
            "#60A5FA" if r >= 1.0 else "#F87171" for r in df_line_ratio["Ratio"]
        ]

        fig_ratio = go.Figure()
        hover_texts = [
            f"<b>{line}</b><br>Target: {tgt:.2f}%<br>Aktual: {oee:.2f}%<br>Selisih: {sel:+.2f}%<br>Ratio: {r:.3f}"
            for line, tgt, oee, sel, r in zip(
                df_line_ratio["LineID"],
                df_line_ratio["Target_Line"],
                df_line_ratio["OEE_pct"],
                df_line_ratio["Selisih_pct"],
                df_line_ratio["Ratio"],
            )
        ]

        fig_ratio.add_trace(
            go.Bar(
                x=df_line_ratio["LineID"],
                y=df_line_ratio["Ratio"],
                marker_color=ratio_colors,
                text=[f"{r:.3f}" for r in df_line_ratio["Ratio"]],
                textposition="outside",
                hoverinfo="text",
                hovertext=hover_texts,
            )
        )
        fig_ratio.add_shape(
            type="line",
            x0=-0.5,
            x1=len(df_line_ratio["LineID"]) - 0.5,
            y0=1.0,
            y1=1.0,
            line=dict(color="#EF4444", width=3),
        )
        fig_ratio.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"),
            yaxis=dict(
                title="[Ratio]",
                range=[0, max(df_line_ratio["Ratio"].max() * 1.15, 1.3)],
            ),
            xaxis=dict(title="", tickangle=-45),
            height=430,
            showlegend=False,
        )
        st.plotly_chart(fig_ratio, use_container_width=True)

        st.markdown("---")

        # TREND HARIAN
        st.markdown(
            f'<div class="section-title">Tren Pergerakan OEE Harian Line {selected_line}</div>',
            unsafe_allow_html=True,
        )
        df_daily = (
            df_filtered.groupby("Tgl")["OEE_pct"].mean().reset_index()
        )
        df_daily["Tgl_Str"] = df_daily["Tgl"].dt.strftime("%d %b %Y")

        fig_line = go.Figure()
        fig_line.add_trace(
            go.Scatter(
                x=df_daily["Tgl_Str"],
                y=df_daily["OEE_pct"],
                mode="lines+markers",
                line=dict(color="#10B981", width=3),
                marker=dict(size=8, color="#34D399"),
                text=[f"{val:.1f}%" for val in df_daily["OEE_pct"]],
                hoverinfo="x+text",
            )
        )
        fig_line.add_hline(
            y=active_std["oee"],
            line_dash="dash",
            line_color="#EF4444",
            line_width=2,
            annotation_text=f"Target Line ({active_std['oee']:.2f}%)",
            annotation_position="top right",
        )
        fig_line.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"),
            yaxis=dict(title="OEE (%)"),
            xaxis=dict(title="Tanggal Produksi", type="category", tickangle=-45),
            height=420,
            showlegend=False,
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # SEKSI KALKULATOR SIMULASI WHAT-IF
        st.markdown("---")
        st.markdown(
            '<div class="section-title">Kalkulator Simulasi & What-If Analysis (Pengambilan Keputusan Proaktif)</div>',
            unsafe_allow_html=True,
        )

        with st.container():
            st.markdown('<div class="sim-card">', unsafe_allow_html=True)
            st.markdown("#### 🎯 Simulasi Dampak Pengurangan Downtime Terhadap OEE")
            
            sim_col_input, sim_col_output = st.columns([1, 1.2])

            with sim_col_input:
                target_sim_line = st.selectbox(
                    "Pilih Line untuk Simulasi:", 
                    sorted_lines, 
                    index=sorted_lines.index(selected_line) if selected_line in sorted_lines else 0,
                    key="sim_line_select"
                )
                downtime_reduction_pct = st.slider(
                    f"Target Pengurangan Unplanned Downtime (%):",
                    min_value=0,
                    max_value=100,
                    value=20,
                    step=5,
                    help="Geser slider untuk melihat potensi kenaikan OEE jika downtime berhasil diturunkan."
                )

                df_sim_line = df_filtered[df_filtered["LineID"] == target_sim_line] if selected_line == "Semua Line" else df_filtered
                num_days = len(df_sim_line["Tgl"].unique()) if len(df_sim_line) > 0 else 1
                
                curr_line_oee = df_sim_line["OEE_pct"].mean() if not df_sim_line.empty else 0
                curr_line_avail = df_sim_line["Avail_pct"].mean() if not df_sim_line.empty else 0
                curr_line_perf = df_sim_line["Perf_pct"].mean() if not df_sim_line.empty else 0
                curr_line_qual = df_sim_line["Qual_pct"].mean() if not df_sim_line.empty else 0
                target_line_oee = get_target_by_line(target_sim_line)["oee"]

                total_unplanned_dt = df_sim_line["Unplanned Downtime"].sum() if "Unplanned Downtime" in df_sim_line.columns else 0
                dt_saved_min = total_unplanned_dt * (downtime_reduction_pct / 100.0)
                remaining_dt_min = total_unplanned_dt - dt_saved_min

                total_planned_operating_time = (num_days * 24 * 60)
                
                if total_planned_operating_time > 0 and total_unplanned_dt > 0:
                    sim_avail = ((total_planned_operating_time - remaining_dt_min) / total_planned_operating_time) * 100.0
                    sim_avail = min(sim_avail, 100.0)
                else:
                    sim_avail = curr_line_avail + (100.0 - curr_line_avail) * (downtime_reduction_pct / 100.0)

                sim_oee = (sim_avail / 100.0) * (curr_line_perf / 100.0) * (curr_line_qual / 100.0) * 100.0
                oee_gain = sim_oee - curr_line_oee

            with sim_col_output:
                st.markdown(f"**Proyeksi Perbaikan untuk Line: {target_sim_line}**")
                
                s_c1, s_c2, s_c3 = st.columns(3)
                s_c1.metric("OEE Saat Ini", f"{curr_line_oee:.2f}%")
                s_c2.metric("Proyeksi OEE Baru", f"{sim_oee:.2f}%", delta=f"+{oee_gain:.2f}%")
                s_c3.metric("Target OEE Line", f"{target_line_oee:.2f}%")

                dt_per_day_target = (remaining_dt_min / num_days) if num_days > 0 else 0
                
                if sim_oee >= target_line_oee:
                    st.success(
                        f"✅ **Target Tercapai!** Dengan menurunkan Downtime sebesar **{downtime_reduction_pct}%** "
                        f"(menghemat **{int(dt_saved_min):,} menit**), OEE Line diproyeksikan naik menjadi **{sim_oee:.2f}%** "
                        f"(Melampaui target **{target_line_oee:.2f}%**)."
                    )
                else:
                    st.warning(
                        f"⚠️ **Masih Perlu Perbaikan:** Penurunan Downtime **{downtime_reduction_pct}%** meningkatkan OEE ke **{sim_oee:.2f}%**, "
                        f"namun masih kurang **{(target_line_oee - sim_oee):.2f}%** dari target. Kombinasikan dengan perbaikan *Speed Loss* / *Setup Time*."
                    )

                st.info(
                    f"💡 **Target Mingguan/Harian Tim Production:** Batasi total Unplanned Downtime maksimal **{int(dt_per_day_target)} menit/hari** "
                    f"(atau **{int(dt_per_day_target * 7)} menit/minggu**) untuk memastikan target OEE tercapai sebelum akhir bulan."
                )

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # DIAGNOSIS AI
        st.markdown(
            '<div class="section-title">AI Executive Insights dan Diagnosis Performa Spesifik Line</div>',
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

        if problem_factors:
            p1_name, p1_val = problem_factors[0]
            header_status = f"Fokus Perbaiki {p1_name} Terlebih Dahulu!"
            desc_status = f"Indikator **{p1_name}** pada **{selected_line}** mengalami defisit terbesar yaitu **{p1_val['defisit']:.2f}%** di bawah target (Aktual: {p1_val['actual']:.2f}% vs Target Line: {p1_val['target']:.2f}%)."

            prioritas_text = ""
            for idx, (fname, fdata) in enumerate(problem_factors, start=1):
                prioritas_text += f"{idx}. **Prioritas {idx} — {fname}** (Defisit: -{fdata['defisit']:.2f}% | Aktual: {fdata['actual']:.2f}% vs Target Line: {fdata['target']:.2f}%)\n"
                prioritas_text += f"   *Tindakan:* {fdata['action']}\n"
        else:
            header_status = (
                "Seluruh Faktor Utama Memenuhi Standar Spesifik!"
            )
            desc_status = f"Luar biasa! Semua faktor (Availability, Performance, Quality) pada **{selected_line}** telah memenuhi atau melampaui target spesifik masing-masing."
            prioritas_text = "Tidak ada indikator yang memerlukan tindakan perbaikan darurat saat ini."

        st.markdown(
            f"""
### Laporan Diagnosis AI: {selected_line}
Pencapaian OEE saat ini adalah **{avg_oee:.2f}%** dibanding target spesifik line sebesar **{active_std['oee']:.2f}%**.

---

#### Rekomendasi Utama: {header_status}
{desc_status}

#### Urutan Matriks Prioritas Perbaikan:
{prioritas_text}
"""
        )
        with st.expander("Lihat Data Excel Mentah Detail"):
            st.dataframe(df_filtered, use_container_width=True)

        # TABEL MONITORING ACTION PLAN PDCA
        st.markdown("---")
        st.markdown(
            '<div class="section-title">Tabel Monitoring Action Plan PDCA (Accountability Control)</div>',
            unsafe_allow_html=True,
        )

        df_action_plan = load_or_init_action_plan()

        with st.expander("Tambah Action Plan Improvement Baru (+)", expanded=False):
            with st.form("form_add_action_plan", clear_on_submit=True):
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1:
                    tgl_inisiasi = st.date_input("Tanggal Inisiasi")
                    line_target = st.selectbox("Line Produksi", sorted_lines)
                with f_col2:
                    tema_imp = st.text_input("Tema Improvement", placeholder="Contoh: Reduced speed pada extruder")
                    pic_name = st.text_input("PIC (Pemilik Tugas)", placeholder="Contoh: Agus (Maint) / Budi (Prod)")
                with f_col3:
                    target_selesai = st.date_input("Target Selesai")
                    status_initial = st.selectbox("Status Awal", ["On Progress", "Done", "Delay"])

                btn_submit = st.form_submit_button("Simpan Action Plan")

                if btn_submit:
                    if tema_imp.strip() == "" or pic_name.strip() == "":
                        st.warning("Mohon isi Tema Improvement dan PIC terlebih dahulu!")
                    else:
                        new_row = pd.DataFrame(
                            [{
                                "Tanggal Inisiasi": tgl_inisiasi.strftime("%Y-%m-%d"),
                                "Line Produksi": line_target,
                                "Tema Improvement": tema_imp.strip(),
                                "PIC": pic_name.strip(),
                                "Target Selesai": target_selesai.strftime("%Y-%m-%d"),
                                "Status": status_initial
                            }]
                        )
                        df_action_plan = pd.concat([df_action_plan, new_row], ignore_index=True)
                        df_action_plan.to_csv(ACTION_PLAN_FILE, index=False)
                        st.success("Action plan berhasil ditambahkan!")
                        st.rerun()

        count_total = len(df_action_plan)
        count_done = len(df_action_plan[df_action_plan["Status"] == "Done"]) if count_total > 0 else 0
        count_progress = len(df_action_plan[df_action_plan["Status"] == "On Progress"]) if count_total > 0 else 0
        count_delay = len(df_action_plan[df_action_plan["Status"] == "Delay"]) if count_total > 0 else 0

        st_c1, st_c2, st_c3, st_c4 = st.columns(4)
        st_c1.metric("Total Action Plan", count_total)
        st_c2.metric("Status: Done", count_done)
        st_c3.metric("Status: On Progress", count_progress)
        st_c4.metric("Status: Delay", count_delay)

        if not df_action_plan.empty:
            st.caption("Ubah status tugas secara langsung pada tabel di bawah ini atau hapus baris jika perlu:")
            
            edited_df = st.data_editor(
                df_action_plan,
                column_config={
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        help="Status Pekerjaan PDCA",
                        options=["On Progress", "Done", "Delay"],
                        required=True,
                    ),
                    "Tanggal Inisiasi": st.column_config.DateColumn("Tanggal Inisiasi"),
                    "Target Selesai": st.column_config.DateColumn("Target Selesai"),
                },
                num_rows="dynamic",
                use_container_width=True,
                key="action_plan_editor"
            )

            if st.button("Simpan Perubahan Tabel Action Plan"):
                edited_df.to_csv(ACTION_PLAN_FILE, index=False)
                st.success("Perubahan Action Plan PDCA berhasil disimpan!")
                st.rerun()
        else:
            st.info("Belum ada Action Plan yang terdaftar. Gunakan tombol 'Tambah Action Plan Improvement Baru (+)' di atas untuk memulai pencatatan PDCA.")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {str(e)}")

else:
    st.markdown(
        '<div class="section-title">A. Executive Summary — Pencapaian OEE Tahunan (Jan - Des)</div>',
        unsafe_allow_html=True,
    )
    fig_trend_year = go.Figure()

    bar_colors = [
        (
            "#3B82F6"
            if (v is not None and v >= 94.0)
            else "#F87171"
            if v is not None
            else "#1F2937"
        )
        for v in df_summary["OEE_Aktual"]
    ]

    fig_trend_year.add_trace(
        go.Bar(
            x=df_summary["Bulan"],
            y=df_summary["OEE_Aktual"],
            text=[
                f"{v:.1f}%" if pd.notnull(v) else ""
                for v in df_summary["OEE_Aktual"]
            ],
            textposition="outside",
            marker_color=bar_colors,
        )
    )
    fig_trend_year.add_hline(
        y=94.0,
        line_color="#EF4444",
        line_width=3,
        annotation_text="Target: 94%",
        annotation_position="top right",
    )
    fig_trend_year.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF"),
        yaxis=dict(title="[%]", range=[70, 105]),
        height=350,
    )
    st.plotly_chart(fig_trend_year, use_container_width=True)

    st.info(
        "Silakan unggah file Excel data OEE harian di sidebar untuk menganalisis per line dan memperbarui tren bulanan."
    )

st.markdown(
    '<div class="footer">copyright ardha_dyota - PT. ARGAPURA 2026</div>',
    unsafe_allow_html=True,
)
