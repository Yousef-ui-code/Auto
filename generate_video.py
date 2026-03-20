import requests, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display
import arabic_reshaper
from moviepy.editor import AudioFileClip, VideoFileClip, ImageClip, CompositeVideoClip, ColorClip, concatenate_videoclips, concatenate_audioclips
from moviepy.audio.AudioClip import AudioArrayClip

VIDEO_WIDTH  = 1080
VIDEO_HEIGHT = 1920
FPS          = 30
TARGET_DUR   = 59.0
FONT_AR_PATH = "fonts/Amiri-Regular.ttf"
FONT_EN_PATH = "fonts/DejaVuSans.ttf"
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY", "agiQsdsM9GHC0XFD91gaX2611yzowQLOi2eeKep8baYsObL7N0MdP5e0")

NATURE_QUERIES = [
    "waterfall nature","forest trees","ocean waves","sunset sky",
    "river stream","mountains nature","rain nature","clouds sky",
    "desert sand","flowers nature","green nature","lake reflection",
    "sunrise nature","snow mountains"
]

SURAH_LENGTHS = {
    1:7,2:286,3:200,4:176,5:120,6:165,7:206,8:75,9:129,10:109,
    11:123,12:111,13:43,14:52,15:99,16:128,17:111,18:110,19:98,
    20:135,21:112,22:78,23:118,24:64,25:77,26:227,27:93,28:88,
    29:69,30:60,31:34,32:30,33:73,34:54,35:45,36:83,37:182,
    38:88,39:75,40:85,41:54,42:53,43:89,44:59,45:37,46:35,
    47:38,48:29,49:18,50:45,51:60,52:49,53:62,54:55,55:78,
    56:96,57:29,58:22,59:24,60:13,61:14,62:11,63:11,64:18,
    65:12,66:12,67:30,68:52,69:52,70:44,71:28,72:28,73:20,
    74:56,75:40,76:31,77:50,78:40,79:46,80:42,81:29,82:19,
    83:36,84:25,85:22,86:17,87:19,88:26,89:30,90:20,91:15,
    92:21,93:11,94:8,95:8,96:19,97:5,98:8,99:8,100:11,
    101:11,102:8,103:3,104:9,105:5,106:4,107:7,108:3,109:6,
    110:3,111:5,112:4,113:5,114:6,
}

def next_ayah_ref(surah, ayah):
    ayah += 1
    if ayah > SURAH_LENGTHS.get(surah, 7):
        surah += 1
        ayah = 1
    if surah > 114:
        surah = 1
        ayah = 1
    return surah, ayah

def get_ayah_data(surah, ayah):
    ar = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/ar.alafasy", timeout=15).json()
    en = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.asad", timeout=15).json()
    return {
        "arabic":       ar["data"]["text"],
        "english":      en["data"]["text"],
        "surah_name":   ar["data"]["surah"]["name"],
        "surah_name_en": ar["data"]["surah"]["englishName"],
        "ayah_number":  ar["data"]["numberInSurah"],
        "surah_number": surah,
    }

def download_audio_ayah(surah, ayah):
    path = f"temp_ayah_{surah}_{ayah}.mp3"
    url  = f"https://everyayah.com/data/Alafasy_128kbps/{str(surah).zfill(3)}{str(ayah).zfill(3)}.mp3"
    r = requests.get(url, timeout=30)
    with open(path, "wb") as f:
        f.write(r.content)
    return path

