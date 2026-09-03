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

# 2. DATABASE REKAP TAHUNAN OTOMATIS
SUMMARY_FILE = "oee_monthly_summary.csv"


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
        <div><h1>OEE Executive Analytics</h1><p>Monitoring Pencapaian Tren OEE Tahunan dan Performa Line Produksi</p></div>
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

        # SEKSI A: EXECUTIVE SUMMARY
        st.markdown(
            '<div class="section-title">A. Executive Summary — Pencapaian OEE Tahunan (Jan - Des)</div>',
            unsafe_allow_html=True,
        )

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
            height=350,
            showlegend=False,
        )
        st.plotly_chart(fig_trend_year, use_container_width=True)

        st.markdown("---")

        df["Target_Line"] = df["LineID"].apply(
            lambda x: get_target_by_line(x)["oee"]
        )
        df["Target_Avail"] = df["LineID"].apply(
            lambda x: get_target_by_line(x)["avail"]
        )
        df["Target_Perf"] = df["LineID"].apply(
            lambda x: get_target_by_line(x)["perf"]
        )
        df["Target_Qual"] = df["LineID"].apply(
            lambda x: get_target_by_line(x)["qual"]
        )

        st.sidebar.markdown("---")
        st.sidebar.markdown(
            "<h4 style='color: #E2E8F0;'>Filter Data</h4>",
            unsafe_allow_html=True,
        )
        sorted_lines = sorted(list(df["LineID"].dropna().unique()))
        lines = ["Semua Line"] + sorted_lines
        selected_line = st.sidebar.selectbox("Pilih Production Line:", lines)

        df_filtered = (
            df.copy()
            if selected_line == "Semua Line"
            else df[df["LineID"] == selected_line]
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

        diff_oee = avg_oee - active_std["oee"]
        diff_avail = avg_avail - active_std["avail"]
        diff_perf = avg_perf - active_std["perf"]
        diff_qual = avg_qual - active_std["qual"]

        gap_oee = avg_oee - active_std["oee"]

        if gap_oee < -3.0:
            st.error(
                f"**SYSTEM STATUS: CRITICAL ALERT — Line: {selected_line}**\n\n"
                f"**OEE Mengalami Defisit Signifikan Dari Target Line**\n\n"
                f"Mandat Operasional: Eskalasi segera ke Manajer Produksi & Engineering untuk intervensi operasional darurat."
            )
        elif gap_oee < 0:
            st.warning(
                f"**SYSTEM STATUS: WARNING — Line: {selected_line}**\n\n"
                f"**OEE Belum Mencapai Target Spesifik Lini**\n\n"
                f"Mandat Operasional: Dibutuhkan perhatian ekstra dari Supervisor & evaluasi harian pada akar masalah utama."
            )
        else:
            st.success(
                f"**SYSTEM STATUS: ON TRACK — Line: {selected_line}**\n\n"
                f"**Performa Operasional Memenuhi / Melebihi Target Standard**\n\n"
                f"Mandat Operasional: Pertahankan ritme operasional & pastikan kepatuhan Preventive Maintenance standar."
            )

        st.markdown("---")

        def get_badge_html(diff, target_text):
            if diff >= 0:
                return f'<span class="metric-badge badge-success">+{diff:.2f}% vs {target_text}</span>'
            return f'<span class="metric-badge badge-danger">{diff:.2f}% vs {target_text}</span>'

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
                '<div class="section-title">Daftar Line di Bawah Target Urut Gap</div>',
                unsafe_allow_html=True,
            )
            if selected_line != "Semua Line":
                if avg_oee < active_std["oee"]:
                    st.error(
                        f"Line {selected_line} tidak mencapai target. Defisit OEE: {(active_std['oee'] - avg_oee):.2f}%."
                    )
                else:
                    st.success(
                        f"Line {selected_line} berhasil memenuhi/melampaui target yang ditentukan ({active_std['oee']:.2f}%)."
                    )
            else:
                line_summary = (
                    df.groupby("LineID")
                    .agg(
                        {
                            "OEE_pct": "mean",
                            "Target_Line": "first",
                            "Avail_pct": "mean",
                            "Target_Avail": "first",
                            "Perf_pct": "mean",
                            "Target_Perf": "first",
                            "Qual_pct": "mean",
                            "Target_Qual": "first",
                        }
                    )
                    .reset_index()
                )

                problem_list = []
                for idx, row in line_summary.iterrows():
                    gap_oee_val = row["Target_Line"] - row["OEE_pct"]
                    if gap_oee_val > 0:
                        problem_list.append(
                            {
                                "Nama Line": row["LineID"],
                                "Target OEE": f"{row['Target_Line']:.2f}%",
                                "Aktual OEE": f"{row['OEE_pct']:.2f}%",
                                "Gap": gap_oee_val,
                                "Kekurangan": f"-{gap_oee_val:.2f}%",
                                "Availability": f"{row['Avail_pct']:.1f}% / {row['Target_Avail']:.0f}%",
                                "Performance": f"{row['Perf_pct']:.1f}% / {row['Target_Perf']:.0f}%",
                                "Quality": f"{row['Qual_pct']:.1f}% / {row['Target_Qual']:.2f}%",
                            }
                        )

                if problem_list:
                    df_problems = (
                        pd.DataFrame(problem_list)
                        .sort_values(by="Gap", ascending=False)
                        .drop(columns=["Gap"])
                    )
                    df_problems.index = range(1, len(df_problems) + 1)
                    st.dataframe(
                        df_problems, height=270, use_container_width=True
                    )
                else:
                    st.success(
                        "Luar biasa! Seluruh Line produksi berhasil mencapai target OEE spesifik masing-masing."
                    )

        st.markdown("---")

        # =========================================================
        # SEKSI PARETO ANALYSIS GLOBAL (HASIL DIBULATKAN TANPA KOMA)
        # =========================================================
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
            col for col in EXPLICIT_LOSS_COLS if col in df_filtered.columns
        ]

        # Konversi tipe data losses jika string berkoma
        for col in available_loss_cols:
            if df[col].dtype == "object":
                df[col] = (
                    df[col].astype(str).str.replace(",", ".").str.strip()
                )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df_filtered_loss = (
            df.copy()
            if selected_line == "Semua Line"
            else df[df["LineID"] == selected_line]
        )

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

        # =========================================================
        # SEKSI BARU: BREAKDOWN SIX BIG LOSSES PER LINE (PRIORITAS REPARASI)
        # =========================================================
        st.markdown(
            '<div class="section-title">Matrix Breakdown Six Big Losses per Line & Prioritas Perbaikan</div>',
            unsafe_allow_html=True,
        )

        # Hitung sum per line untuk tiap kolom losses
        df_line_losses = df.groupby("LineID")[available_loss_cols].sum()
        # Pembulatan bulat utuh
        df_line_losses = df_line_losses.round(0).astype(int)

        # Tambahkan Total Losses per Line
        df_line_losses["TOTAL_LOSSES"] = df_line_losses.sum(axis=1)
        df_line_losses = df_line_losses.sort_values(
            by="TOTAL_LOSSES", ascending=False
        )

        # Temukan loss terbesar dominan di masing-masing line
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

        # Format tampilan angka di tabel agar ada pemisah ribuan
        for c_col in available_loss_cols + ["TOTAL_LOSSES"]:
            df_line_losses_display[c_col] = df_line_losses_display[c_col].apply(
                lambda x: f"{x:,}"
            )

        # Susun urutan kolom tampilan
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
            badges = ["badge-danger", "badge-danger", "badge-success"]
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

        # GRAFIK STACKED BAR LOSSES PER LINE
        st.markdown(
            "<h4 style='color: #F3F4F6;'>Visualisasi Komposisi Kerugian per Line Produksi</h4>",
            unsafe_allow_html=True,
        )

        fig_stacked_loss = go.Figure()
        colors_palette = [
            "#EF4444",
            "#F59E0B",
            "#3B82F6",
            "#10B981",
            "#8B5CF6",
            "#EC4899",
            "#64748B",
        ]

        for idx_c, l_col in enumerate(available_loss_cols):
            fig_stacked_loss.add_trace(
                go.Bar(
                    name=l_col,
                    x=df_line_losses.index,
                    y=df_line_losses[l_col],
                    marker_color=colors_palette[idx_c % len(colors_palette)],
                )
            )

        fig_stacked_loss.update_layout(
            barmode="stack",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"),
            xaxis=dict(tickangle=-35),
            yaxis=dict(title="Durasi Kerugian (Menit)"),
            height=380,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        st.plotly_chart(fig_stacked_loss, use_container_width=True)

        st.markdown("---")

        # SEKSI RATIO PENCAPAIAN
        st.markdown(
            '<div class="section-title">Ratio Pencapaian per Line [Ratio]</div>',
            unsafe_allow_html=True,
        )
        df_line_ratio = (
            df.groupby("LineID")
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

        # SEKSI TREND HARIAN
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

        # SEKSI DIAGNOSIS AI
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
