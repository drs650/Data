'''
day62_subway/pages_src/home.py

작성일 : 26-08-06
작성자 : 수완
목적 : 앱의 첫 화면

'''
import streamlit as st
from data_loader import load_subway

st.title('대구 지하철 승하차 통합 대시보드')

df = load_subway()

year_min, year_max = df['날짜'].dt.year.min(), df['날짜'].dt.year.max()
year_label = f'{year_min}년' if year_min == year_max else f'{year_min}~{year_max}년'

with st.sidebar:
    st.header('데이터 요약 필터')

    all_stations = sorted(df['역명'].unique())
    top10_default = df.groupby('역명', observed=True)['인원수'].sum().nlargest(10).index.to_list()
    picked = st.multiselect(
        '요약에 포함할 역',
        options = all_stations,
        default = top10_default,
    )
    weekend_only = st.checkbox('주말(토,일)만 보기')

# 사이드바 조건 적용
summary_df = df[df['역명'].isin(picked)] if picked else df.iloc[0:0]
if weekend_only:
    summary_df = summary_df[summary_df['주말여부']]

# --- 본문 ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric('선택된 역 수', f'{len(picked)}개')
with col2:
    total_passengers = int(summary_df['인원수'].sum())
    st.metric('합계 인원(선택 기준)', f'{total_passengers}명')
with col3:
    st.metric('데이터 기간', f'{df["날짜"].min().date()} ~ {df["날짜"].max().date()}')

st.divider()

# --- 탭 ---
tab1, tab2 = st.tabs(['표로 보기', '그래프로 보기'])
with tab1:
    st.dataframe(
        summary_df.sort_values('날짜', ascending=False).head(30)[['날짜', '역명', '승하차', '시간대컬럼', '인원수', '요일코드']]
    )

with tab2:
    if not summary_df.empty:
        chart_data = (
            summary_df.groupby('역명', observed=True)['인원수'].sum().sort_values(ascending=False)
        )
        st.bar_chart(chart_data)
    else:
        st.info('사이드바에서 역을 하나 이상 선택해주세요.')