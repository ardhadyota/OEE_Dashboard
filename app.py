import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="OEE Analysis & PDCA Dashboard",
    page_layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. KONSTANTA & NAMA FILE ---
ACTION_PLAN_FILE = "pdca_action_plan.csv"

# --- 3. FUNGSI BANTUAN (HELPER FUNCTIONS) ---
def load_or_init_action_plan():
    """Memuat data PDCA Action Plan dari CSV atau membuat dataframe default jika belum ada."""
    if os.path.exists(ACTION_PLAN_FILE):
        try:
            df = pd.read_csv(ACTION_PLAN_FILE)
            # PERBAIKAN TIPE DATA: Konversi kolom tanggal dari String ke Datetime
            if "Tanggal Inisiasi" in df.columns:
                df["Tanggal Inisiasi"] = pd.to_datetime(df["Tanggal Inisiasi"], errors="coerce")
            if "Target Selesai" in df.columns:
                df["Target Selesai"] = pd.to_datetime(df["Target Selesai"], errors="coerce")
            return df
        except Exception as e:
            st.warning(f"Gagal membaca file Action Plan: {e}. Membuat tabel baru.")
    
    # Template default jika file tidak ditemukan
    return pd.DataFrame({
        "ID Issue": ["ISSUE-001"],
        "Aktivitas / PDCA": ["Pembersihan rutin sensor OEE"],
        "PIC": ["Tim Maintenance"],
        "Status": ["In Progress"],
        "Tanggal Inisiasi": [pd.to_datetime(datetime.date.today())],
        "Target Selesai": [pd.to_datetime(datetime.date.today() + datetime.timedelta(days=7))],
        "Catatan": ["Optimalisasi keandalan data"]
    })

def save_action_plan(df):
    """Menyimpan data PDCA Action Plan kembali ke file CSV."""
    try:
        df_to_save = df.copy()
        # Konversi tipe datetime kembali ke string YYYY-MM-DD untuk disimpan di CSV
        if "Tanggal Inisiasi" in df_to_save.columns:
            df_to_save["Tanggal Inisiasi"] = df_to_save["Tanggal Inisiasi"].dt.strftime("%Y-%m-%d")
        if "Target Selesai" in df_to_save.columns:
            df_to_save["Target Selesai"] = df_to_save["Target Selesai"].dt.strftime("%Y-%m-%d")
        df_to_save.to_csv(ACTION_PLAN_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan data Action Plan: {e}")
        return False

# --- 4. SIDEBAR CONTROL PANEL ---
st.sidebar.title(" Control Panel")
uploaded_file = st.sidebar.file_uploader(
    "Unggah File Excel OEE Bulanan (.xlsx, .xls)",
    type=["xlsx", "xls"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Panduan Upload:**\nPastikan file Excel memiliki kolom standar OEE: Availability, Performance, Quality, atau data downtime.")

# --- 5. HEADER UTAMA DASHBOARD ---
st.title("📊 Dashboard Analisis OEE & Action Plan PDCA")
st.markdown("Aplikasi ini membantu menganalisis indikator OEE serta mengelola rencana aksi perbaikan berkelanjutan (PDCA).")

# --- 6. LOGIKA UTAMA APLIKASI ---
if uploaded_file is not None:
    # PERBAIKAN SYNTAX: Seluruh blok try memiliki penanganan 'except' di akhir
    try:
        # Membaca data dari Excel
        excel_data = pd.ExcelFile(uploaded_file)
        sheet_names = excel_data.sheet_names
        selected_sheet = st.sidebar.selectbox("Pilih Lembar Kerja (Sheet):", sheet_names)
        
        df_raw = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        st.subheader(f"📈 Ringkasan Data: {selected_sheet}")
        
        # Contoh Ringkasan KPI / Metrik OEE
        col1, col2, col3, col4 = st.columns(4)
        oee_val = df_raw.select_dtypes(include=[np.number]).mean().mean() if not df_raw.empty else 0.0
        
        col1.metric("Rata-rata OEE Overall", f"{min(oee_val, 100.0):.2f}%")
        col2.metric("Availability Rate", "88.5%", "1.2%")
        col3.metric("Performance Rate", "92.1%", "-0.5%")
        col4.metric("Quality Rate", "99.0%", "0.3%")
        
        # Preview Data Mentah
        with st.expander("👁️ Lihat Data Mentah Excel", expanded=False):
            st.dataframe(df_raw, use_container_width=True)
            
        st.markdown("---")
        
        # --- TABEL ACTION PLAN PDCA ---
        st.subheader("🛠️ Rencana Aksi Perbaikan (PDCA Tracker)")
        st.write("Kelola dan perbarui status tindakan korektif secara terintegrasi.")
        
        df_action = load_or_init_action_plan()
        
        # Editor Data Interaktif
        edited_df = st.data_editor(
            df_action,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "ID Issue": st.column_config.TextColumn("ID Issue", required=True),
                "Aktivitas / PDCA": st.column_config.TextColumn("Rencana Aktivitas", width="large"),
                "PIC": st.column_config.TextColumn("Penanggung Jawab (PIC)"),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Open", "In Progress", "Completed", "On Hold"],
                    default="Open"
                ),
                "Tanggal Inisiasi": st.column_config.DateColumn(
                    "Tanggal Inisiasi",
                    format="YYYY-MM-DD"
                ),
                "Target Selesai": st.column_config.DateColumn(
                    "Target Selesai",
                    format="YYYY-MM-DD"
                ),
                "Catatan": st.column_config.TextColumn("Catatan Tambahan")
            },
            key="pdca_editor"
        )
        
        if st.button("💾 Simpan Perubahan Action Plan", type="primary"):
            if save_action_plan(edited_df):
                st.success("✅ Perubahan Rencana Aksi PDCA berhasil disimpan!")
                
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data Excel: {e}")

else:
    st.info("💡 Silakan unggah file Excel OEE Bulanan pada Control Panel di sebelah kiri untuk menampilkan analisis.")
    
    st.markdown("---")
    st.subheader("📋 Rencana Aksi PDCA (Mode Standalone)")
    
    try:
        df_action = load_or_init_action_plan()
        
        edited_df = st.data_editor(
            df_action,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "ID Issue": st.column_config.TextColumn("ID Issue", required=True),
                "Aktivitas / PDCA": st.column_config.TextColumn("Rencana Aktivitas", width="large"),
                "PIC": st.column_config.TextColumn("Penanggung Jawab (PIC)"),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Open", "In Progress", "Completed", "On Hold"],
                    default="Open"
                ),
                "Tanggal Inisiasi": st.column_config.DateColumn(
                    "Tanggal Inisiasi",
                    format="YYYY-MM-DD"
                ),
                "Target Selesai": st.column_config.DateColumn(
                    "Target Selesai",
                    format="YYYY-MM-DD"
                ),
                "Catatan": st.column_config.TextColumn("Catatan Tambahan")
            },
            key="pdca_editor_standalone"
        )
        
        if st.button("💾 Simpan Perubahan Action Plan", type="primary"):
            if save_action_plan(edited_df):
                st.success("✅ Perubahan Rencana Aksi PDCA berhasil disimpan!")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat PDCA Action Plan: {e}")
