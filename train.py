"""
작업일자 : 2026-08-03
작업자 : 석쌤
목적 : 통신 고객 이탈 분류 모델을 학습하고 평가, 결과와 모델을 저장한다.
데이터 파일 : ml_data/telecom_churn.csv

train.py 실행 --> streamlit 파일 실행

"""
# 라이브러리 불러오기
from pathlib import Path  # 경로 설정
import json  
import joblib  # 학습이 끝난 파이프라인(전처리+모델)을 파일로 저장하고 나중에 다시 불러오기 위해 사용
import pandas as pd
from sklearn.compose import ColumnTransformer  # 열마다 다른 전처리를 동시에 적용
from sklearn.ensemble import RandomForestClassifier # 랜덤포레스트 분류 모델
from sklearn.impute import SimpleImputer  # 결측치를 대표값(숫자는 중앙값, 범주형은 최빈값)으로 채운다.
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score # 평가지표들(분류)
from sklearn.model_selection import train_test_split # 학습/평가 데이터 분할
from sklearn.pipeline import Pipeline # 전처리+모델을 하나로 묶어서 학습/예측 코드 재현성 보장
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# 데이터 경로 설정
# __file__ : 현재 이 .py 파일 자신의 경로
# .resolve() : 상대경로를 절대경로 바꾸어준다 (어디서 실행하든지 안전)
# .parent : 파일이 들어있는 폴더
HERE = Path(__file__).resolve().parent
# C:\Users\Administrator\bigdata2026\data_analysis\ml_data\telecom_churn.csv
# print(HERE /'ml_data'/'telecom_churn.csv') 
DATA_PATH = HERE /'ml_data'/'telecom_churn.csv'
# print(HERE.parents[0]) # C:\Users\Administrator\bigdata2026
# print(HERE.parents[1]) # C:\Users\Administrator
# print(HERE.parents[2]) # C:\Users

# 학습된 모델과 평가지표를 이 파일이 있는 폴더(HERE) 바로 아래에 저장
MODEL_PATH = HERE / 'churn_model.joblib'
METRICS_PATH = HERE / 'metrics.json'

# 모델 입력으로 사용할 열(특성, 피처) 목록을 명시적으로 나열 (데이터 누수 방지)
FEATURES = ['usage_minutes', 'complaints', 'contract_months', 'monthly_fee', 'contract_type', 'region']

# 예측하려고 하는 정답(이탈 여부) 열 (타겟)
TARGET = 'churn'

# 특성(피처) 중 숫자형과 범주형(문자형) 구분 - 서로 다른 전처리가 필요하기 때문에
NUMERIC = ['usage_minutes', 'complaints', 'contract_months', 'monthly_fee']
CATEGORICAL = ['contract_type', 'region']

# 파이프라인 구성 
def build_pipeline() -> Pipeline:
    """전처리와 모델을 하나로 묶어 학습,api의 처리"""

    # --- 숫자형 특성(피처, 컬럼) 처리 파이프라인 ---
    numeric_pipe = Pipeline([
        # 결측치를 채운다 -> 중앙값으로 채운다.
        ('imputer', SimpleImputer(strategy='median')),
        # 표준화로 스케일링 : monthly_fee(수만원 단위), complaints(0~5정도의 단위)처럼 단위차이가 클 때 사용
        ('scaler', StandardScaler())
    ])

    # --- 범주형(문자형) 특성 처리 파이프라인 ---
    category_pipe = Pipeline([
        # 결측치를 채운다 -> 최빈값으로 채운다.
        ('imputer', SimpleImputer(strategy='most_frequent')),
        # 원-핫 인코딩 : 문자열 카테고리를 0 / 1로 변환 
        #   판다스의 get_dummies()는 그때그때 다른 열을 만든다.
        #   사이킷런의 OneHotEncoder는 학습 시점의 규칙을 기억한다. 벡터로 처리, 파이프라인 단위로 할 때 편리하다.
        #   handle_unknown='ignore' : 처음 보는 값이 들어오면, 새 컬럼을 만드는 대신 설정에 따라 
        #       모든 값이 0인 벡터로 처리한다.
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ]) 

    # --- 컬럼별로 다른 전처리를 동시에 적용 ---
    # ColumnTransformer : "이 열은 numberic_pip로, 저 열은 category_pipe로 한 번에 지정해서 병렬 처리"
    preprocessor = ColumnTransformer([
        ('numeric', numeric_pipe, NUMERIC),
        ('category', category_pipe, CATEGORICAL)
    ])

    # --- 모델 정의 ---
    model = RandomForestClassifier(
        n_estimators=300,
        class_weight='balanced', # 이탈(1), 비이탈(0)보다 적은 불균형 데이터 보정
        random_state=42,
        min_samples_leaf=3  # 리프 노드 최소 샘플수 (과적합 억제)
    )

    # 전처리 + 모델을 하나의 파이프라인으로 묶어서 반환
    return Pipeline([('preprocess', preprocessor), ('model', model)])

