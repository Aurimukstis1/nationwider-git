import os
import requests

def download_latest_release():
    github_url = "https://github.com/Aurimukstis1/nationwider-git/dist/main.exe"
    try:
        response = requests.get(github_url)
        response.raise_for_status()
        with open("new_version.exe.tmp", "wb") as f:
            f.write(response.content)
        print("Downloaded new version")
        # replace old exe
        os.rename("new_version.exe.tmp", "main.exe")
    except Exception as e:
        print(f"Error: {e}")
    
if __name__ == "__main__":
    download_latest_release()
