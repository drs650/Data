'''
day62_subway/pages_src/search.py

작성일 : 26-08-06
작성자 : 수완
목적 : 폼 안에 입력 위젯들(역 이름, 승하구분, 기간, 시작시 범위, 요일) --> 조건들을 조작할 때마다
        재실행되지 않고 "검색"버튼을 누르는 순간에만 한 번에 처리되도록 폼을 사용
        
        만약에 데이터가 많을 때 폼 없이 위젯을 조작하면 필터링을 다시 하면 체감 속도가
        느려진다. --> st.form을 사용한다.
        
'''
import pandas as pd
import streamlit as st
from data_loader import load_subway, WEEKDAY_ORDER

st.title('조건 검색 - st.form 위젯 사용')

df = load_subway()

with st.form('subway_search_form'):
    col1, col2 = st.columns(2) # 세로 2칸 (1:1 비율)
    with col1:
        keyword = st.text_input('역 이름(일부만 입력 가능, 비워두면 전체)')
    with col2:
        ride_type = st.selectbox('구분', ['전체', '승차', '하차'])

    date_range = st.date_input('조회 기간',
                               value=(df['날짜'].min(), df['날짜'].max()),
                               min_value=df['날짜'].min(),
                               max_value=df['날짜'].max(),
    )

    # 슬라이더 위젯
    hour_range = st.slider('조회 시간대 (시작시 기준)',
                           min_value=5,
                           max_value=23,
                           value=(5, 23))

    # 멀티 셀렉트 위젯
    weekday_pick = st.multiselect(
        '요일',
        options=WEEKDAY_ORDER,
        default=WEEKDAY_ORDER
    )

    # 버튼 - 폼 안에서 버튼은 st.form_submit_button
    submitted = st.form_submit_button('검색 실행')

# 버튼을 눌렀다면
if submitted:
    filtered = df.copy()

    if keyword:
        filtered = filtered[filtered['역명'].str.contains(keyword)]

    if ride_type != '전체':
        filtered = filtered[filtered['승하차'] == ride_type]

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[
            (filtered['날짜'] >= pd.to_datetime(start)) &
            (filtered['날짜'] <= pd.to_datetime(end))
        ]

    # 슬라이더는 (최솟값, 최댓값) 튜플을 반환 -> 시작시가 그 범위 안에 있는 행만 남김
    filtered = filtered[
        (filtered['시작시'] >= hour_range[0]) & (filtered['시작시'] <= hour_range[1])
    ]

    if weekday_pick:
        filtered = filtered[filtered['요일코드'].isin(weekday_pick)]

    # about.py에서 확인할 수 있도록 세션에 저장
    st.session_state.last_search_result = filtered

    st.write(f'검색 결과 : {len(filtered):,}건')
    # 표는 상위 500행만 보여주고 다운로드는 전체 제공
    st.dataframe(
        filtered.sort_values('날짜', ascending=False)
        .head(500)[['날짜', '역명', '승하차', '시간대컬럼', '인원수', '요일코드', '주말여부']]
    )
    if len(filtered) > 500:
        st.caption(f'표에는 상위 500건만 표시됩니다. 전체 {len(filtered):,}건은 아래 버튼으로 다운로드 하세요. ')

    csv_bytes = filtered.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        '검색 결과 CSV 다운로드',
        data=csv_bytes,
        file_name='subway_search_result.csv',
        mime='text/csv',
    )
