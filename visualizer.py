import os
import ffmpeg
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import shutil
import random

# ===== CONFIG =====
DRIVE_FOLDER_ID = "FOLDER_ID_DI_DRIVE"  # ganti dengan ID folder Drive yang berisi 1 MP3 & background
TMP_FOLDER = "tmp_files"
os.makedirs(TMP_FOLDER, exist_ok=True)
# ==================

# Autentikasi Drive
gauth = GoogleAuth()
gauth.LoadClientConfigFile("credentials.json")
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# Ambil semua file di folder Drive
file_list = drive.ListFile({'q': f"'{DRIVE_FOLDER_ID}' in parents and trashed=false"}).GetList()

# Filter MP3 (hanya 1 file)
mp3_files = [f for f in file_list if f['title'].lower().endswith('.mp3')]
if not mp3_files:
    raise FileNotFoundError("❌ Tidak ada MP3 di Drive!")

mp3_file = mp3_files[0]
mp3_name_safe = mp3_file['title']
mp3_local = os.path.join(TMP_FOLDER, mp3_name_safe)
mp3_file.GetContentFile(mp3_local)
print("🎵 MP3:", mp3_name_safe)

# Filter background (ambil 1 random atau fallback hitam)
bg_files = [f for f in file_list if f['title'].lower().endswith(('.jpg', '.png'))]
if bg_files:
    bg_file = random.choice(bg_files)
    bg_name_safe = bg_file['title']
    bg_local = os.path.join(TMP_FOLDER, bg_name_safe)
    bg_file.GetContentFile(bg_local)
    print("🖼️ Background:", bg_name_safe)
else:
    bg_local = os.path.join(TMP_FOLDER, "bg_black.jpg")
    os.system(f'ffmpeg -f lavfi -i color=c=black:s=1920x1080 -frames:v 1 "{bg_local}"')
    print("⚠️ Background tidak ditemukan, pakai hitam.")

# Output video
output_video = os.path.splitext(mp3_name_safe)[0] + "_rainbow.mp4"
output_local = os.path.join(TMP_FOLDER, output_video)

# Render visualizer spectrum pelangi
filter_complex = (
    '[0:a]showwaves=s=1920x400:mode=line:colors=red|orange|yellow|green|blue|violet[viz];'
    '[1:v][viz]overlay=x=0:y=main_h-400:format=auto[outv]'
)

ffmpeg.input(mp3_local).output(
    ffmpeg.input(bg_local),
    output_local,
    vcodec='libx264',
    preset='ultrafast',
    pix_fmt='yuv420p',
    filter_complex=filter_complex,
    shortest=None,
    map='[outv]',
    map0=0
).run(overwrite_output=True)

print("✅ Video berhasil dibuat:", output_local)

# Upload hasil ke Drive
file_drive = drive.CreateFile({'title': output_video, 'parents':[{'id': DRIVE_FOLDER_ID}]})
file_drive.SetContentFile(output_local)
file_drive.Upload()
print("📼 Video berhasil diupload ke Drive!")

# Hapus folder sementara
shutil.rmtree(TMP_FOLDER)
