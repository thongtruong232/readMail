# from celery import shared_task
# from django.shortcuts import render
# import requests
# from imap_tools import MailBox
# from config import CLIENT_ID, CLIENT_SECRET, TENANT_ID
# import re
# from lxml import html
# from bs4 import BeautifulSoup
# from django.http import HttpResponse


# @shared_task
# def process_email_task(emails):
#     # try:
#         print('Start process_email_task')
#         email_user = str(emails.get('email', ''))
#         refresh_token = str(emails.get('additional_info', ''))
#         client_id = str(emails.get('id', ''))
#         print(f'email_user: {email_user}')
#         print(f'refresh_token: {refresh_token}')
#         print(f'client_id: {client_id}')


#         url = "http://localhost:5019/api/mail/read"
#         payload = {
#             "Email": email_user,
#             "RefreshToken": refresh_token,
#             "ClientId": client_id
#         }

#         response = requests.post(url, json=payload)
#         data = response.json()

#         results = []  # List để chứa tất cả kết quả

#         for item in data:
#             if item['from'] == 'noreply@notifications.textnow.com':
#                 link = parse_beautifulshop_tn(item['body'])
#                 tn_from = item['from']
#                 tn_data = item['date']
#                 results.append({'from': tn_from, 'link': link, 'date': tn_data})  # Append vào list

#             if item['from'] == 'info@info.textfree.us':
#                 code = parse_html_tf(item['body'])
#                 tf_from = item['from']
#                 tf_data = item['date']
#                 results.append({'from': tf_from, 'code': code, 'date': tf_data})  # Append vào list

#         return results  # Trả về danh sách kết quả
#         # return ('value1', 'value2', 'value3')
    
#     # except Exception as e:
#     #     return f"An error occurred: {e}"


# def parse_html_tf(html_content):
#     try:
#         print('Parse html')
#         # Sử dụng biểu thức chính quy để tìm 6 chữ số liên tiếp và loại trừ "000000"
#         match = re.search(r'\b(?!000000\b)\d{6}\b', html_content)
#         if match:
#             # print(match.group())  # In ra kết quả, ví dụ: "175414"
#             return match.group()
#         else:
#             print("Không tìm thấy mã xác nhận hợp lệ.")

#     except Exception as e:
#         print(e)


# def parse_beautifulshop_tn(html_content):
#     # Phân tích cú pháp HTML với BeautifulSoup
#     soup = BeautifulSoup(html_content, 'html.parser')
#     # Tìm tất cả các thẻ <a> có href chứa "https://94lr.adj.st/email_verification"
#     links = soup.find_all('a', href=True)

#     # Lọc các link có href đúng với mẫu cần tìm
#     target_links = [link['href'] for link in links if 'https://94lr.adj.st/email_verification' in link['href']]

#     # In tất cả các link tìm được
#     for link in target_links:
#         return link
    
    
# def txt_write(data_list):
#     with open("output.txt", "w", encoding="utf-8") as f:
#         for index, item in enumerate(data_list, start=1):
#             f.write(f"Email {index}:\n")
#             f.write(f"From: {item.get('from', '')}\n")
#             f.write(f"Subject: {item.get('subject', '')}\n")
#             f.write(f"Date: {item.get('date', '')}\n")
#             f.write("Body:\n")
#             f.write(item.get("body", "") + "\n")
#             f.write("=" * 50 + "\n\n")
