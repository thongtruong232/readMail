import subprocess
import requests
from django.shortcuts import render

def start_api(request):
    api_url = "http://localhost:5000/api/health"  # Endpoint kiểm tra API C#

    try:
        response = requests.get(api_url)
        if response.status_code != 200:
            raise Exception("API chưa chạy hoặc không phản hồi.")
    except Exception:
        try:
            # Nếu API không chạy, khởi động API C#
            subprocess.Popen(["dotnet", "path_to_your_api_csharp_project.dll"])
            print("API C# đã được khởi động.")
        except Exception as e:
            print(f"Không thể khởi động API C#: {e}")

    return render(request, "your_template.html")