def train() -> dict:
    """재현 가능한 분할로 모델을 학습하고, 실무 설명용 지표를 반환한다."""

    # CSV 파일을 읽어 데이터프레임으로 저장
    data = pd.read_csv(DATA_PATH)

    # 입력(X), 정답(y) 분리 --> X, y = data[FEATURES], data[TARGET]
    X = data[FEATURES]
    y = data[TARGET]

    # 학습용/평가용 데이터 분할 --> 전체의 25%를 평가용
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # 파이프라인 생성 후 학습 데이터로 학습
    pipeline = build_pipeline()  # 함수 호출
    pipeline.fit(X_train, y_train)

    # predict_proba() : 각 클래스(0, 1)에 속할 확률을 반환 (0:이탈 안한다. 1:이탈 한다.)
    #                   [:, 1] 모든행, 1번 컬럼
    #                   이탈할 확률을 알고 싶다. 
    probabilities = pipeline.predict_proba(X_test)[:, 1]

    # 확률이 0.5이상이면 이탈(1), 미만이면 비이탈(0)으로 최종 분류
    predictions = (probabilities >= 0.5).astype(int)  # int형변환

    # 정밀도(precision), 재현율(recall), f1-score 등을 클래스별로 계산 -> 보고서
    # output_dict=True : 딕셔너리 형태로 받아서 이후 코드에서 값을 꺼낼때 쓰기 쉽게 한다.
    # zero_division=0 : 분모가 0이 되는 경우(예측이 한쪽으로 쏠릴 때) 에러 대신 0 반환
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)

    # {
    # "0": {"precision": 0.95, "recall": 0.92, "f1-score": 0.93, "support": 800},
    # "1": {"precision": 0.78, "recall": 0.81, "f1-score": 0.79, "support": 200},
    # "accuracy": 0.90,
    # "macro avg": {...},
    # "weighted avg": {...}
    # }   


    # 보고용으로 핵심 지료만 정리
    metrics = {
        'test_rows': len(X_test), 
        # roc_auc : 0.5(랜덤 수준)~1.0(완벽) 사이 값, 임계값(0.5)에 상관없이 모델의 전반적인 분류 성능을
        #           보여주는 지표
        # round(숫자, 4) : 숫자를 소수 넷째자리까지 반올림
        # float()를 붙여서 형변환을 하는 이유 : 파이썬의 기본 float이 아니라, numpy.float64 타입이라서
        'roc_auc': round(float(roc_auc_score(y_test, probabilities)), 4),
        # recall_churn : <재현율> 실제 이탈 고객 중 몇 %를 잡아냈나? -> 이탈 예측에서는 이 값이 아주 중요!
        #               (놓치면 안되는 고객이므로)
        'recall_churn': round(float(report['1']['recall']), 4),
        # precision_churn : <정밀도> 이탈이라고 예측한 것 중 몇 %가 실제 이탈이었나?
        'precision_churn': round(float(report['1']['precision']), 4),
        # .tolist() : numpy 배열은 JSON으로 저장할 수 없어서 파이썬 리스트로 변환
        'confusion_matrix': confusion_matrix(y_test, predictions).tolist()
    }

    # 학습된 파이프라인(전처리+모델) 파일로 저장
    joblib.dump(pipeline, MODEL_PATH)

    # 평가 지표를 사람이 있을 수 있도록 JSON 파일로 저장
    # ensure_ascii=False : 한글이 유니코드의 escape(\uXXXXX)로 깨지지 않고, 그대로 저장
    # indent=2 : 들여쓰기 2칸으로 보기 좋게 저장
    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8-sig')

    return metrics

if __name__ == '__main__':
    # 이 파일을 직접 python train.py 형태로 실행했을 때만 동작
    # (다른 파일에서 import해서 train()함수만 가져다 쓸 때는 실행되지 않는다.)
    print(json.dumps(train(), ensure_ascii=False, indent=2))