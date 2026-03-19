import requests, os, random, subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from moviepy.editor import AudioFileClip, VideoFileClip, CompositeVideoClip, TextClip

VIDEO_WIDTH  = 1080
VIDEO_HEIGHT = 1920
FPS          = 30
FONT_AR_PATH = "fonts/Amiri-Regular.ttf"
FONT_EN_PATH = "fonts/DejaVuSans.ttf"
PEXELS_KEY   = "agiQsdsM9GHC0XFD91gaX2611yzowQLOi2eeKep8baYsObL7N0MdP5e0"

NATURE_QUERIES = [
    "waterfall nature", "forest trees", "ocean waves",
    "sunset sky", "river stream", "mountains nature",
    "rain nature", "clouds sky", "desert sand", "flowers nature"
]

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

def download_nature_video(duration_needed):
    query = random.choice(NATURE_QUERIES)
    print(f"[Pexels] جاري جلب فيديو: {query}")
    headers = {"Authorization": PEXELS_KEY}
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers=headers,
        params={"query": query, "per_page": 15, "orientation": "portrait"},
        timeout=15
    ).json()

    videos = r.get("videos", [])
    random.shuffle(videos)

    for video in videos:
        for vf in video.get("video_files", []):
            if vf.get("quality") in ["hd", "sd"] and vf.get("width", 0) >= 720:
                url = vf["link"]
                out = "temp_bg.mp4"
                print(f"[Pexels] تنزيل الفيديو...")
                resp = requests.get(url, timeout=60, stream=True)
                with open(out, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"[Pexels] تم التنزيل!")
                return out

    return None

def fix_arabic(text):
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        try:
            w = draw.textlength(test, font=font)
        except:
            w = draw.textbbox((0,0), test, font=font)[2]
        if w > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines

