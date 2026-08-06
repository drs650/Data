'''
day62_subway/pages_src/explore.py

작성일 : 26-08-06
작성자 : 수완
목적 : 즐겨찾는 역을 저장 --> 다른 위젯을 조작해도 사라지지 않게 한다.
        선택한 역의 시간대별 승하차 패턴을 그래프로 보여준다.
        
'''
import streamlit as st
from data_loader import load_subway

st.title('역별 탐색')

# 데이터 불러오기
df = load_subway()
station_list = sorted(df['역명'].unique())

# 'favorite_stations'라는 키가 없을 때만 빈 리스트로 초기화
#  (==이 세션에서 처음 방문했을 때만)
if 'favorite_stations' not in st.session_state:
    st.session_state.favorite_stations = []

st.subheader('즐겨찾는 역 관리')

col_add, col_btn = st.columns([3, 1])
with col_add:
    station_to_add = st.selectbox('추가할 역', station_list, key='station_to_add')
with col_btn:
    st.write('') # 버튼 높이를 selectbox와 맞추기 위한 여백용 빈 줄
    st.write('')
    if st.button('+ 추가'):
        if station_to_add not in st.session_state.favorite_stations:
            st.session_state.favorite_stations.append(station_to_add)
            st.rerun()

if not st.session_state.favorite_stations:
    st.info('아직 즐겨찾기한 약이 없습니다. 위에서 역을 선택하고 추가 버튼을 눌러보세요.')
else:
    for i, station in enumerate(st.session_state.favorite_stations):
        col_name, col_del = st.columns([4, 1])
        with col_name:
            st.write(f'{i+1}. {station}')
        with col_del:
            # key=f'del_{i}' : 삭제 버튼이 여러 개일 때 서로 구분하기 위한 고유 key
            if st.button('삭제', key=f'del_{i}'):
                st.session_state.favorite_stations.pop(i) # i번 째 값을 꺼내어 삭제
                st.rerun()

st.divider()

# --- 즐겨찾기한 역의 '시간대별 패턴' 확인 ---
if st.session_state.favorite_stations:
    # 즐겨찾기 한 역이 여러 개이면 그 중 하나를 골라 상세 패턴을 보게 한다.
    focus_station = st.selectbox('상세히 볼 역 선택', st.session_state.favorite_stations)

    fav_df = df[df['역명'] == focus_station]  # df[조건] --> 조건이 참인 데이터프레임만 거른다.

    st.subheader(f'{focus_station} - 승차/하차 합계')
    # observed=True : 실제 존재하는 조합만 그룹한다.
    total_by_type = fav_df.groupby('승하차', observed=True)['인원수'].sum()
    st.bar_chart(total_by_type)

    st.subheader(f'{focus_station} - 시간대별(5시~23시) 이용 패턴')
    # 시작시(정수)로 groupby -> x축이 자연스럽게 5,6,7,...시 순서로 정렬
    # (문자열인 시간대컬럼으로 정렬하면 '10시~11시'가 '1시~2시'보다 잘못 정렬되는 오류생긴다.)
    hourly = fav_df.groupby(['시작시', '승하차'], observed=True)['인원수'].sum().reset_index()
    hourly_pivot = hourly.pivot(index='시작시', columns='승하차', values='인원수')
    st.line_chart(hourly_pivot)