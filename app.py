import streamlit as st
import requests
import pandas as pd

# 1. 페이지 기본 설정
st.set_page_config(page_title="2026 월드컵 조 3위 경쟁표", page_icon="🏆", layout="wide")

# 2. API 설정 
# 깃허브에 코드를 올릴 때는 API 키가 노출되면 안 되므로 Streamlit의 st.secrets를 사용해.
# 배포 후 Streamlit Cloud의 App settings -> Secrets 탭에 API_KEY="본인키" 를 적어주면 돼.
try:
    API_KEY = st.secrets["API_KEY"]
except KeyError:
    # 로컬 테스트용 임시 키 (실제 깃허브 업로드 시에는 비워두거나 Secrets를 꼭 설정해!)
    API_KEY = "여기에_본인_API_KEY를_입력해"

HEADERS = {
    "x-apisports-key": API_KEY
}

# 3. 데이터 가져오기 및 캐싱 (10분마다 갱신하여 무료 API 한도 초과 방지)
@st.cache_data(ttl=600)
def get_worldcup_standings():
    url = "https://v3.football.api-sports.io/standings"
    querystring = {"league": "1", "season": "2026"}
    response = requests.get(url, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        return response.json()
    return None

@st.cache_data(ttl=600)
def get_remaining_fixtures():
    url = "https://v3.football.api-sports.io/fixtures"
    # 조별리그 마지막 기간 필터링
    querystring = {
        "league": "1", 
        "season": "2026",
        "from": "2026-06-25",
        "to": "2026-06-27"
    }
    response = requests.get(url, headers=HEADERS, params=querystring)
    if response.status_code == 200:
        return response.json()
    return None

# ==========================================
# 4. 화면 UI 구성 시작
# ==========================================
st.title("🏆 2026 월드컵 와일드카드(조 3위) 실시간 경쟁표")
st.markdown("조 3위 12개 팀 중 상위 8개 팀이 32강에 진출합니다. (승점 ➔ 골득실 ➔ 다득점 순)")

# 데이터 불러오기
standings_data = get_worldcup_standings()
third_place_teams = []
st.write(standings_data)

# 조 3위 데이터 파싱
if standings_data and 'response' in standings_data and len(standings_data['response']) > 0:
    league_data = standings_data['response'][0]['league']
    standings = league_data['standings'] # 이중 리스트 형태 (조별 배열)
    
    for group in standings:
        for team_info in group:
            if team_info['rank'] == 3: # 조 3위 팀만 추출
                third_place_teams.append({
                    "Group": team_info['group'][-1], # 'Group A'에서 'A'만 추출
                    "Team": team_info['team']['name'],
                    "Points": team_info['points'],
                    "GD": team_info['goalsDiff'],
                    "GF": team_info['all']['goals']['for'],
                    "Played": team_info['all']['played']
                })

# 순위표 렌더링
if third_place_teams:
    df_3rd = pd.DataFrame(third_place_teams)
    
    # 순위 결정 로직: 승점 -> 골득실 -> 다득점 순으로 내림차순 정렬
    df_3rd = df_3rd.sort_values(by=['Points', 'GD', 'GF'], ascending=[False, False, False]).reset_index(drop=True)
    
    # 인덱스를 1위부터 시작하도록 조정
    df_3rd.index = df_3rd.index + 1
    
    st.subheader("📊 실시간 랭킹")
    
    # 하이라이트 스타일 함수 (상위 8팀 초록색, 하위 4팀 붉은색)
    def highlight_status(row):
        if row.name <= 8:
            return ['background-color: rgba(40, 167, 69, 0.2)'] * len(row)
        else:
            return ['background-color: rgba(220, 53, 69, 0.2)'] * len(row)
            
    # Styler 적용하여 데이터프레임 출력
    st.dataframe(df_3rd.style.apply(highlight_status, axis=1), use_container_width=True)
else:
    st.warning("순위 데이터를 불러오는 데 실패했거나 아직 데이터가 없어.")

st.divider()

# 남은 경기 일정 렌더링
st.subheader("🗓️ 남은 조별리그 경기 현황")
fixtures_data = get_remaining_fixtures()
match_list = []

if fixtures_data and 'response' in fixtures_data:
    for match in fixtures_data['response']:
        home_goal = match['goals']['home']
        away_goal = match['goals']['away']
        score_display = f"{home_goal} : {away_goal}" if home_goal is not None else "vs"
        
        match_list.append({
            "Date": match['fixture']['date'][:10],
            "Time (UTC)": match['fixture']['date'][11:16],
            "Status": match['fixture']['status']['short'], # NS(시작전), 1H, 2H, FT(종료) 등
            "Home Team": match['teams']['home']['name'],
            "Score": score_display,
            "Away Team": match['teams']['away']['name']
        })
        
if match_list:
    df_matches = pd.DataFrame(match_list)
    st.dataframe(df_matches, use_container_width=True)
else:
    st.info("조건에 맞는 남은 경기 일정이 없어.")
