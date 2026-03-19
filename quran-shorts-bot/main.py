import os, json, glob, sys
from generate_video import get_ayah_data, generate_video
from upload_youtube import upload_video

PROGRESS_FILE = "data/progress.json"
AUDIO_DIR     = "audio"
OUTPUT_VIDEO  = "output_video.mp4"

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

def load_progress():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"last_surah":1,"last_ayah":0,"total_uploaded":0}

def save_progress(p):
    with open(PROGRESS_FILE,"w") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def next_ayah(p):
    s, a = p["last_surah"], p["last_ayah"]+1
    if a > SURAH_LENGTHS.get(s,7):
        s += 1; a = 1
    if s > 114:
        s = 1; a = 1
    return s, a

def find_audio(s, a):
    for pat in [
        f"{AUDIO_DIR}/{str(s).zfill(3)}{str(a).zfill(3)}.mp3",
        f"{AUDIO_DIR}/{s}_{a}.mp3",
        f"{AUDIO_DIR}/{s}-{a}.mp3",
    ]:
        if os.path.exists(pat): return pat
    m = glob.glob(f"{AUDIO_DIR}/*{str(s).zfill(3)}*{str(a).zfill(3)}*.mp3")
    return m[0] if m else None

def main():
    print("="*50)
    p = load_progress()
    s, a = next_ayah(p)
    print(f"[->] سورة {s} آية {a}")
    audio = find_audio(s, a)
    if not audio:
        print(f"[!] لا يوجد MP3 لسورة {s} آية {a}")
        print(f"    المطلوب: audio/{str(s).zfill(3)}{str(a).zfill(3)}.mp3")
        sys.exit(1)
    print(f"[~] {audio}")
    data = get_ayah_data(s, a)
    print(f"[v] {data['arabic'][:50]}...")
    generate_video(data, audio, OUTPUT_VIDEO)
    url = upload_video(OUTPUT_VIDEO, data)
    p.update({"last_surah":s,"last_ayah":a,"total_uploaded":p.get("total_uploaded",0)+1})
    save_progress(p)
    if os.path.exists(OUTPUT_VIDEO):
        os.remove(OUTPUT_VIDEO)
    print(f"[OK] فيديو رقم {p['total_uploaded']}")
    print(url)
    print("="*50)

if __name__ == "__main__":
    main()
