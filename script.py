import os
from dotenv import load_dotenv
import requests
from datetime import datetime

# .env 파일 로드
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
        title = result['properties']['할 일']['title'][0]['plain_text']
        task_status = result['properties']['상태']['status']['name']
        task_type_value = result['properties']['유형']['select']['name']
        
        if task_status == status and task_type_value in task_types:
            tasks.append(f"• *{title}*")  # 제목을 굵게 표시
    return "\n".join(tasks)

def create_slack_message(data):
    today = datetime.today().strftime("%Y-%m-%d")

    # ToDo 리스트 추가
    todo_tasks = filter_tasks(data, ["할 일"])
    todo_section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*To Do:*\n{todo_tasks if todo_tasks else '할 일이 없습니다.'}"
        }
    }

    # 매일 알림 (ToDo에 포함되지 않은 것만)
    daily_tasks = filter_tasks(data, ["매일"])
    daily_section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Daily CheckList:*\n{daily_tasks if daily_tasks else '오늘 할 일이 없습니다.'}"
        }
    }

    # 매주 토요일 알림
    weekly_section = {}
    if datetime.today().weekday() == 5:  # 토요일
        weekly_tasks = filter_tasks(data, ["매주"])
        weekly_section = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Weekly CheckList:*\n{weekly_tasks if weekly_tasks else '이번 주 할 일이 없습니다.'}"
            }
        }

    # 매월 마지막 주 토요일 알림
    monthly_section = {}
    if datetime.today().weekday() == 5 and (datetime.today().day + 7) > 31:  # 마지막 주 토요일
        monthly_tasks = filter_tasks(data, ["매월"])
        monthly_section = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Monthly CheckList:*\n{monthly_tasks if monthly_tasks else '이번 달 할 일이 없습니다.'}"
            }
        }

    # 메시지 블록 구성
    blocks = [
        {"type": "divider"},
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"오늘 날짜: {today}"
            }
        },
        {"type": "divider"},
        todo_section,
        daily_section
    ]

    # 조건부 섹션 추가
    if weekly_section:
        blocks.append(weekly_section)
    if monthly_section:
        blocks.append(monthly_section)

    blocks.append({"type": "divider"})

    return blocks


def send_slack_notification(blocks):
    slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {slack_bot_token}",
        "Content-Type": "application/json"
    }
    data = {
        "channel": "#알림-봇",  # 원하는 채널로 변경
        "blocks": blocks
    }
    requests.post(url, headers=headers, json=data)


def main():
    data = fetch_notion_data()
    blocks = create_slack_message(data)
    send_slack_notification(blocks)

if __name__ == "__main__":
    main()