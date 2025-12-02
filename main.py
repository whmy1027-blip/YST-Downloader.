import flet as ft
import yt_dlp
import os
from pathlib import Path
import threading
from datetime import datetime

class YSTDownloader:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        self.setup_ui()
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
    
    def setup_page(self):
        """إعدادات الصفحة"""
        self.page.title = "YST Downloader 🚀"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 20
        self.page.bgcolor = "#0f0f23"
        self.page.window.width = 800
        self.page.window.height = 700
        self.page.window.resizable = True
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        
        # العنوان الرئيسي
        self.title = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.DOWNLOAD, color=ft.colors.BLUE_400, size=30),
                ft.Column([
                    ft.Text("YST DOWNLOADER", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                    ft.Text("Download YouTube Videos & MP3", size=14, color=ft.colors.BLUE_200)
                ])
            ]),
            margin=ft.margin.only(bottom=30)
        )
        
        # حقل إدخال الرابط
        self.url_input = ft.TextField(
            label="🎬 Enter YouTube URL",
            hint_text="https://www.youtube.com/watch?v=...",
            width=600,
            border_color=ft.colors.BLUE_400,
            prefix_icon=ft.icons.LINK,
            filled=True,
            bgcolor=ft.colors.GREY_900,
            on_submit=lambda e: self.start_download("720p")
        )
        
        # أزرار الجودة
        self.quality_buttons = ft.Row([
            self.create_quality_button("360p", ft.colors.BLUE_600),
            self.create_quality_button("480p", ft.colors.BLUE_700),
            self.create_quality_button("720p", ft.colors.GREEN_600),
            self.create_quality_button("1080p", ft.colors.GREEN_700),
            self.create_quality_button("MP3", ft.colors.PURPLE_600),
            self.create_quality_button("Playlist", ft.colors.ORANGE_600),
        ], wrap=True, spacing=10)
        
        # معلومات التحميل
        self.progress_bar = ft.ProgressBar(
            width=600,
            height=10,
            color=ft.colors.BLUE_400,
            bgcolor=ft.colors.GREY_800,
            visible=False
        )
        
        self.status_text = ft.Text(
            "🔵 Ready to download...",
            size=16,
            color=ft.colors.GREEN_400
        )
        
        self.file_info = ft.Text("", size=14, color=ft.colors.GREY_400)
        
        # قائمة الملفات المحملة
        self.downloads_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20
        )
        
        # زر عرض الملفات
        self.show_files_btn = ft.ElevatedButton(
            "📁 Show Downloaded Files",
            on_click=self.show_downloaded_files,
            icon=ft.icons.FOLDER_OPEN
        )
        
        # بناء الواجهة
        self.page.add(
            ft.Column([
                self.title,
                ft.Divider(),
                self.url_input,
                ft.Container(height=20),
                self.quality_buttons,
                ft.Container(height=20),
                self.progress_bar,
                self.status_text,
                self.file_info,
                ft.Container(height=30),
                ft.Text("📂 Downloaded Files:", size=18, color=ft.colors.BLUE_400),
                self.show_files_btn,
                ft.Container(
                    content=self.downloads_list,
                    height=200,
                    border=ft.border.all(1, ft.colors.GREY_700),
                    border_radius=10,
                    padding=10
                )
            ], scroll=ft.ScrollMode.ADAPTIVE)
        )
        
        # تحميل قائمة الملفات أول مرة
        self.show_downloaded_files(None)
    
    def create_quality_button(self, text, color):
        """إنشاء زر جودة"""
        return ft.ElevatedButton(
            text,
            on_click=lambda e: self.start_download(text),
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=color,
                padding=15
            )
        )
    
    def start_download(self, quality):
        """بدء عملية التحميل"""
        url = self.url_input.value.strip()
        
        if not url:
            self.show_message("⚠️ Please enter a YouTube URL", ft.colors.ORANGE)
            return
        
        # تحديث الواجهة
        self.progress_bar.visible = True
        self.status_text.value = f"⏬ Downloading {quality}..."
        self.status_text.color = ft.colors.BLUE_400
        self.file_info.value = "Processing request..."
        self.page.update()
        
        # تشغيل التحميل في thread منفصل
        threading.Thread(
            target=self.download_video,
            args=(url, quality),
            daemon=True
        ).start()
    
    def download_video(self, url, quality):
        """عملية التحميل الحقيقية"""
        try:
            # إعدادات yt-dlp
            if quality == "MP3":
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f'{self.downloads_dir}/%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [self.progress_hook],
                }
            elif quality == "Playlist":
                ydl_opts = {
                    'format': 'best[height<=720]',
                    'outtmpl': f'{self.downloads_dir}/%(playlist_title)s/%(title)s.%(ext)s',
                    'ignoreerrors': True,
                    'progress_hooks': [self.progress_hook],
                }
            else:
                quality_map = {
                    "360p": "360",
                    "480p": "480", 
                    "720p": "720",
                    "1080p": "1080"
                }
                ydl_opts = {
                    'format': f'best[height<={quality_map[quality]}]',
                    'outtmpl': f'{self.downloads_dir}/%(title)s.%(ext)s',
                    'progress_hooks': [self.progress_hook],
                }
            
            # التحميل الحقيقي
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # الحصول على معلومات الفيديو
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'Unknown Video')
                
                self.file_info.value = f"📥 Downloading: {video_title}"
                self.page.update()
                
                # البدء في التحميل
                ydl.download([url])
            
            # التحميل نجح
            self.status_text.value = f"✅ Download completed ({quality})"
            self.status_text.color = ft.colors.GREEN_400
            self.file_info.value = f"✅ Saved: {video_title}"
            
            # إشعار النجاح
            self.show_message(f"🎉 Successfully downloaded: {video_title}", ft.colors.GREEN)
            
            # تحديث قائمة الملفات
            self.show_downloaded_files(None)
            
        except Exception as e:
            # في حالة خطأ
            self.status_text.value = f"❌ Download failed"
            self.status_text.color = ft.colors.RED_400
            self.file_info.value = f"Error: {str(e)}"
            
            self.show_message(f"❌ Error: {str(e)}", ft.colors.RED)
            
        finally:
            self.progress_bar.visible = False
            self.page.update()
    
    def progress_hook(self, d):
        """تتبع تقدم التحميل"""
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 1)
            
            if total > 0:
                percent = (downloaded / total) * 100
                speed = d.get('speed', 0)
                
                # تحديث شريط التقدم
                self.progress_bar.value = percent / 100
                
                # عرض معلومات التحميل
                speed_mb = speed / (1024 * 1024) if speed else 0
                self.file_info.value = f"⬇️ {percent:.1f}% | Speed: {speed_mb:.1f} MB/s"
                self.page.update()
    
    def show_downloaded_files(self, e):
        """عرض الملفات المحملة"""
        self.downloads_list.controls.clear()
        
        # الحصول على جميع الملفات
        files = []
        for ext in ['*.mp4', '*.mp3', '*.webm', '*.mkv']:
            files.extend(self.downloads_dir.glob(ext))
        
        if files:
            # ترتيب الملفات حسب تاريخ التعديل
            files = sorted(files, key=os.path.getmtime, reverse=True)
            
            for file in files[:10]:  # عرض آخر 10 ملفات
                file_size = file.stat().st_size / (1024 * 1024)  # MB
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                time_str = file_time.strftime("%Y-%m-%d %H:%M")
                
                # اختصار اسم الملف إذا كان طويلاً
                display_name = file.name
                if len(display_name) > 30:
                    display_name = display_name[:27] + "..."
                
                # إضافة الملف للقائمة
                self.downloads_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(
                            ft.icons.AUDIO_FILE if file.suffix == '.mp3' else ft.icons.VIDEO_FILE,
                            color=ft.colors.BLUE_400
                        ),
                        title=ft.Text(display_name, size=14),
                        subtitle=ft.Text(f"{file_size:.2f} MB | {time_str}", size=12),
                        trailing=ft.IconButton(
                            icon=ft.icons.FOLDER_OPEN,
                            tooltip="Open folder",
                            on_click=lambda e, f=file: self.open_file_folder(f)
                        )
                    )
                )
        else:
            self.downloads_list.controls.append(
                ft.Text("No downloads yet. Start downloading videos!", 
                       size=16, color=ft.colors.GREY_500)
            )
        
        self.page.update()
    
    def open_file_folder(self, file_path):
        """فتح مجلد الملف"""
        import platform
        import subprocess
        
        try:
            system = platform.system()
            
            if system == "Windows":
                os.startfile(file_path.parent)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path.parent])
            else:  # Linux
                subprocess.run(["xdg-open", file_path.parent])
                
            self.show_message("📂 Opened downloads folder", ft.colors.BLUE)
            
        except Exception as e:
            self.show_message(f"❌ Could not open folder: {str(e)}", ft.colors.RED)
    
    def show_message(self, message, color):
        """عرض رسالة للمستخدم"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.colors.WHITE),
            bgcolor=color,
            action="OK",
            action_color=ft.colors.WHITE
        )
        self.page.snack_bar.open = True
        self.page.update()

def main(page: ft.Page):
    app = YSTDownloader(page)

# تشغيل التطبيق
if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.FLET_APP,
        assets_dir="assets"
    )
