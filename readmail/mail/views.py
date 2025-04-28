from django.shortcuts import render
import requests
from imap_tools import MailBox
import json
from config import CLIENT_ID, CLIENT_SECRET, TENANT_ID
import re
from lxml import html
from bs4 import BeautifulSoup
from django.http import HttpResponse
import subprocess
import concurrent.futures
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
# Create your views here.
def home_view(request):
    return render(request, 'home.html')

def get_code_view(request):
    try:
        if request.method == 'POST':
            email_data = request.POST.get('email_data', '')
            results_list = []

            if email_data:
                email_data_parse = parse_multiple_data(email_data)
                
                if email_data_parse is None or not isinstance(email_data_parse, list) or len(email_data_parse) == 0:
                    return render(request, 'home.html')
                
                # Remove duplicate emails while preserving the latest data for each email
                unique_emails = {}
                for email in email_data_parse:
                    email_address = email.get('email', '')
                    if email_address:
                        unique_emails[email_address] = email

                # Create a ThreadPoolExecutor with max_workers parameter
                max_threads = min(32, len(unique_emails))
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
                    # Create a list of futures for each unique email
                    socket_id = request.POST.get('socket_id')
                    print(f'socket_id: {socket_id}')
                    future_to_email = {}
                    for email in unique_emails.values():
                        future = executor.submit(read_mail, email['email'], email['additional_info'], email['id'], email['index'], request)
                        future_to_email[future] = email['email']
                    
                    # Process results as they complete
                    for future in concurrent.futures.as_completed(future_to_email):
                        email_user = future_to_email[future]
                        email_data = next((data for data in email_data_parse if data['email'] == email_user), None)
                        try:
                            results = future.result()
                            if type(results) == list:
                                if results:  # Only add if there are results
                                    results_list.append({
                                        "email_user": {
                                            "address": email_user,
                                            "index": email_data['index'] if email_data else 0
                                        },
                                        "results": results
                                    })
                        except Exception as e:
                            print(f"Error processing email {email_user}: {e}")
                            results_list.append({
                                "email_user": {
                                    "address": email_user,
                                    "index": email_data['index'] if email_data else 0
                                },
                                "results": f"Error: {str(e)}"
                            })

                # Sort results_list by index before rendering
                results_list.sort(key=lambda x: x['email_user']['index'])
                print('Done scripts')
                return HttpResponse('Processing completed')

            return render(request, 'home.html')

        return render(request, 'home.html')

    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'home.html')

def parse_multiple_data(input_string):
    try:
        # Tách chuỗi theo dấu '\n' để lấy từng dòng
        lines = [line.strip() for line in input_string.split("\n") if line.strip()]  # Loại bỏ dòng trống
        
        result = []
        for index, line in enumerate(lines, 1):  # Bắt đầu đếm từ 1
            # Tách mỗi dòng theo dấu '|'
            attributes = line.split("|")
            
            # Kiểm tra đủ thông tin
            if len(attributes) >= 4:
                # Tạo dictionary cho mỗi đối tượng
                data_object = {
                    "index": index,  # Thêm số thứ tự
                    "email": attributes[0].strip(),
                    "password": attributes[1].strip(),
                    "additional_info": attributes[2].strip(),
                    "id": attributes[3].strip()
                }
                result.append(data_object)
            else:
                print(f"Dòng {index} không đủ thông tin: {line}")

        return result
    except Exception as e:
        print(f"Lỗi khi parse data: {e}")
        return None

def read_mail(email, refresh_token, client_id, email_index, request):
    try:
        url = "http://localhost:5000/api/mail/read"
        payload = {
            "Email": email,
            "RefreshToken": refresh_token,
            "ClientId": client_id
        }
        socket_id = request.POST.get('socket_id')
        response = requests.post(url, json=payload)
        data = response.json()

        results = []  # List để chứa tất cả kết quả

        for item in data:
            if item['from'] == 'noreply@notifications.textnow.com':
                link = parse_beautifulshop_tn(item['body'])
                tn_from = item['from']
                tn_data = item['date']
                result = {'from': tn_from, 'link': link, 'date': tn_data}
                results.append(result)
                
                # Send WebSocket update
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"client_{socket_id}",
                    {
                        'type': 'email_update',
                        'email': email,
                        'result': result,
                        'email_index': email_index,
                        'result_index': len(results)
                    }
                )

            if item['from'] == 'info@info.textfree.us':
                code = parse_html_tf(item['body'])
                tf_from = item['from']
                tf_data = item['date']
                result = {'from': tf_from, 'code': code, 'date': tf_data}
                results.append(result)
                
                # Send WebSocket update
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"client_{socket_id}",
                    {
                        'type': 'email_update',
                        'email': email,
                        'result': result,
                        'email_index': email_index,
                        'result_index': len(results)
                    }
                )
        return results
    except Exception as e:
        print(f"An error occurred while reading email for {email}: {e}")
        return f"An error occurred: {e}"


def parse_html_tf(html_content):
    try:
        print('Parse html')
        # Sử dụng biểu thức chính quy để tìm 6 chữ số liên tiếp và loại trừ "000000"
        match = re.search(r'\b(?!000000\b)\d{6}\b', html_content)
        if match:
            # print(match.group())  # In ra kết quả, ví dụ: "175414"
            return match.group()
        else:
            print("Không tìm thấy mã xác nhận hợp lệ.")

    except Exception as e:
        print(e)


def parse_beautifulshop_tn(html_content):
    # Phân tích cú pháp HTML với BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    # Tìm tất cả các thẻ <a> có href chứa "https://94lr.adj.st/email_verification"
    links = soup.find_all('a', href=True)

    # Lọc các link có href đúng với mẫu cần tìm
    target_links = [link['href'] for link in links if 'https://94lr.adj.st/email_verification' in link['href']]

    # In tất cả các link tìm được
    for link in target_links:
        return link
    
    
    
def txt_write(data_list):
    with open("output.txt", "w", encoding="utf-8") as f:
        for index, item in enumerate(data_list, start=1):
            f.write(f"Email {index}:\n")
            f.write(f"From: {item.get('from', '')}\n")
            f.write(f"Subject: {item.get('subject', '')}\n")
            f.write(f"Date: {item.get('date', '')}\n")
            f.write("Body:\n")
            f.write(item.get("body", "") + "\n")
            f.write("=" * 50 + "\n\n")
