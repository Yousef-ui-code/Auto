import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    if not os.path.exists("client_secrets.json"):
        print("[!] client_secrets.json غير موجود!")
        return
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    creds = flow.run_local_server(port=8080, prompt="consent")
    with open("token.json","w") as f:
        f.write(creds.to_json())
    print("[OK] تم توليد token.json")
    print("انسخ محتواه وضعه في GitHub Secret باسم YOUTUBE_TOKEN")

if __name__ == "__main__":
    main()
