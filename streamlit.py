"""








"""
# 라이브러리 불러오기
from pathlib import Path
import joblib
import pandas as pd
import streamlit as st

# 경로 설정
MODEL_PATH = Path(__file__).resolve().parent / 'churn_model.joblib'

# 브라우저 탭 제목과 아이콘 설정 - 반드시 다른 st.명령어보다 먼저 호출해야 한다.
st.set_page_config(page_title='실습:고객 이탈 위험', page_icon='')

st.title('고객 이탈 조기 경보')
st.caption('상담 우선순위를 정하기 위한 의사결정 보고 도구이며, 예측만으로 불이익을 주면 안됩니다.')

# 모델 파일이 존재하는지 먼저 확인
if not MODEL_PATH.exists():
    st.error('모델 파일이 없습니다. 터미널에서 `python train.py`를 먼저 실행하세요')
    st.stop()  # 이 지점에서 스크립트 실행을 완전히 중단 (추가 에러 방지)

# 저장했던 전처리 + 모델 그대로 복원
model = joblib.load(MODEL_PATH)

with st.form('customer'):
    # number_input 위젯 : (레이블, 최솟값, 최댓값, 기본값)
    usage = st.number_input('월 사용 시간(분)', 0.0, 10000.0, 250.0)
    complaints = st.number_input('최근 불만 횟수', 0, 100, 2)
    months = st.number_input('계약 유지 개월', 0, 120, 12)
    fee = st.number_input('월 요금', 0.1, 10000.0, 69.9)

    # selectbox 위젯 : 미리 정해진 값 중 하나만 고르게 한다.
    #                train.py에서 학습할 때 지정한 데이터와 같아야 한다.
    contract = st.selectbox('계약 유형', ['month-to-month', 'one-year', 'two-year'])
    region = st.selectbox('지역', ['Seoul', 'Gyenggi', 'Other'])

    # form_submit_button : 폼 안에서 유일학 ㅔ실행을 시작하게 하는 버튼
    submitted = st.form_submit_button('위험 예측')

# 버튼을 클릭했다면
if submitted:
    # 사용자가 입력한 값들로 1행짜리 데이터프레임 생성
    row = pd.DataFrame([{
        'usage_minutes': usage,
        'complaints': complaints,
        'contract_months': months,
        'monthly_fee': fee,
        'contract_type': contract,
        'region': region
    }])

    # predict_proba(row): [[비이탈 확률, 이탈확률]] 형태의 2차원 배열 반환
    # [0, 1] : 0번째 행(유일한 입력 고객), 1번째 열 (이탈=1일 확률)
    probability = float(model.predict_proba(row)[0, 1])

    # st.metric 위젯 : 큰 숫자 형태로 강조 표시
    st.metric('예상 이탈 확률 : ', f'{probability:.1%}')

    st.progress(probability) # 0~1 사이의 값을 막대 형태로 시각화

    st.info('확률이 높다면 고객의 실제 불편을 먼저 확인하고 적절한 유지 상담을 진행하세요.')