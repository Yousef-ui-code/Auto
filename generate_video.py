import requests, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from moviepy.editor import (AudioFileClip, VideoFileClip, ImageClip,
    CompositeVideoClip, ColorClip, concatenate_videoclips, concatenate_audioclips)
from moviepy.audio.AudioClip import AudioArrayClip

VIDEO_WIDTH  = 1080
VIDEO_HEIGHT = 1920
FPS          = 30
TARGET_DUR   = 59.0
FONT_AR_PATH = "fonts/ArabicBold.ttf"
FONT_EN_PATH = "fonts/DejaVuSans.ttf"
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY", "agiQsdsM9GHC0XFD91gaX2611yzowQLOi2eeKep8baYsObL7N0MdP5e0")

NATURE_QUERIES = [
    "road nature","waterfall nature","forest trees","ocean waves",
    "sunset sky","river stream","mountains nature","rain nature",
    "clouds sky","desert sand","flowers nature","green nature",
    "lake reflection","sunrise nature","snow mountains"
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
        surah += 1; ayah = 1
    if surah > 114:
        surah = 1; ayah = 1
    return surah, ayah

def get_ayah_data(surah, ayah):
    ar = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/ar.alafasy", timeout=15).json()
    en = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.asad", timeout=15).json()
    return {
        "arabic":        ar["data"]["text"],
        "english":       en["data"]["text"],
        "surah_name":    ar["data"]["surah"]["name"],
        "surah_name_en": ar["data"]["surah"]["englishName"],
        "ayah_number":   ar["data"]["numberInSurah"],
        "surah_number":  surah,
    }

def download_audio_ayah(surah, ayah):
    path = f"temp_ayah_{surah}_{ayah}.mp3"
    url  = f"https://everyayah.com/data/Alafasy_128kbps/{str(surah).zfill(3)}{str(ayah).zfill(3)}.mp3"
    r = requests.get(url, timeout=30)
    with open(path, "wb") as f:
        f.write(r.content)
    return path

def fix_ar(text):
    try:
        return arabic_reshaper.reshape(text)
    except:
        return text

def tw(draw, text, font):
    try:
        return int(draw.textlength(text, font=font))
    except:
        return draw.textbbox((0,0),text,font=font)[2]

def wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur+[w])
        if tw(draw,test,font) > max_w and cur:
            lines.append(" ".join(cur)); cur=[w]
        else:
            cur.append(w)
    if cur: lines.append(" ".join(cur))
    return lines

