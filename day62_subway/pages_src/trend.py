'''
day62_subway/pages_src/trend.py

작성일 : 26-08-06
작성자 : 수완
목적 : 전체 역 기준으로 "일별 추이"와 "요일/주말-평일 패턴"을 함께 보여주는 페이지
        
'''
import streamlit as st
from data_loader import load_subway

st.title('기간, 시간대 추이')

df = load_subway()  # 데이터 불러오기

ride_type = st.radio('구분 선택', ['승차', '하차'], horizontal=True)
filtered = df[df['승하차'] == ride_type]

# --- 일별 추이 (365일 전체를 하루 단위로 합산) ---
st.subheader('일별 추이')
daily_total = filtered.groupby('날짜')['인원수'].sum()
st.line_chart(daily_total)

# --- 요일별 평균 (월~일 순서 고정)
st.subheader('요일별 평균 이용객 수')
weekday_avg = filtered.groupby('요일코드', observed=True)['인원수'].mean()
st.bar_chart(weekday_avg)

# --- 주말 vs 평일 시간대별 패턴 비교 ---
st.subheader('평일 vs 주말 - 시간대별 패턴 비교')
hourly = (
    filtered.groupby(['시작시', '주말여부'], observed=True)['인원수'].mean().reset_index()
)
# 주말여부(True/Flase)를 사람이 읽기 쉬운 레이블로 바꾼다.
hourly['구분'] = hourly['주말여부'].map({True: '주말', False: '평일'})
hourly_pivot = hourly.pivot(index='시작시', columns='구분', values='인원수')
st.line_chart(hourly_pivot)

# --- 역별로 나눠서 비교하기 (일별 추이, 상위 인기역 기본 선택) ---
st.subheader('역별로 나눠서 비교하기')
top_stations = (
    df.groupby('역명', observed=True)['인원수'].sum().nlargest(20).index.tolist()
)
compare_stations = st.multiselect(
    '비교할 역 선택 (인원수 상위 20개 역 중에서, 최대 5개 권장)',
    options=top_stations,
    default=top_stations[:3],
)

if compare_stations:
    compare_df = filtered[filtered['역명'].isin(compare_stations)]
    pivot = compare_df.pivot_table(index='날짜', columns='역명', values='인원수', aggfunc='sum')
    st.line_chart(pivot)

st.session_state.last_viewed_ride_type = ride_type
