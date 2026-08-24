import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(page_title="OEE Analytics & AI Insights", layout="wide")

st.title("🏭 OEE Analytics Dashboard & AI Insights")

# 2. Sidebar Uploader & Filter
st.sidebar.header("📁 Upload & Filter")
uploaded_file = st.sidebar.file_uploader("Upload File Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='Data Daily')
        
        # Format tanggal & urutkan kronologis
        df['Tgl'] = pd.to_datetime(df['Tgl'])
        df = df.sort_values(by='Tgl')

        # Konversi desimal OEE ke persen
        df['OEE_pct'] = df['OEE'] * 100 if df['OEE'].max() <= 1.0 else df['OEE']
        df['Avail_pct'] = df['Avail']
        df['Perf_pct'] = df['% Performance'] * 100 if df['% Performance'].max() <= 1.0 else df['% Performance']
        df['Qual_pct'] = df['Quality'] * 100 if df['Quality'].max() <= 1.0 else df['Quality']

        overall_avg_oee = df['OEE_pct'].mean()
        TARGET_OEE = 94.0

        # ==========================================
        # 3. GRAFIK PALING ATAS: TARGET VS AKTUAL
        # ==========================================
        st.subheader("🎯 Target vs Aktual Pencapaian OEE (Semua Line)")
        
        df_target_vs_actual = pd.DataFrame({
            "Kategori": ["Target OEE", "Aktual OEE (Rata-Rata)"],
            "Persentase": [TARGET_OEE, overall_avg_oee],
            "Warna": ["Target (94%)", "Aktual"]
        })

        fig_target = px.bar(
            df_target_vs_actual,
            x="Kategori",
            y="Persentase",
            text="Persentase",
            color="Warna",
            color_discrete_map={
                "Target (94%)": "#2E7D32", 
                "Aktual": "#1976D2" if overall_avg_oee >= TARGET_OEE else "#D32F2F"
            },
            title=f"Perbandingan Target ({TARGET_OEE}%) vs Rata-Rata OEE Aktual ({overall_avg_oee:.2f}%)"
        )

        fig_target.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig_target.update_layout(yaxis=dict(range=[0, 110]), showlegend=False, height=350)
        st.plotly_chart(fig_target, width="stretch")

        st.markdown("---")

        # ==========================================
        # 4. FILTER LINE & METRICS KPI
        # ==========================================
        lines = ["Semua Line"] + list(df["LineID"].dropna().unique())
        selected_line = st.sidebar.selectbox("Pilih Line Spesifik:", lines)
        
        df_filtered = df.copy()
        if selected_line != "Semua Line":
            df_filtered = df_filtered[df_filtered["LineID"] == selected_line]

        avg_oee = df_filtered['OEE_pct'].mean()
        avg_avail = df_filtered['Avail_pct'].mean()
        avg_perf = df_filtered['Perf_pct'].mean()
        avg_qual = df_filtered['Qual_pct'].mean()

        st.subheader(f"📊 Ringkasan Pencapaian: {selected_line}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("OEE", f"{avg_oee:.2f}%", delta=f"{avg_oee - TARGET_OEE:.2f}% vs Target 94%")
        c2.metric("Availability", f"{avg_avail:.2f}%", delta=f"{avg_avail - 90.0:.2f}% vs Standar World Class (90%)")
        c3.metric("Performance", f"{avg_perf:.2f}%", delta=f"{avg_perf - 95.0:.2f}% vs Standar World Class (95%)")
        c4.metric("Quality", f"{avg_qual:.2f}%", delta=f"{avg_qual - 99.0:.2f}% vs Standar World Class (99%)")
        
        # ==========================================
        # 5. ROBOT ANALISIS AI (AI INSIGHTS)
        # ==========================================
        st.info("🤖 **Analisis AI & Rekomendasi Tindakan**")
        
        ai_notes = []
        if avg_oee >= TARGET_OEE:
            ai_notes.append(f"✅ **Pencapaian Sangat Baik:** Performa OEE ({avg_oee:.2f}%) berhasil melampaui target perusahaan sebesar {TARGET_OEE}%.")
        else:
            ai_notes.append(f"⚠️ **Di Bawah Target:** Performa OEE ({avg_oee:.2f}%) belum mencapai target {TARGET_OEE}% (Selisih: {avg_oee - TARGET_OEE:.2f}%).")

        # Deteksi Bottleneck Komponen
        bottlenecks = []
        if avg_avail < 90.0:
            bottlenecks.append(f"- **Availability Low ({avg_avail:.2f}%):** Terjadi banyak waktu ketiadaan produksi/breakdown mesin. Fokus pada perbaikan *Breakdown Maintenance* & durasi *Setup/Changeover*.")
        if avg_perf < 95.0:
            bottlenecks.append(f"- **Performance Low ({avg_perf:.2f}%):** Mesin beroperasi di bawah kecepatan ideal atau ada *minor stoppage* (mesin sering berhenti sesaat). Rekomendasi: Evaluasi *Ideal Cycle Time* & cek keausan komponen teknis.")
        if avg_qual < 99.0:
            bottlenecks.append(f"- **Quality Low ({avg_qual:.2f}%):** Ditemukan rasio produk cacat/reject atau rework yang tinggi. Rekomendasi: Inspeksi parameter proses cetak/setting mesin dan material masukan.")

        if bottlenecks:
            ai_notes.append("**Bottleneck / Area Masalah Utama:**\n" + "\n".join(bottlenecks))
        else:
            ai_notes.append("🌟 Semua komponen 3 (Availability, Performance, Quality) memenuhi standar efisiensi industri World Class.")

        st.markdown("\n\n".join(ai_notes))

        st.markdown("---")

        # ==========================================
        # 6. DIAGRAM BATANG PER LINE & TREN HARIAN
        # ==========================================
        st.subheader("📊 Perbandingan Pencapaian OEE per Line")
        df_line_oee = df.groupby("LineID")["OEE_pct"].mean().reset_index().sort_values(by="OEE_pct", ascending=False)
        
        fig_bar = px.bar(
            df_line_oee, x="LineID", y="OEE_pct", text="OEE_pct",
            color="OEE_pct", color_continuous_scale="Blues",
            title="Peringkat OEE per Line (Dari Terbesar ke Terkecil)"
        )
        fig_bar.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig_bar.add_hline(y=TARGET_OEE, line_dash="dash", line_color="green", annotation_text=f"Target {TARGET_OEE}%")
        st.plotly_chart(fig_bar, width="stretch")

        st.markdown("---")

        st.subheader(f"📈 Tren OEE Harian ({selected_line})")
        if selected_line == "Semua Line":
            df_daily_trend = df.groupby("Tgl")["OEE_pct"].mean().reset_index()
            fig_line = px.line(
                df_daily_trend, x="Tgl", y="OEE_pct", markers=True,
                title="Rata-rata Pergerakan OEE Harian (Semua Line)"
            )
        else:
            fig_line = px.line(
                df_filtered, x="Tgl", y="OEE_pct", markers=True,
                title=f"Pergerakan OEE Harian ({selected_line})"
            )

        fig_line.add_hline(y=TARGET_OEE, line_dash="dash", line_color="green")
        st.plotly_chart(fig_line, width="stretch")

    except Exception as e:
        st.error(f"Gagal membaca data: {e}")

else:
    st.info("👈 Unggah file Excel OEE Anda di sidebar sebelah kiri.")
