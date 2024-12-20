import os
import requests
from datetime import datetime
# 로컬에서 실행시 dotenv import
from dotenv import load_dotenv

# 로컬에서 실행시 .env 파일 로드
load_dotenv()

def fetch_notion_data():
    notion_api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Notion-Version": "2021-05-13"
    }
    response = requests.post(url, headers=headers)
    return response.json()

def filter_tasks(data, task_types, status="진행 중"):
    tasks = []
    for result in data.get('results', []):
        # 제목이 비어있는 경우 처리
        title_array = result['properties']['할 일']['title']
        if not title_array:  # 제목이 비어있으면 건너뛰기
            continue
            
        title = title_array[0]['plain_text']
        task_status = result['properties']['상태']['status']['name']
        task_type_value = result['properties']['유형']['select']['name']
        
        if task_status == status and task_type_value in task_types:
            tasks.append(f"• *{title}*")  # 제목을 굵게 표시
    
    # 각 항목을 두 줄 바꿈으로 구분
    return "\n".join(tasks) if tasks else "할 일이 없습니다."

def create_discord_message(data):
    today = datetime.today().strftime("%Y-%m-%d")
    
    message = {
        "embeds": [{
            "title": f"📅 오늘 날짜: {today}",
            "color": 0x00ff00,
            "fields": []
        }]
    }
    
    # ToDo 리스트
    todo_tasks = filter_tasks(data, ["To Do"])
    message["embeds"][0]["fields"].append({
        "name": "📌 To Do",
        "value": f"{todo_tasks}\n\u200B",  # 보이지 않는 문자로 줄바꿈 추가
        "inline": False
    })
    
    # Daily 체크리스트
    daily_tasks = filter_tasks(data, ["Daily"])
    message["embeds"][0]["fields"].append({
        "name": "📋 Daily CheckList",
        "value": f"{daily_tasks}\n\u200B",  # 보이지 않는 문자로 줄바꿈 추가
        "inline": False
    })
    
    # Weekly 체크 (토요일)
    if datetime.today().weekday() == 5:
        weekly_tasks = filter_tasks(data, ["Weekly"])
        message["embeds"][0]["fields"].append({
            "name": "📅 Weekly CheckList",
            "value": f"{weekly_tasks}\n\u200B",  # 보이지 않는 문자로 줄바꿈 추가
            "inline": False
        })
    
    # Monthly 체크 (마지막 주 토요일)
    if datetime.today().weekday() == 5 and (datetime.today().day + 7) > 31:
        monthly_tasks = filter_tasks(data, ["Monthly"])
        message["embeds"][0]["fields"].append({
            "name": "📊 Monthly CheckList",
            "value": monthly_tasks,  # 마지막 필드는 줄바꿈 불필요
            "inline": False
        })
    
    return message

def send_discord_notification(message):
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    response = requests.post(webhook_url, json=message)
    return response.status_code == 204  # Discord webhook은 204를 반환하면 성공

def main():
    data = fetch_notion_data()
    message = create_discord_message(data)
    send_discord_notification(message)

if __name__ == "__main__":
    main()