def create_overlay(ayah_data):
    img = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0,0,0,0))
    draw = ImageDraw.Draw(img)

    try:
        far_big = ImageFont.truetype(FONT_AR_PATH, 72)
        far_med = ImageFont.truetype(FONT_AR_PATH, 50)
        far_sm  = ImageFont.truetype(FONT_AR_PATH, 38)
        fen_med = ImageFont.truetype(FONT_EN_PATH, 32)
        fen_sm  = ImageFont.truetype(FONT_EN_PATH, 24)
    except:
        far_big = far_med = far_sm = fen_med = fen_sm = ImageFont.load_default()

    gold  = (255, 215, 80, 255)
    white = (255, 255, 255, 255)
    gray  = (200, 220, 255, 210)
    cx    = VIDEO_WIDTH // 2
    margin = 80
    max_w  = VIDEO_WIDTH - margin * 2

    # طبقة شبه شفافة في المنتصف
    overlay = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0,0,0,0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.rectangle([0, VIDEO_HEIGHT//2 - 500, VIDEO_WIDTH, VIDEO_HEIGHT//2 + 600], fill=(0,0,0,150))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    def shadow(pos, text, font, fill):
        x, y = pos
        draw.text((x+3, y+3), text, font=font, fill=(0,0,0,200))
        draw.text((x, y), text, font=font, fill=fill)

    # بسم الله
    bism = fix_arabic("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
    try:
        bw = int(draw.textlength(bism, font=far_sm))
    except:
        bw = draw.textbbox((0,0), bism, font=far_sm)[2]
    shadow((cx - bw//2, VIDEO_HEIGHT//2 - 480), bism, far_sm, gold)

    # خط ذهبي
    draw.line([(margin, VIDEO_HEIGHT//2 - 410), (VIDEO_WIDTH-margin, VIDEO_HEIGHT//2 - 410)], fill=(255,215,80,180), width=2)

    # اسم السورة
    sl = fix_arabic(f"سورة {ayah_data['surah_name']} — الآية {ayah_data['ayah_number']}")
    try:
        slw = int(draw.textlength(sl, font=far_med))
    except:
        slw = draw.textbbox((0,0), sl, font=far_med)[2]
    shadow((cx - slw//2, VIDEO_HEIGHT//2 - 370), sl, far_med, gold)

    # نص الآية العربية
    ar_lines = wrap_text(fix_arabic(ayah_data["arabic"]), far_big, max_w, draw)
    lh = 95
    total_h = len(ar_lines) * lh
    start_y = VIDEO_HEIGHT//2 - total_h//2 + 20
    for i, line in enumerate(ar_lines):
        try:
            lw = int(draw.textlength(line, font=far_big))
        except:
            lw = draw.textbbox((0,0), line, font=far_big)[2]
        shadow((cx - lw//2, start_y + i*lh), line, far_big, white)

    # خط فاصل
    sep_y = start_y + total_h + 30
    draw.line([(margin+60, sep_y), (VIDEO_WIDTH-margin-60, sep_y)], fill=(255,215,80,120), width=1)

    # الترجمة
    en_lines = wrap_text(f'"{ayah_data["english"]}"', fen_med, max_w, draw)
    for i, line in enumerate(en_lines):
        try:
            lw = int(draw.textlength(line, font=fen_med))
        except:
            lw = draw.textbbox((0,0), line, font=fen_med)[2]
        shadow((cx - lw//2, sep_y + 25 + i*45), line, fen_med, gray)

    # المرجع
    ref = f"Surah {ayah_data['surah_name_en']} [{ayah_data['surah_number']}:{ayah_data['ayah_number']}]"
    try:
        rw = int(draw.textlength(ref, font=fen_sm))
    except:
        rw = draw.textbbox((0,0), ref, font=fen_sm)[2]
    draw.text((cx - rw//2, VIDEO_HEIGHT - 180), ref, font=fen_sm, fill=(200,200,220,200))

    # هاشتاقات
    tags = "#Quran #Islam #QuranShorts #قرآن #إسلام"
    try:
        tw = int(draw.textlength(tags, font=fen_sm))
    except:
        tw = draw.textbbox((0,0), tags, font=fen_sm)[2]
    draw.text((cx - tw//2, VIDEO_HEIGHT - 140), tags, font=fen_sm, fill=(150,180,200,180))

    tmp = "temp_overlay.png"
    img.save(tmp)
    return tmp

def generate_video(ayah_data, audio_path, output_path="output_video.mp4"):
    from moviepy.editor import AudioFileClip, VideoFileClip, ImageClip, CompositeVideoClip

    audio = AudioFileClip(audio_path)
    duration = audio.duration + 2.0

    # تنزيل فيديو الطبيعة
    bg_video_path = download_nature_video(duration)

    if bg_video_path and os.path.exists(bg_video_path):
        # استخدام فيديو الطبيعة كخلفية
        bg = VideoFileClip(bg_video_path)

        # تكرار الفيديو لو أقصر من المطلوب
        if bg.duration < duration:
            from moviepy.editor import concatenate_videoclips
            repeats = int(duration / bg.duration) + 1
            bg = concatenate_videoclips([bg] * repeats)

        bg = bg.subclip(0, duration)

        # تغيير الحجم لـ 9:16
        bg_ratio = bg.w / bg.h
        target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
        if bg_ratio > target_ratio:
            bg = bg.resize(height=VIDEO_HEIGHT)
            x_center = bg.w / 2
            bg = bg.crop(x1=x_center - VIDEO_WIDTH/2, x2=x_center + VIDEO_WIDTH/2)
        else:
            bg = bg.resize(width=VIDEO_WIDTH)
            y_center = bg.h / 2
            bg = bg.crop(y1=y_center - VIDEO_HEIGHT/2, y2=y_center + VIDEO_HEIGHT/2)

        bg = bg.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
    else:
        # خلفية سوداء لو فشل التنزيل
        from moviepy.editor import ColorClip
        bg = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(15,15,30), duration=duration)

    # إنشاء الـ overlay
    overlay_path = create_overlay(ayah_data)
    overlay = ImageClip(overlay_path).set_duration(duration)

    # دمج الفيديو والـ overlay والصوت
    final = CompositeVideoClip([bg, overlay]).set_audio(audio)
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        threads=4,
        logger=None
    )

    # تنظيف
    for f in [overlay_path, bg_video_path]:
        if f and os.path.exists(f):
            os.remove(f)

    print(f"[OK] تم انشاء الفيديو: {output_path}")
    return output_path
