import os
import random
import ffmpeg
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import shutil

# ===== CONFIG =====
DRIVE_FOLDER_ID = "FOLDER_ID_DI_DRIVE"  # folder Drive tempat MP3 & background
# ==================

# Autentikasi Google Drive
gauth = GoogleAuth()
gauth.LoadCredentialsFile("credentials.json")
if gauth.credentials is None:
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()
gauth.SaveCredentialsFile("credentials.json")
drive = GoogleDrive(gauth)

# Buat folder sementara
tmp_folder = "tmp_files"
os.makedirs(tmp_folder, exist_ok=True)

# 1️⃣ Ambil semua file di folder Drive
file_list = drive.ListFile({'q': f"'{DRIVE_FOLDER_ID}' in parents and trashed=false"}).GetList()

# Filter MP3
mp3_files = [f for f in file_list if f['title'].lower().endswith('.mp3')]
if not mp3_files:
    raise FileNotFoundError("❌ Tidak ada MP3 ditemukan di Drive!")

# Pilih satu MP3 random
mp3_file = random.choice(mp3_files)
mp3_name_safe = mp3_file['title']
mp3_local = os.path.join(tmp_folder, mp3_name_safe)
mp3_file.GetContentFile(mp3_local)
print("🎵 MP3:", mp3_name_safe)

# Filter background image
bg_files = [f for f in file_list if f['title'].lower().endswith(('.jpg', '.png'))]
if bg_files:
    bg_file = random.choice(bg_files)
    bg_name_safe = bg_file['title']
    bg_local = os.path.join(tmp_folder, bg_name_safe)
    bg_file.GetContentFile(bg_local)
    print("🖼️ Background:", bg_name_safe)
else:
    bg_local = os.path.join(tmp_folder, "bg_black.jpg")
    os.system(f'ffmpeg -f lavfi -i color=c=black:s=1920x1080 -frames:v 1 "{bg_local}"')
    print("⚠️ Background tidak ditemukan, pakai hitam.")

# Output video
output_video = os.path.splitext(mp3_name_safe)[0] + "_rainbow.mp4"
output_local = os.path.join(tmp_folder, output_video)

# 2️⃣ Render visualizer spectrum/line pelangi
# Gunakan showwaves mode=line
filter_complex = (
    '[0:a]showwaves=s=1920x400:mode=line:colors=red|orange|yellow|green|blue|violet[viz];'
    '[1:v][viz]overlay=x=0:y=main_h-400:format=auto[outv]'
)

ffmpeg_cmd = (
    ffmpeg.input(mp3_local)
    .output(ffmpeg.input(bg_local), output_local,
            vcodec='libx264', preset='ultrafast', pix_fmt='yuv420p',
            filter_complex=filter_complex, shortest=None, map='[outv]', map0=0)
)
ffmpeg_cmd.run(overwrite_output=True)
print("✅ Video berhasil dibuat:", output_local)

# 3️⃣ Upload ke Drive
file_drive = drive.CreateFile({'title': output_video, 'parents':[{'id': DRIVE_FOLDER_ID}]})
file_drive.SetContentFile(output_local)
file_drive.Upload()
print("📼 Video berhasil diupload ke Drive!")

# Hapus folder sementara
shutil.rmtree(tmp_folder)
