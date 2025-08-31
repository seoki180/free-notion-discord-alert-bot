import os
import requests
from datetime import datetime, timezone, timedelta
# 로컬에서 실행시 dotenv import
from dotenv import load_dotenv

# 로컬에서 실행시 .env 파일 로드
load_dotenv()

def fetch_notion_calendar():
    """노션 캘린더에서 오늘 일정을 가져옵니다."""
    notion_api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    # 한국 시간대 설정 (UTC+9)
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst)
    
    # 오늘 날짜의 시작과 끝 시간 설정
    start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Notion-Version": "2021-05-13",
        "Content-Type": "application/json"
    }
    
    # 모든 데이터를 가져온 후 Python에서 필터링
    payload = {}
    
    response = requests.post(url, headers=headers,json=payload)
    return response.json()

def format_schedule_time(date_property):
    """일정 시간을 포맷팅합니다."""
    if not date_property or not date_property.get('date'):
        return "시간 미정"
    
    date_info = date_property['date']
    if not date_info.get('start'):
        return "시간 미정"
    
    # 시작 시간 파싱
    start_str = date_info['start']
    
    # 날짜만 있고 시간이 없는 경우 (예: "2024-01-01")
    if 'T' not in start_str:
        return "시간 미정"
    
    # 한국 시간대 설정
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).date()
    
    try:
        start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        start_time_kst = start_time.astimezone(kst)
        start_date = start_time_kst.date()
        
        # 종료 시간이 있는 경우
        if date_info.get('end'):
            end_str = date_info['end']
            
            # 종료 시간도 날짜만 있는 경우
            if 'T' not in end_str:
                # 시작 날짜가 오늘인 경우에만 시작 시간 표시
                if start_date == today:
                    return start_time_kst.strftime('%H:%M')
                else:
                    return "시간 미정"
            
            end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            end_time_kst = end_time.astimezone(kst)
            end_date = end_time_kst.date()
            
            # 시작 날짜가 오늘인 경우
            if start_date == today:
                # 종료 날짜도 오늘인 경우
                if end_date == today:
                    return f"{start_time_kst.strftime('%H:%M')} - {end_time_kst.strftime('%H:%M')}"
                else:
                    # 종료 시간이 내일 이후인 경우, 오늘은 시작 시간부터
                    return f"{start_time_kst.strftime('%H:%M')} -"
            # 종료 날짜가 오늘인 경우 (시작 날짜는 어제 이전)
            elif end_date == today:
                return f"- {end_time_kst.strftime('%H:%M')}"
            else:
                return "시간 미정"
        else:
            # 종료 시간이 없는 경우, 시작 날짜가 오늘인 경우에만 표시
            if start_date == today:
                return start_time_kst.strftime('%H:%M')
            else:
                return "시간 미정"
    except:
        # 시간 파싱에 실패한 경우
        return "시간 미정"

