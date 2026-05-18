import os
import sys
from pathlib import Path
import yt_dlp


def select_quality():
    quality_options = {
        '1': ('bestaudio/best', 320, 'Mejor calidad disponible'),
        '2': ('bestaudio[brate>=320]/bestvideo[ext=m4a]/best', 320, 'Máxima (320 kbps)'),
        '3': ('worstaudio/best', 96, 'Mínima'),
    }

    print("\nSeleccione la calidad de audio:")
    print("1. Mejorable disponible")
    print("2. Máxima (320 kbps)")
    print("3. Mínima (96 kbps)")

    while True:
        choice = input("\nOpción [1-3]: ").strip()
        if choice in quality_options:
            return quality_options[choice]
        print("Por favor ingrese una opción válida (1-3).")


def get_output_path():
    dir = Path.cwd() / "descargas"
    dir.mkdir(exist_ok=True)
    return str(dir)


def download_audio(url, quality='bestaudio/best', use_cookies=False, output_dir=None):
    output_template = os.path.join(output_dir or get_output_path(), '%(title)s.%(ext)s')

    ydl_opts = {
        'format': quality,
        'outtmpl': output_template,
        'extract_audio': True,
        'audio_format': 'mp3',
        'progress_hooks': [download_progress],
        'quiet': False,
        'no_warnings': False,
        'js_runtimes': {'node': {}},
        'remote_components': ['ejs:github'],
    }

    if use_cookies:
        cookies_file = Path.cwd() / 'cookies.txt'
        if cookies_file.exists():
            ydl_opts['cookiefile'] = str(cookies_file)
        else:
            try:
                ydl_opts['cookiesfrombrowser'] = ('firefox',)
            except Exception:
                pass

    try:
        print(f"\nDescargando desde: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("\n¡Descarga completada!")
    except Exception as e:
        print(f"\nError durante la descarga: {e}")
        sys.exit(1)


def download_progress(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()

        sys.stdout.write(f"\rDescargando: {percent} | Velocidad: {speed} | ETA: {eta}")
        sys.stdout.flush()

    elif d['status'] == 'finished':
        sys.stdout.write("\rProcesando...")
        sys.stdout.flush()


def main():
    if len(sys.argv) >= 3:
        url = sys.argv[1]
        quality_idx = int(sys.argv[2])
        use_cookies = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True

        quality_options = {
            1: ('bestaudio/best', 320),
            2: ('bestaudio[brate>=320]/bestvideo[ext=m4a]/best', 320),
            3: ('worstaudio/best', 96),
        }

        if quality_idx not in quality_options:
            print("Índice de calidad inválido (1-3).")
            sys.exit(1)

        quality_setting, bitrate = quality_options[quality_idx]
        descriptions = {1: 'Mejor calidad disponible', 2: 'Máxima (320 kbps)', 3: 'Mínima'}
        print(f"\nCalidad seleccionada: {descriptions[quality_idx]} ({bitrate} kbps)")

        download_audio(url, quality_setting, use_cookies)
        return

    print("=" * 50)
    print("YouTube Audio Downloader")
    print("=" * 50)

    url = input("\nIngrese el URL del video o playlist: ").strip()
    if not url:
        print("URL inválida.")
        sys.exit(1)

    quality_setting, bitrate, description = select_quality()
    print(f"\nCalidad seleccionada: {description} ({bitrate} kbps)")

    download_audio(url, quality_setting, True)


if __name__ == '__main__':
    main()
