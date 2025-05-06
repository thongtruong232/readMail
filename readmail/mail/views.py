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
print('==> [views.py] File loaded')
def home_view(request):
    print('==> [home_view] Called')
    return render(request, 'home.html')

def get_code_view(request):
    print(f"==> [get_code_view] Called, method: {request.method}")
    try:
        if request.method == 'POST':
            email_data = request.POST.get('email_data', '')
            print(f"==> [get_code_view] email_data: {email_data}")
            results_list = []

            if email_data:
                print('==> [get_code_view] Parsing email_data')
                email_data_parse = parse_multiple_data(email_data)
                print(f"==> [get_code_view] email_data_parse: {email_data_parse}")
                
                if email_data_parse is None or not isinstance(email_data_parse, list) or len(email_data_parse) == 0:
                    print('==> [get_code_view] email_data_parse is invalid')
                    return render(request, 'home.html')
                
                # Remove duplicate emails while preserving the latest data for each email
                unique_emails = {}
                for email in email_data_parse:
                    email_address = email.get('email', '')
                    if email_address:
                        unique_emails[email_address] = email
                print(f"==> [get_code_view] unique_emails: {list(unique_emails.keys())}")

                # Create a ThreadPoolExecutor with max_workers parameter
                max_threads = min(32, len(unique_emails))
                print(f"==> [get_code_view] max_threads: {max_threads}")
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
                    # Create a list of futures for each unique email
                    socket_id = request.POST.get('socket_id')
                    print(f'socket_id: {socket_id}')
                    future_to_email = {}
                    for email in unique_emails.values():
                        print(f"==> [get_code_view] Submitting read_mail for: {email['email']}")
                        future = executor.submit(read_mail, email['email'], email['additional_info'], email['id'], email['index'], request)
                        future_to_email[future] = email['email']
                    
                    # Process results as they complete
                    for future in concurrent.futures.as_completed(future_to_email):
                        email_user = future_to_email[future]
                        email_data = next((data for data in email_data_parse if data['email'] == email_user), None)
                        try:
                            results = future.result()
                            print(f"==> [get_code_view] Results for {email_user}: {results}")
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
                print(f"==> [get_code_view] Final results_list: {results_list}")
                return HttpResponse('Processing completed')

            print('==> [get_code_view] No email_data')
            return render(request, 'home.html')

        print('==> [get_code_view] Not POST')
        return render(request, 'home.html')

    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'home.html')

def parse_multiple_data(input_string):
    print(f"==> [parse_multiple_data] input_string: {input_string}")
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

        print(f"==> [parse_multiple_data] result: {result}")
        return result
    except Exception as e:
        print(f"Lỗi khi parse data: {e}")
        return None

def read_mail(email, refresh_token, client_id, email_index, request):
    print(f"==> [read_mail] Called for email: {email}, client_id: {client_id}, index: {email_index}")
    try:
        url = "http://207.148.69.229:5000/api/mail/read"
        # url = "http://localhost:5000/api/mail/read"
        payload = {
            "Email": email,
            "RefreshToken": refresh_token,
            "ClientId": client_id
        }
        socket_id = request.POST.get('socket_id')
        
        # Log request details
        print(f"==> [read_mail] Making API request to {url}")
        print(f"==> [read_mail] Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload)
        
        # Log response details
        # print(f"Response status: {response.status_code}")
        # print(f"Response headers: {dict(response.headers)}")
        # try:
        #     print(f"Response body: {response.text[:500]}...")  # Print first 500 chars of response
        # except:
        #     print("Could not print response body")
        
        # Kiểm tra response status
        if response.status_code != 200:
            print(f"API returned status code {response.status_code}")
            return f"API error: {response.status_code}"
            
        try:
            data = response.json()
            print(f"==> [read_mail] Response JSON: {data}")
        except ValueError as e:
            print(f"Invalid JSON response: {e}")
            return f"Invalid response format: {e}"
            
        if not isinstance(data, list):
            print(f"Expected list but got {type(data)}")
            return f"Invalid data format: expected list"
            
        results = []  # List để chứa tất cả kết quả

        for item in data:
            print(f"==> [read_mail] Processing item: {item}")
            if not isinstance(item, dict):
                print(f"Skipping invalid item: {item}")
                continue
                
            if item.get('from') == 'noreply@notifications.textnow.com':
                try:
                    print(f"==> [read_mail] Parsing TextNow email body")
                    link = parse_beautifulshop_tn(item.get('body', ''))
                    tn_from = item.get('from', '')
                    tn_data = item.get('date', '')
                    result = {'from': tn_from, 'link': link, 'date': tn_data}
                    print(f"==> [read_mail] TextNow result: {result}")
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
                except Exception as e:
                    print(f"Error processing TextNow email: {e}")
                    continue

            if item.get('from') == 'info@info.textfree.us':
                try:
                    print(f"==> [read_mail] Parsing TextFree email body")
                    code = parse_html_tf(item.get('body', ''))
                    tf_from = item.get('from', '')
                    tf_data = item.get('date', '')
                    result = {'from': tf_from, 'code': code, 'date': tf_data}
                    print(f"==> [read_mail] TextFree result: {result}")
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
                except Exception as e:
                    print(f"Error processing TextFree email: {e}")
                    continue
                    
        print(f"==> [read_mail] Final results: {results}")
        return results
    except Exception as e:
        print(f"An error occurred while reading email for {email}: {e}")
        return f"An error occurred: {e}"


def parse_html_tf(html_content):
    print(f"==> [parse_html_tf] Input: {html_content[:100]}")
    try:
        print('Parse html')
        # Sử dụng biểu thức chính quy để tìm 6 chữ số liên tiếp và loại trừ "000000"
        match = re.search(r'\b(?!000000\b)\d{6}\b', html_content)
        if match:
            # print(match.group())  # In ra kết quả, ví dụ: "175414"
            print(f"==> [parse_html_tf] Found code: {match.group()}")
            return match.group()
        else:
            print("Không tìm thấy mã xác nhận hợp lệ.")

    except Exception as e:
        print(f"==> [parse_html_tf] Exception: {e}")


def parse_beautifulshop_tn(html_content):
    print(f"==> [parse_beautifulshop_tn] Input: {str(html_content)[:100]}")
    # Phân tích cú pháp HTML với BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    # Tìm tất cả các thẻ <a> có href chứa "https://94lr.adj.st/email_verification"
    links = soup.find_all('a', href=True)

    # Lọc các link có href đúng với mẫu cần tìm
    target_links = [link['href'] for link in links if 'https://94lr.adj.st/email_verification' in link['href']]
    print(f"==> [parse_beautifulshop_tn] target_links: {target_links}")

    # In tất cả các link tìm được
    for link in target_links:
        return link
    
    
    
def txt_write(data_list):
    print(f"==> [txt_write] Writing {len(data_list)} items to output.txt")
    with open("output.txt", "w", encoding="utf-8") as f:
        for index, item in enumerate(data_list, start=1):
            f.write(f"Email {index}:\n")
            f.write(f"From: {item.get('from', '')}\n")
            f.write(f"Subject: {item.get('subject', '')}\n")
            f.write(f"Date: {item.get('date', '')}\n")
            f.write("Body:\n")
            f.write(item.get("body", "") + "\n")
            f.write("=" * 50 + "\n\n")