def process_calendar_events(data):
    """캘린더 이벤트를 처리하여 일정 목록을 만듭니다."""
    events = {"date": [], "participant": []}
    
    # 한국 시간대 설정
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).date()
    
    for result in data.get('results', []):
        properties = result['properties']
        
        # 제목 가져오기 (다양한 속성명 시도)
        title = None
        for title_prop in ['제목', '이름', 'Name', 'Title', '일정']:
            if title_prop in properties:
                title_array = properties[title_prop].get('title', [])
                if title_array:
                    title = title_array[0]['plain_text']
                    break
        
        if not title:
            continue
        
        # 날짜/시간 정보 가져오기
        date_property = None
        for date_prop in ['시간', '시 간', 'Time', 'Date']:
            if date_prop in properties and properties[date_prop].get('date'):
                date_property = properties[date_prop]
                break
        
        # 오늘 날짜에 해당하는지 확인
        if date_property and date_property.get('date'):
            date_info = date_property['date']
            is_today_event = False
            
            # 시작 날짜 확인
            if date_info.get('start'):
                start_str = date_info['start']
                if 'T' in start_str:  # 시간이 포함된 경우
                    try:
                        start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                        start_time_kst = start_time.astimezone(kst)
                        start_date = start_time_kst.date()
                        if start_date == today:
                            is_today_event = True
                    except:
                        pass
                else:  # 날짜만 있는 경우
                    try:
                        start_date = datetime.fromisoformat(start_str).date()
                        if start_date == today:
                            is_today_event = True
                    except:
                        pass
            
            # 종료 날짜 확인
            if date_info.get('end'):
                end_str = date_info['end']
                if 'T' in end_str:  # 시간이 포함된 경우
                    try:
                        end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                        end_time_kst = end_time.astimezone(kst)
                        end_date = end_time_kst.date()
                        if end_date == today:
                            is_today_event = True
                    except:
                        pass
                else:  # 날짜만 있는 경우
                    try:
                        end_date = datetime.fromisoformat(end_str).date()
                        if end_date == today:
                            is_today_event = True
                    except:
                        pass
            
            # 오늘 일정이 아니면 건너뛰기
            if not is_today_event:
                continue
        else:
            continue
        
        time_str = format_schedule_time(date_property)
        
        # 위치 정보 가져오기 (있는 경우)
        location = ""
        for loc_prop in ['장소']:
            if loc_prop in properties:
                loc_value = properties[loc_prop]
                if loc_value.get('rich_text'):
                    location = loc_value['rich_text'][0]['plain_text']
                elif loc_value.get('url'):
                    location = loc_value['url']
                break

        participant = ""
        for participant_prop in ['참석']:
            if participant_prop in properties:
                people_list = properties[participant_prop].get('people', [])
                for person in people_list:
                    if 'name' in person:
                        participant += person['name'] + ", "
                break
        
        # 일정 정보 구성
        event_info = f"• **{time_str}** - *{title}*"
        if location:
            event_info += f" 📍 {location}"

        events["date"].append(event_info)
        events["participant"].append(participant)
    
    return events

def create_discord_message(events):
    """디스코드 메시지를 생성합니다."""
    # 한국 시간대 설정 (UTC+9)
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst)
    
    if len(events["date"]) == 0:
        message = {
            "embeds": [{
                "title": f"📅 {today.strftime('%Y년 %m월 %d일')} 일정",
                "description": "오늘 예정된 일정이 없습니다. 😊",
                "color": 0x00ff00,
                "footer": {
                    "text": f"알림 시간: {today.strftime('%H:%M')}"
                }
            }]
        }
    else:
        events_text = "\n".join(events["date"])+ "    😀 참석 : ".join(events["participant"])
        message = {
            "embeds": [{
                "title": f"📅 {today.strftime('%Y년 %m월 %d일')} 일정",
                "description": f"오늘 **{len(events['date'])}개**의 일정이 있습니다:\n\n{events_text}\n",
                "color": 0x00ff00,
                "footer": {
                    "text": f"알림 시간: {today.strftime('%H:%M')}"
                }
            }]
        }
    
    return message

def send_discord_notification(message):
    """디스코드로 알림을 보냅니다."""
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    response = requests.post(webhook_url, json=message)
    return response.status_code == 204  # Discord webhook은 204를 반환하면 성공

def main():
    """메인 함수"""
    try:
        print("노션 캘린더에서 오늘 일정을 가져오는 중...")
        data = fetch_notion_calendar()
        
        print("일정을 처리하는 중...")
        events = process_calendar_events(data)
        
        print("디스코드 메시지를 생성하는 중...")
        message = create_discord_message(events)

        print("디스코드로 알림을 보내는 중...")
        success = send_discord_notification(message)
        
        if success:
            print("✅ 알림이 성공적으로 전송되었습니다!")
        else:
            print("❌ 알림 전송에 실패했습니다.")
            
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main()