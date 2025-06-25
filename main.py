import streamlit as st
import pandas as pd
import os
from streamlit_option_menu import option_menu
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import json




# Konfigurasi kredensial dan folder Drive
scope = ['https://www.googleapis.com/auth/drive']
service_account_file = 'service_account.json'
parent_folder_id = "1WV7Xby3cEd2gHoRJNEzcDieSO0WUlMRB"

# Autentikasi Google Drive dari secrets
def authenticate():
    service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=["https://www.googleapis.com/auth/drive"])
    service = build('drive', 'v3', credentials=creds)
    return service

## Fungsi autentikasi Google Drive
# def authenticate():
#     creds = service_account.Credentials.from_service_account_file(
#         service_account_file, scopes=scope)
#     service = build('drive', 'v3', credentials=creds)
#     return service

# Fungsi upload ke Google Drive
def upload_to_drive(file_path, filename, parent_folder_id):
    service = authenticate()
    file_metadata = {
        'name': filename,
        'parents': [parent_folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return uploaded_file.get('id')

# Konfigurasi halaman
st.set_page_config(page_title="Form Reservasi Material", page_icon="📋", layout="wide")

# Folder lokal untuk menyimpan file sebelum upload
folder_path = "data_reservasi"
os.makedirs(folder_path, exist_ok=True)

# Sidebar menu
with st.sidebar:
    selected = option_menu(
        menu_title="Menu Utama",
        options=["Form", "Lihat Data", "File Tersimpan"],
        icons=["clipboard-check", "table", "folder"],
        menu_icon="menu-app",
        default_index=0,
    )

# ==========================
# HALAMAN FORM
# ==========================
if selected == "Form":
    st.title("📦 Form Input Reservasi Material")

    # ...
    with st.form("form_reservasi"):
        nama_file = st.text_input("📝 Nama File (tanpa .xlsx)")
        reservasi = st.text_input("Masukkan No. Reservasi")
        lokasi = st.text_input("Masukkan Lokasi")
        material_input = st.text_area("📦 Masukkan Daftar Material (1 baris 1 material)")
        quantity_input = st.text_area("🔢 Masukkan Jumlah Material (1 baris 1 jumlah, sesuai urutan material)")
        submit = st.form_submit_button("Simpan")

        if submit:
            if not nama_file or not reservasi or not lokasi or not material_input.strip() or not quantity_input.strip():
                st.warning("❗ Semua kolom wajib diisi!")
            else:
                list_material = material_input.strip().splitlines()
                list_quantity = quantity_input.strip().splitlines()

                if len(list_material) != len(list_quantity):
                    st.error("❌ Jumlah baris material dan jumlah baris quantity tidak sama!")
                else:
                    try:
                        quantity_numbers = [int(q.strip()) for q in list_quantity]
                    except ValueError:
                        st.error("❌ Quantity harus berupa angka!")
                        st.stop()

                    nama_file_sanitized = nama_file.strip().replace(" ", "_") + ".xlsx"
                    file_path = os.path.join(folder_path, nama_file_sanitized)

                    if os.path.exists(file_path):
                        st.error("❌ Nama file sudah ada. Silakan gunakan nama lain.")
                    else:
                        df_baru = pd.DataFrame({
                            "Reservasi": [reservasi] * len(list_material),
                            "Lokasi": [lokasi] * len(list_material),
                            "Material": list_material,
                            "Quantity": quantity_numbers
                        })
                        df_baru.to_excel(file_path, index=False)
                        st.success(f"✅ Data berhasil disimpan dalam file {nama_file_sanitized}")

                        try:
                            drive_file_id = upload_to_drive(file_path, nama_file_sanitized, parent_folder_id)
                            st.success(f"📤 File berhasil diunggah ke Google Drive dengan ID: {drive_file_id}")
                        except Exception as e:
                            st.error(f"❌ Gagal upload ke Google Drive: {e}")


# ==========================
# HALAMAN LIHAT DATA
# ==========================
elif selected == "Lihat Data":
    st.title("📊 Data Reservasi Tersimpan")

    excel_files = [f for f in os.listdir(folder_path) if f.endswith(".xlsx")]

    if excel_files:
        selected_file = st.selectbox("Pilih file untuk ditampilkan:", excel_files)
        file_path = os.path.join(folder_path, selected_file)

        df_tampil = pd.read_excel(file_path)
        edited_df = st.data_editor(df_tampil, use_container_width=True, num_rows="dynamic")

        if st.button("💾 Simpan Perubahan"):
            edited_df.to_excel(file_path, index=False)
            st.success("✅ Perubahan berhasil disimpan!")

        if st.button("🗑️ Hapus Isi File Ini"):
            df_kosong = pd.DataFrame(columns=["Reservasi", "Lokasi", "Material"])
            df_kosong.to_excel(file_path, index=False)
            st.success("✅ Data dalam file ini berhasil dihapus!")
    else:
        st.warning("⚠️ Belum ada file data tersedia.")

# ==========================
# HALAMAN FILE TERSIMPAN
# ==========================
elif selected == "File Tersimpan":
    st.title("📁 Daftar File Excel yang Tersimpan")

    excel_files = [f for f in os.listdir(folder_path) if f.endswith(".xlsx")]

    if excel_files:
        for file in excel_files:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"📄 {file}")
            with col2:
                if st.button("🗑️ Hapus", key=file):
                    file_path = os.path.join(folder_path, file)
                    os.remove(file_path)
                    st.success(f"✅ File {file} berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Belum ada file Excel yang tersimpan.")
