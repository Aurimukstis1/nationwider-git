import os
import requests

def download_latest_release():
    github_url = "https://github.com/Aurimukstis1/nationwider-git/raw/refs/heads/main/dist/main.exe"
    try:
        response = requests.get(github_url)
        response.raise_for_status()
        with open("new_version.exe.tmp", "wb") as f:
            f.write(response.content)
        print("replacing ...")
        # replace old exe
        if os.path.exists("main.exe"):
            os.remove("main.exe")
        if os.path.exists("new_version.exe.tmp"):
            os.rename("new_version.exe.tmp", "main.exe")
    except Exception as e:
        print(f"Error: {e}")
    
if __name__ == "__main__":
    print("Checking for updates...")
    download_latest_release()
    print("Downloaded new version.")