def make_ayah_frame(arabic, english):
    # صورة شفافة بالكامل — بس النص في المنتصف
    img  = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0,0,0,0))
    draw = ImageDraw.Draw(img)

    try:
        far = ImageFont.truetype(FONT_AR_PATH, 88)
        fen = ImageFont.truetype(FONT_EN_PATH, 34)
    except:
        far = fen = ImageFont.load_default()

    cx = VIDEO_WIDTH // 2
    mw = VIDEO_WIDTH - 120

    ar_lines = wrap(draw, fix_ar(arabic), far, mw)
    en_lines = wrap(draw, english, fen, mw)

    lh_ar = 105
    lh_en = 46
    gap   = 25
    total = len(ar_lines)*lh_ar + gap + len(en_lines)*lh_en

    y = (VIDEO_HEIGHT - total) // 2

    # ظل خفيف خلف النص فقط
    pad = 45
    draw = ImageDraw.Draw(img)

    # النص العربي
    for line in ar_lines:
        lw = tw(draw, line, far)
        draw.text((cx-lw//2+4, y+4), line, font=far, fill=(0,0,0,210))
        draw.text((cx-lw//2,   y  ), line, font=far, fill=(255,255,255,255))
        y += lh_ar

    y += gap

    # الترجمة
    for line in en_lines:
        lw = tw(draw, line, fen)
        draw.text((cx-lw//2+2, y+2), line, font=fen, fill=(0,0,0,180))
        draw.text((cx-lw//2,   y  ), line, font=fen, fill=(210,210,210,230))
        y += lh_en

    return img

def download_bg(query_index):
    query = NATURE_QUERIES[query_index % len(NATURE_QUERIES)]
    print(f"[Pexels] {query}")
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_KEY},
            params={"query": query, "per_page": 15, "orientation": "portrait"},
            timeout=15
        ).json()
        videos = r.get("videos", [])
        random.shuffle(videos)
        for v in videos:
            for vf in sorted(v.get("video_files",[]), key=lambda x: x.get("width",0), reverse=True):
                if vf.get("width",0) >= 720:
                    out = "temp_bg.mp4"
                    resp = requests.get(vf["link"], timeout=60, stream=True)
                    with open(out,"wb") as f:
                        for chunk in resp.iter_content(8192): f.write(chunk)
                    print("[Pexels] تم!")
                    return out
    except Exception as e:
        print(f"[Pexels] خطأ: {e}")
    return None

def generate_video(start_surah, start_ayah, output_path="output_video.mp4", query_index=0):
    ayahs, audio_clips = [], []
    total = 0.0
    surah, ayah = start_surah, start_ayah

    while total < TARGET_DUR:
        try:
            print(f"[+] سورة {surah} آية {ayah}")
            ap  = download_audio_ayah(surah, ayah)
            ac  = AudioFileClip(ap)
            dur = ac.duration
            if total + dur > TARGET_DUR and ayahs:
                os.remove(ap); break
            data = get_ayah_data(surah, ayah)
            ayahs.append({"data":data, "dur":dur, "path":ap})
            audio_clips.append(ac)
            total += dur
            print(f"    {total:.1f}s")
            surah, ayah = next_ayah_ref(surah, ayah)
        except Exception as e:
            print(f"خطأ: {e}")
            surah, ayah = next_ayah_ref(surah, ayah)

    if not ayahs: raise Exception("فشل!")

    # الصوت
    audio = concatenate_audioclips(audio_clips)
    if audio.duration < TARGET_DUR:
        sil = AudioArrayClip(np.zeros((int((TARGET_DUR-audio.duration)*44100),2)), fps=44100)
        audio = concatenate_audioclips([audio, sil])
    audio = audio.subclip(0, TARGET_DUR)

    # الخلفية
    bg_path = download_bg(query_index)
    if bg_path and os.path.exists(bg_path):
        bg_raw = VideoFileClip(bg_path)
        if bg_raw.duration < TARGET_DUR:
            bg_raw = concatenate_videoclips([bg_raw]*(int(TARGET_DUR/bg_raw.duration)+2))
        bg_raw = bg_raw.subclip(0, TARGET_DUR)
        bw,bh  = bg_raw.size
        tr     = VIDEO_WIDTH/VIDEO_HEIGHT
        if bw/bh > tr:
            nw = int(bh*tr); bg_raw = bg_raw.crop(x1=(bw-nw)//2, x2=(bw-nw)//2+nw)
        else:
            nh = int(bw/tr); bg_raw = bg_raw.crop(y1=(bh-nh)//2, y2=(bh-nh)//2+nh)
        bg = bg_raw.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
    else:
        bg = ColorClip(size=(VIDEO_WIDTH,VIDEO_HEIGHT), color=(10,20,40), duration=TARGET_DUR)

    # كل آية = clip منفصل يظهر في وقتها بس
    text_clips = []
    t = 0.0
    for ref in ayahs:
        frame = make_ayah_frame(ref["data"]["arabic"], ref["data"]["english"])
        tmp   = f"tmp_f_{ref['data']['surah_number']}_{ref['data']['ayah_number']}.png"
        frame.save(tmp)
        clip  = (ImageClip(tmp)
                 .set_start(t)
                 .set_duration(ref["dur"])
                 .set_fps(FPS))
        text_clips.append(clip)
        t += ref["dur"]

    final = CompositeVideoClip([bg]+text_clips).set_duration(TARGET_DUR).set_audio(audio)
    final.write_videofile(output_path, fps=FPS, codec="libx264",
                         audio_codec="aac", preset="fast", threads=4, logger="bar")

    # تنظيف
    for ref in ayahs:
        for f in [ref["path"], f"tmp_f_{ref['data']['surah_number']}_{ref['data']['ayah_number']}.png"]:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass
    if bg_path and os.path.exists(bg_path):
        try: os.remove(bg_path)
        except: pass

    print(f"[OK] {output_path}")
    return output_path, surah, ayah
