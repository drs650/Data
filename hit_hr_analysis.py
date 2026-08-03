"""
KBO 타자 데이터 분석: 안타 수와 홈런 수의 관계
가설
  H0(귀무가설): 안타 수와 홈런 수는 선형적인 관계가 없다.
  H1(대립가설): 안타 수가 증가할수록 홈런 수도 증가한다.

실행 전 준비:
  pip install pandas numpy scipy scikit-learn statsmodels matplotlib joblib
  '타자.csv' 파일을 이 스크립트와 같은 폴더에 두세요.
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt

CSV_PATH = "타자.csv"        # 데이터 파일 경로
MIN_PA = 100                  # 최소 타석 기준
RANDOM_STATE = 42
TEST_SIZE = 0.2


# ------------------------------------------------------------------
# 1단계. 전처리
# ------------------------------------------------------------------
def load_and_preprocess(path: str, min_pa: int) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    print(f"원본 shape: {df.shape}")

    # 표본 신뢰도를 위해 최소 타석 이상만 사용
    df_f = df[df["타석"] >= min_pa].copy()
    print(f"타석 {min_pa} 이상 필터링 후 shape: {df_f.shape}")

    print(f"결측치 개수: {df_f.isna().sum().sum()}")

    df_final = df_f[["선수", "팀", "타석", "안타", "홈런"]].reset_index(drop=True)
    return df_final


# ------------------------------------------------------------------
# 2단계. 데이터 분할 (지도학습 - 회귀이므로 Train/Test 분할)
# ------------------------------------------------------------------
def split_data(df: pd.DataFrame):
    X = df[["안타"]]
    y = df["홈런"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    print(f"Train: {X_train.shape[0]}명 / Test: {X_test.shape[0]}명")
    return X_train, X_test, y_train, y_test


# ------------------------------------------------------------------
# 3단계. 가설 검정 + 모델 개발
# ------------------------------------------------------------------
def hypothesis_test(df: pd.DataFrame, alpha: float = 0.05):
    r, p = stats.pearsonr(df["안타"], df["홈런"])
    print("\n=== 가설 검정 (피어슨 상관분석) ===")
    print(f"상관계수 r = {r:.4f}")
    print(f"p-value = {p:.6f}")
    if p < alpha:
        print(f"p < {alpha} → 귀무가설(H0) 기각 → 안타-홈런 간 유의한 선형관계 있음")
    else:
        print(f"p >= {alpha} → 귀무가설(H0) 채택 → 유의한 선형관계 없음")
    return r, p


def fit_ols(df: pd.DataFrame):
    X_sm = sm.add_constant(df["안타"])
    model = sm.OLS(df["홈런"], X_sm).fit()
    print("\n=== OLS 회귀 요약 (전체 데이터) ===")
    print(model.summary().tables[1])
    return model


def train_model(X_train, y_train, X_all, y_all):
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    print("\n=== scikit-learn LinearRegression ===")
    print(f"회귀식: 홈런 = {lr.coef_[0]:.4f} * 안타 + {lr.intercept_:.4f}")

    cv_scores = cross_val_score(lr, X_all, y_all, cv=5, scoring="r2")
    print(f"5-Fold 교차검증 R² 평균: {cv_scores.mean():.4f} (표준편차 {cv_scores.std():.4f})")
    return lr


# ------------------------------------------------------------------
# 4단계. 모델 성능 평가
# ------------------------------------------------------------------
def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)

    print("\n=== Test 데이터 성능 평가 ===")
    print(f"R² Score : {r2:.4f}")
    print(f"RMSE     : {rmse:.4f}")
    print(f"MAE      : {mae:.4f}")
    return r2, rmse, mae


def plot_results(df: pd.DataFrame, model, r: float, p: float, save_path: str):
    plt.rcParams["axes.unicode_minus"] = False
    # OS별 한글 폰트 자동 탐색 (없으면 기본 폰트로 진행 -> 한글이 깨질 수 있음)
    import platform
    import matplotlib.font_manager as fm

    system = platform.system()
    candidates = {
        "Windows": ["Malgun Gothic"],
        "Darwin": ["AppleGothic"],
        "Linux": ["NanumGothic", "Noto Sans CJK KR", "Noto Sans CJK JP"],
    }.get(system, [])

    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            break
    else:
        print("경고: 한글 폰트를 찾지 못했습니다. 그래프의 한글이 깨질 수 있습니다.")
        print("Windows/Mac은 보통 기본 내장 폰트로 해결되고, Linux는 'sudo apt install fonts-nanum' 등으로 설치하세요.")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    # 산점도 + 회귀선
    ax = axes[0]
    ax.scatter(df["안타"], df["홈런"], alpha=0.5, color="#2c7fb8", edgecolor="white", s=40)
    x_line = np.linspace(df["안타"].min(), df["안타"].max(), 100).reshape(-1, 1)
    y_line = model.predict(pd.DataFrame(x_line, columns=["안타"]))
    ax.plot(x_line, y_line, color="#e34a33", linewidth=2.5, label="회귀선")
    ax.set_xlabel("안타 수")
    ax.set_ylabel("홈런 수")
    ax.set_title(f"안타 수 vs 홈런 수 (n={len(df)})")
    ax.legend()
    ax.text(0.05, 0.92, f"r = {r:.4f}, p < 0.001" if p < 0.001 else f"r={r:.4f}, p={p:.4f}",
            transform=ax.transAxes, bbox=dict(facecolor="white", alpha=0.8))

    # 잔차 플롯
    ax2 = axes[1]
    residuals = df["홈런"] - model.predict(df[["안타"]])
    ax2.scatter(model.predict(df[["안타"]]), residuals, alpha=0.5, color="#31a354", edgecolor="white", s=40)
    ax2.axhline(0, color="#e34a33", linestyle="--", linewidth=2)
    ax2.set_xlabel("예측값 (홈런)")
    ax2.set_ylabel("잔차 (실제 - 예측)")
    ax2.set_title("잔차 플롯")

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n그래프 저장 완료: {save_path}")


# ------------------------------------------------------------------
# 실행
# ------------------------------------------------------------------
if __name__ == "__main__":
    df = load_and_preprocess(CSV_PATH, MIN_PA)
    X_train, X_test, y_train, y_test = split_data(df)

    r, p = hypothesis_test(df)
    ols_model = fit_ols(df)
    lr_model = train_model(X_train, y_train, df[["안타"]], df["홈런"])

    evaluate_model(lr_model, X_test, y_test)
    plot_results(df, lr_model, r, p, "hit_hr_analysis.png")
