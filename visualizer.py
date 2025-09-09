import os
import random
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import subprocess
import shutil

# ===== CONFIG =====
DRIVE_FOLDER_ID = "ID_FOLDER_DRIVE"  # ganti dengan folder Drive yang berisi MP3 & background
TMP_FOLDER = "tmp_files"
os.makedirs(TMP_FOLDER, exist_ok=True)
# ==================

# Autentikasi Drive
gauth = GoogleAuth()
gauth.LoadClientConfigFile("credentials.json")
# Token pertama kali akan tetap minta browser. Setelah itu disimpan sebagai mycreds.txt
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# Ambil semua file di folder
file_list = drive.ListFile({'q': f"'{DRIVE_FOLDER_ID}' in parents and trashed=false"}).GetList()

# Ambil MP3 (1 file panjang)
mp3_files = [f for f in file_list if f['title'].lower().endswith('.mp3')]
if not mp3_files:
    raise FileNotFoundError("❌ Tidak ada MP3 di Drive!")

mp3_file = mp3_files[0]
mp3_local = os.path.join(TMP_FOLDER, mp3_file['title'])
mp3_file.GetContentFile(mp3_local)
print("🎵 MP3:", mp3_file['title'])

# Ambil background (random jpg/png) atau fallback hitam
bg_files = [f for f in file_list if f['title'].lower().endswith(('.jpg', '.png'))]
if bg_files:
    bg_file = random.choice(bg_files)
    bg_local = os.path.join(TMP_FOLDER, bg_file['title'])
    bg_file.GetContentFile(bg_local)
    print("🖼️ Background:", bg_file['title'])
else:
    bg_local = os.path.join(TMP_FOLDER, "bg_black.jpg")
    subprocess.run(f'ffmpeg -f lavfi -i color=c=black:s=1920x1080 -frames:v 1 "{bg_local}"', shell=True)
    print("⚠️ Background hitam dibuat")

# Output video
output_video = os.path.splitext(mp3_file['title'])[0] + "_rainbow.mp4"
output_local = os.path.join(TMP_FOLDER, output_video)

# Render visualizer
filter_complex = (
    '[0:a]showwaves=s=1920x400:mode=line:colors=red|orange|yellow|green|blue|violet[viz];'
    '[1:v][viz]overlay=x=0:y=main_h-400:format=auto[outv]'
)

subprocess.run(
    f'ffmpeg -i "{mp3_local}" -loop 1 -i "{bg_local}" -filter_complex "{filter_complex}" '
    f'-map "[outv]" -map 0:a -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a copy -shortest "{output_local}"',
    shell=True
)
print("✅ Video dibuat:", output_local)

# Upload hasil ke Drive
file_drive = drive.CreateFile({'title': output_video, 'parents':[{'id': DRIVE_FOLDER_ID}]})
file_drive.SetContentFile(output_local)
file_drive.Upload()
print("📼 Video berhasil diupload ke Drive!")

# Hapus folder sementara
shutil.rmtree(TMP_FOLDER)