def collect_ayahs(start_surah, start_ayah):
    """يجمع آيات متتالية لحد ما يوصل 59 ثانية"""
    clips    = []
    ayahs    = []
    total    = 0.0
    surah, ayah = start_surah, start_ayah

    while total < TARGET_DUR:
        try:
            print(f"[audio] جاري تنزيل سورة {surah} آية {ayah}...")
            ap = download_audio_ayah(surah, ayah)
            ac = AudioFileClip(ap)
            dur = ac.duration

            if total + dur > TARGET_DUR and clips:
                os.remove(ap)
                break

            clips.append(ac)
            ayahs.append({"surah": surah, "ayah": ayah, "path": ap})
            total += dur
            print(f"[audio] إجمالي: {total:.1f}s")

            surah, ayah = next_ayah_ref(surah, ayah)

        except Exception as e:
            print(f"[audio] خطأ في سورة {surah} آية {ayah}: {e}")
            surah, ayah = next_ayah_ref(surah, ayah)
            continue

    # دمج الصوت
    if not clips:
        return None, [], start_surah, start_ayah

    combined = concatenate_audioclips(clips)

    # لو أقل من 59 ثانية — نضيف صمت
    if combined.duration < TARGET_DUR:
        silence_dur = TARGET_DUR - combined.duration
        silence_arr = np.zeros((int(silence_dur * 44100), 2))
        silence     = AudioArrayClip(silence_arr, fps=44100)
        combined    = concatenate_audioclips([combined, silence])

    combined = combined.subclip(0, TARGET_DUR)

    return combined, ayahs, surah, ayah

def fix_ar(text):
    try:
        return arabic_reshaper.reshape(text)
    except:
        return text

def tw(draw, text, font):
    try:
        return int(draw.textlength(text, font=font))
    except:
        return draw.textbbox((0,0), text, font=font)[2]

def sh(draw, pos, text, font, fill):
    x, y = pos
    draw.text((x+4, y+4), text, font=font, fill=(0,0,0,230))
    draw.text((x,   y  ), text, font=font, fill=fill)

