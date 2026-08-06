'''
day62_subway/pages_src/about.py

작성일 : 26-08-06
작성자 : 수완
목적 : 다른 페이지에서 st.session_state에 저장해둔 값들을 여기서 그대로 읽어올 수 있는지
        확인 --> st.session_state가 페이지를 넘어가도 유지된다라는 점을 알아두자.
        
'''
import streamlit as st

st.title('소개')
st.write('대구 지하철 시간대별 승하차 데이터를 활용한 Streamlit 통합 실습 맵입니다.')

st.subheader('지금까지 다른화면에서 남긴 흔적')

if 'favorite_stations' in st.session_state and st.session_state.favorite_stations:
    st.write('즐겨찾는 역:', st.session_state.favorite_stations)
else:
    st.write('즐겨찾는 역: 아직 없습니다. "역별 탐색"화면에서 추가해보세요')

if 'last_viewed_ride_type' in st.session_state:
    st.write('마지막으로 본 추이 구분:', st.session_state.lase_viewed_ride_type)
else:
    st.write('아직 "기간, 시간대 추이" 화면을 방문하지 않았습니다.')

if 'last_search_result' in st.session_state:
    st.write('마지막 검색 결과 건수:', len(st.session_state.last_search_result))
else:
    st.write('아직 "검색(폼)" 화면에서 검색을 실행하지 않았습니다.')