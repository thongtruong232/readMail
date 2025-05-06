import subprocess
import requests
from django.shortcuts import render

def start_api(request):
    print('==> [start_api] Called')
    api_url = "http://localhost:5000/api/health"  # Endpoint kiểm tra API C#

    try:
        print(f"==> [start_api] Checking API health at {api_url}")
        response = requests.get(api_url)
        print(f"==> [start_api] API health status: {response.status_code}")
        if response.status_code != 200:
            raise Exception("API chưa chạy hoặc không phản hồi.")
    except Exception as e:
        print(f"==> [start_api] API health check failed: {e}")
        try:
            print("==> [start_api] Trying to start API C#...")
            subprocess.Popen(["dotnet", "path_to_your_api_csharp_project.dll"])
            print("API C# đã được khởi động.")
        except Exception as e:
            print(f"Không thể khởi động API C#: {e}")

    return render(request, "your_template.html")