def create_overlay(ayahs_data):
    """يعرض كل الآيات في الفيديو"""
    img  = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0,0,0,0))
    dark = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0,0,0,120))
    img  = Image.alpha_composite(img, dark)
    draw = ImageDraw.Draw(img)

    try:
        far_big = ImageFont.truetype(FONT_AR_PATH, 72)
        far_med = ImageFont.truetype(FONT_AR_PATH, 50)
        far_sm  = ImageFont.truetype(FONT_AR_PATH, 36)
        fen_med = ImageFont.truetype(FONT_EN_PATH, 30)
        fen_sm  = ImageFont.truetype(FONT_EN_PATH, 24)
    except:
        far_big = far_med = far_sm = fen_med = fen_sm = ImageFont.load_default()

    gold  = (255, 210, 70,  255)
    white = (255, 255, 255, 255)
    lgray = (200, 220, 255, 200)
    cx    = VIDEO_WIDTH // 2
    mg    = 70
    mw    = VIDEO_WIDTH - mg * 2

    def wrap(text, font):
        words = text.split()
        lines, cur = [], []
        for w in words:
            test = " ".join(cur + [w])
            if tw(draw, test, font) > mw and cur:
                lines.append(" ".join(cur))
                cur = [w]
            else:
                cur.append(w)
        if cur:
            lines.append(" ".join(cur))
        return lines

    # ── بسم الله ──
    bism = fix_ar("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
    sh(draw, (cx - tw(draw,bism,far_sm)//2, 130), bism, far_sm, gold)
    draw.line([(mg,210),(VIDEO_WIDTH-mg,210)], fill=(255,210,70,150), width=2)

    # ── اسم السورة الأولى ──
    first = ayahs_data[0]
    sl = fix_ar(f"سورة {first['surah_name']}  ﴿{first['ayah_number']} - {ayahs_data[-1]['ayah_number']}﴾")
    sh(draw, (cx - tw(draw,sl,far_med)//2, 240), sl, far_med, gold)
    draw.line([(mg,310),(VIDEO_WIDTH-mg,310)], fill=(255,210,70,80), width=1)

    # ── الآيات ──
    y = 350
    for d in ayahs_data:
        # رقم الآية
        num = fix_ar(f"﴿{d['ayah_number']}﴾")
        sh(draw, (cx - tw(draw,num,far_sm)//2, y), num, far_sm, gold)
        y += 50

        # نص الآية
        ar_lines = wrap(fix_ar(d['arabic']), far_big)
        for line in ar_lines:
            sh(draw, (cx - tw(draw,line,far_big)//2, y), line, far_big, white)
            y += 88

        y += 15

    # ── هاشتاقات ──
    tags = "#Quran #Islam #QuranShorts #قرآن #إسلام"
    draw.text((cx - tw(draw,tags,fen_sm)//2, VIDEO_HEIGHT-110), tags, font=fen_sm, fill=(150,180,200,170))

    tmp = "temp_overlay.png"
    img.save(tmp)
    return tmp

def download_nature_video(query_index):
    query = NATURE_QUERIES[query_index % len(NATURE_QUERIES)]
    print(f"[Pexels] فيديو: {query}")
    headers = {"Authorization": PEXELS_KEY}
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params={"query": query, "per_page": 15, "orientation": "portrait"},
            timeout=15
        ).json()
        videos = r.get("videos", [])
        random.shuffle(videos)
        for video in videos:
            for vf in sorted(video.get("video_files",[]), key=lambda x: x.get("width",0), reverse=True):
                if vf.get("width",0) >= 720:
                    out = "temp_bg.mp4"
                    resp = requests.get(vf["link"], timeout=60, stream=True)
                    with open(out,"wb") as f:
                        for chunk in resp.iter_content(8192):
                            f.write(chunk)
                    print(f"[Pexels] تم!")
                    return out
    except Exception as e:
        print(f"[Pexels] خطأ: {e}")
    return None

def generate_video(start_surah, start_ayah, output_path="output_video.mp4", query_index=0):
    # ── جمع الآيات والصوت ──
    print("[*] جمع الآيات...")
    audio_combined, ayahs, next_s, next_a = collect_ayahs(start_surah, start_ayah)

    if not audio_combined:
        raise Exception("فشل تنزيل الصوت!")

    # جلب بيانات الآيات
    ayahs_data = []
    for ref in ayahs:
        try:
            d = get_ayah_data(ref["surah"], ref["ayah"])
            ayahs_data.append(d)
        except:
            pass

    print(f"[*] عدد الآيات: {len(ayahs_data)}")

    # ── خلفية الطبيعة ──
    bg_path = download_nature_video(query_index)
    if bg_path and os.path.exists(bg_path):
        bg_raw = VideoFileClip(bg_path)
        if bg_raw.duration < TARGET_DUR:
            repeats = int(TARGET_DUR / bg_raw.duration) + 2
            bg_raw  = concatenate_videoclips([bg_raw] * repeats)
        bg_raw = bg_raw.subclip(0, TARGET_DUR)
        bw, bh = bg_raw.size
        tr = VIDEO_WIDTH / VIDEO_HEIGHT
        if bw/bh > tr:
            nw = int(bh * tr)
            bg_raw = bg_raw.crop(x1=(bw-nw)//2, x2=(bw-nw)//2+nw)
        else:
            nh = int(bw / tr)
            bg_raw = bg_raw.crop(y1=(bh-nh)//2, y2=(bh-nh)//2+nh)
        bg = bg_raw.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
    else:
        bg = ColorClip(size=(VIDEO_WIDTH,VIDEO_HEIGHT), color=(10,20,40), duration=TARGET_DUR)

    # ── overlay ──
    overlay_path = create_overlay(ayahs_data)
    overlay = ImageClip(overlay_path).set_duration(TARGET_DUR)

    # ── دمج ──
    final = CompositeVideoClip([bg, overlay]).set_duration(TARGET_DUR).set_audio(audio_combined)
    final.write_videofile(output_path, fps=FPS, codec="libx264", audio_codec="aac", preset="fast", threads=4, logger="bar")

    # تنظيف
    for ref in ayahs:
        if os.path.exists(ref["path"]):
            os.remove(ref["path"])
    for f in [overlay_path, bg_path]:
        if f and os.path.exists(f):
            try: os.remove(f)
            except: pass

    print(f"[OK] الفيديو جاهز: {output_path}")
    return output_path, next_s, next_a
