import requests, os
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from moviepy.editor import AudioFileClip, ImageClip

VIDEO_WIDTH  = 1080
VIDEO_HEIGHT = 1920
FPS          = 30
FONT_AR_PATH = "fonts/Amiri-Regular.ttf"
FONT_EN_PATH = "fonts/DejaVuSans.ttf"

def get_ayah_data(surah, ayah):
    ar = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/ar.alafasy", timeout=15).json()
    en = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.asad", timeout=15).json()
    return {
        "arabic": ar["data"]["text"],
        "english": en["data"]["text"],
        "surah_name": ar["data"]["surah"]["name"],
        "surah_name_en": ar["data"]["surah"]["englishName"],
        "ayah_number": ar["data"]["numberInSurah"],
        "surah_number": surah,
    }

def fix_arabic(text):
    return get_display(arabic_reshaper.reshape(text))

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        w = draw.textbbox((0,0), test, font=font)[2]
        if w > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines

def shadow(draw, pos, text, font, fill, sc=(0,0,0,180), o=3):
    x, y = pos
    draw.text((x+o, y+o), text, font=font, fill=sc)
    draw.text((x, y), text, font=font, fill=fill)

def create_frame(ayah_data, bg_path="assets/background.jpg"):
    if os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGBA").resize((VIDEO_WIDTH, VIDEO_HEIGHT))
    else:
        bg = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (15,15,30,255))
    overlay = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0,0,0,130))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)
    try:
        far_big = ImageFont.truetype(FONT_AR_PATH, 72)
        far_med = ImageFont.truetype(FONT_AR_PATH, 48)
        far_sm  = ImageFont.truetype(FONT_AR_PATH, 38)
        fen_med = ImageFont.truetype(FONT_EN_PATH, 36)
        fen_sm  = ImageFont.truetype(FONT_EN_PATH, 28)
    except:
        far_big = far_med = far_sm = fen_med = fen_sm = ImageFont.load_default()
    margin, cx = 80, VIDEO_WIDTH//2
    bism = fix_arabic("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
    bw = draw.textbbox((0,0), bism, font=far_sm)[2]
    shadow(draw, (cx-bw//2, 120), bism, far_sm, (255,215,100,255))
    draw.line([(margin,210),(VIDEO_WIDTH-margin,210)], fill=(255,215,100,150), width=2)
    sl = fix_arabic(f"سورة {ayah_data['surah_name']} — الآية {ayah_data['ayah_number']}")
    slw = draw.textbbox((0,0), sl, font=far_med)[2]
    shadow(draw, (cx-slw//2, 250), sl, far_med, (255,230,150,255))
    ar_lines = wrap_text(fix_arabic(ayah_data["arabic"]), far_big, VIDEO_WIDTH-margin*2, draw)
    lh = 90
    sy = (VIDEO_HEIGHT//2) - (len(ar_lines)*lh//2) - 80
    for i, line in enumerate(ar_lines):
        lw = draw.textbbox((0,0), line, font=far_big)[2]
        shadow(draw, (cx-lw//2, sy+i*lh), line, far_big, (255,255,255,255))
    sep_y = sy + len(ar_lines)*lh + 40
    draw.line([(margin+80,sep_y),(VIDEO_WIDTH-margin-80,sep_y)], fill=(255,215,100,120), width=1)
    en_lines = wrap_text(f'"{ayah_data["english"]}"', fen_med, VIDEO_WIDTH-margin*2, draw)
    for i, line in enumerate(en_lines):
        lw = draw.textbbox((0,0), line, font=fen_med)[2]
        shadow(draw, (cx-lw//2, sep_y+30+i*50), line, fen_med, (200,220,255,220))
    ref = f"Surah {ayah_data['surah_name_en']} [{ayah_data['surah_number']}:{ayah_data['ayah_number']}]"
    rw = draw.textbbox((0,0), ref, font=fen_sm)[2]
    draw.text((cx-rw//2, VIDEO_HEIGHT-160), ref, font=fen_sm, fill=(180,180,220,200))
    tags = "#Quran #Islam #QuranShorts #قرآن #إسلام"
    tw = draw.textbbox((0,0), tags, font=fen_sm)[2]
    draw.text((cx-tw//2, VIDEO_HEIGHT-110), tags, font=fen_sm, fill=(150,180,200,180))
    tmp = "temp_frame.png"
    bg.convert("RGB").save(tmp)
    return tmp

def generate_video(ayah_data, audio_path, output_path="output_video.mp4"):
    audio = AudioFileClip(audio_path)
    dur   = audio.duration + 1.5
    frame = create_frame(ayah_data)
    clip  = ImageClip(frame).set_duration(dur).set_fps(FPS).set_audio(audio)
    clip.write_videofile(output_path, fps=FPS, codec="libx264", audio_codec="aac", preset="fast", threads=4, logger=None)
    if os.path.exists(frame):
        os.remove(frame)
    print(f"[OK] تم انشاء الفيديو: {output_path}")
    return output_path
