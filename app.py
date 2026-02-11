import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="가계부 대시보드", page_icon="💰", layout="wide")

# --- 카테고리 매핑 ---
CATEGORY_MAP = {
    "식비": {
        "대분류": "생활비",
        "keywords": ["식비", "음식", "식당", "배달", "카페", "커피", "편의점", "마트", "식료품", "반찬", "빵", "과일", "야채", "고기", "생선", "우유", "음료", "주류", "술", "치킨", "피자", "햄버거", "분식", "라면"]
    },
    "교통비": {
        "대분류": "생활비",
        "keywords": ["교통", "버스", "지하철", "택시", "주유", "기름", "톨게이트", "고속도로", "주차", "카카오택시", "우버", "티머니", "교통카드"]
    },
    "통신비": {
        "대분류": "고정비",
        "keywords": ["통신", "핸드폰", "인터넷", "휴대폰", "SKT", "KT", "LG", "요금"]
    },
    "주거비": {
        "대분류": "고정비",
        "keywords": ["월세", "관리비", "전기", "가스", "수도", "공과금", "아파트", "임대료"]
    },
    "쇼핑": {
        "대분류": "소비",
        "keywords": ["쇼핑", "옷", "의류", "신발", "가방", "쿠팡", "네이버", "무신사", "올리브영", "다이소", "화장품"]
    },
    "의료비": {
        "대분류": "생활비",
        "keywords": ["병원", "약국", "의료", "치과", "안과", "건강", "진료", "약"]
    },
    "문화/여가": {
        "대분류": "소비",
        "keywords": ["영화", "넷플릭스", "유튜브", "구독", "게임", "취미", "도서", "책", "공연", "여행", "숙박", "호텔", "항공"]
    },
    "교육": {
        "대분류": "자기계발",
        "keywords": ["교육", "학원", "강의", "수업", "도서", "책", "학습"]
    },
    "보험/금융": {
        "대분류": "고정비",
        "keywords": ["보험", "적금", "저축", "투자", "이자", "대출", "카드"]
    },
    "기타": {
        "대분류": "기타",
        "keywords": []
    }
}

def categorize_item(text: str) -> tuple[str, str]:
    """항목명으로 대분류/소분류 자동 분류"""
    if not isinstance(text, str):
        return ("기타", "기타")
    text_lower = text.lower()
    for sub_cat, info in CATEGORY_MAP.items():
        for kw in info["keywords"]:
            if kw in text_lower:
                return (info["대분류"], sub_cat)
    return ("기타", "기타")


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """데이터프레임 전처리 및 카테고리 자동 분류"""
    # 컬럼명 정리 (공백 제거)
    df.columns = df.columns.str.strip()
    
    # 날짜 컬럼 자동 감지 및 변환
    for col in df.columns:
        if any(k in col for k in ["날짜", "일자", "date", "Date"]):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
    # 금액 컬럼 자동 감지 및 숫자 변환
    for col in df.columns:
        if any(k in col for k in ["금액", "amount", "Amount", "지출", "수입", "원"]):
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.replace("원", "").str.strip(), errors="coerce")
    
    # 항목/내역 컬럼으로 카테고리 자동 분류
    item_col = None
    for col in df.columns:
        if any(k in col for k in ["항목", "내역", "적요", "메모", "내용", "사용처", "가맹점"]):
            item_col = col
            break
    
    if item_col and "대분류" not in df.columns:
        categories = df[item_col].apply(categorize_item)
        df["대분류"] = categories.apply(lambda x: x[0])
        df["소분류"] = categories.apply(lambda x: x[1])
    
    return df


# ============ UI ============

st.title("💰 가계부 대시보드")
st.caption("엑셀 업로드 → 자동 분류 → 표 & 차트")

# --- 세션 상태 초기화 ---
if "df" not in st.session_state:
    st.session_state.df = None

# --- 1. 엑셀 업로드 ---
st.sidebar.header("📂 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("엑셀 파일 (.xlsx, .xls)", type=["xlsx", "xls"])

if uploaded_file:
    try:
        raw_df = pd.read_excel(uploaded_file)
        st.session_state.df = process_dataframe(raw_df)
        st.sidebar.success(f"✅ {len(st.session_state.df)}건 로드 완료")
    except Exception as e:
        st.sidebar.error(f"파일 읽기 실패: {e}")

# --- 샘플 데이터 ---
if st.session_state.df is None:
    st.sidebar.markdown("---")
    if st.sidebar.button("📝 샘플 데이터로 시작"):
        sample = pd.DataFrame({
            "날짜": pd.date_range("2026-01-01", periods=20, freq="3D"),
            "항목": ["커피", "점심 식당", "버스", "쿠팡 쇼핑", "넷플릭스 구독", 
                     "전기세", "택시", "편의점", "치과 진료", "학원비",
                     "월세", "치킨 배달", "주유", "옷 구매", "약국",
                     "영화 관람", "인터넷 요금", "마트 장보기", "보험료", "카페"],
            "금액": [4500, 12000, 1400, 35000, 17000,
                    45000, 8800, 3200, 50000, 200000,
                    500000, 22000, 60000, 89000, 5600,
                    14000, 33000, 67000, 150000, 6500]
        })
        st.session_state.df = process_dataframe(sample)
        st.rerun()

if st.session_state.df is None:
    st.info("👈 사이드바에서 엑셀 파일을 업로드하거나 샘플 데이터로 시작하세요.")
    st.stop()

df = st.session_state.df

# --- 2. 데이터 편집 ---
st.subheader("📋 데이터 편집")
st.caption("셀을 클릭하여 직접 수정할 수 있습니다. 대분류/소분류도 변경 가능!")

# 카테고리 옵션
major_cats = list(set(v["대분류"] for v in CATEGORY_MAP.values()))
minor_cats = list(CATEGORY_MAP.keys())

column_config = {}
if "대분류" in df.columns:
    column_config["대분류"] = st.column_config.SelectboxColumn("대분류", options=major_cats)
if "소분류" in df.columns:
    column_config["소분류"] = st.column_config.SelectboxColumn("소분류", options=minor_cats)
for col in df.columns:
    if any(k in col for k in ["금액", "지출", "수입"]):
        column_config[col] = st.column_config.NumberColumn(col, format="₩%d")

edited_df = st.data_editor(
    df,
    column_config=column_config,
    num_rows="dynamic",
    use_container_width=True,
    key="data_editor"
)
st.session_state.df = edited_df
df = edited_df

# --- 3. 요약 & 차트 ---
st.markdown("---")
st.subheader("📊 분석 결과")

# 금액 컬럼 찾기
amount_col = None
for col in df.columns:
    if any(k in col for k in ["금액", "지출", "수입", "amount"]):
        amount_col = col
        break

if amount_col is None:
    st.warning("금액 컬럼을 찾을 수 없습니다. 컬럼명에 '금액' 또는 '지출'이 포함되어야 합니다.")
    st.stop()

# 총합 카드
col1, col2, col3 = st.columns(3)
total = df[amount_col].sum()
count = len(df)
avg = df[amount_col].mean()

col1.metric("💵 총 지출", f"₩{total:,.0f}")
col2.metric("📝 건수", f"{count}건")
col3.metric("📈 평균", f"₩{avg:,.0f}")

# 차트 레이아웃
chart_col1, chart_col2 = st.columns(2)

# 대분류별 파이차트
if "대분류" in df.columns:
    with chart_col1:
        st.markdown("#### 대분류별 지출")
        major_sum = df.groupby("대분류")[amount_col].sum().reset_index()
        fig1 = px.pie(major_sum, values=amount_col, names="대분류", hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig1.update_traces(textinfo="label+percent+value", texttemplate="%{label}<br>%{percent}<br>₩%{value:,.0f}")
        st.plotly_chart(fig1, use_container_width=True)

# 소분류별 바차트
if "소분류" in df.columns:
    with chart_col2:
        st.markdown("#### 소분류별 지출")
        minor_sum = df.groupby("소분류")[amount_col].sum().reset_index().sort_values(amount_col, ascending=True)
        fig2 = px.bar(minor_sum, x=amount_col, y="소분류", orientation="h",
                      color=amount_col, color_continuous_scale="Blues",
                      text=minor_sum[amount_col].apply(lambda x: f"₩{x:,.0f}"))
        fig2.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

# 날짜별 추이
date_col = None
for col in df.columns:
    if any(k in col for k in ["날짜", "일자", "date"]):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_col = col
            break

if date_col:
    st.markdown("#### 📅 일별 지출 추이")
    daily = df.groupby(df[date_col].dt.date)[amount_col].sum().reset_index()
    daily.columns = ["날짜", "금액"]
    fig3 = px.line(daily, x="날짜", y="금액", markers=True,
                   text=daily["금액"].apply(lambda x: f"₩{x:,.0f}"))
    fig3.update_traces(textposition="top center")
    fig3.update_layout(yaxis_tickformat=",")
    st.plotly_chart(fig3, use_container_width=True)

# 대분류/소분류 요약 테이블
if "대분류" in df.columns and "소분류" in df.columns:
    st.markdown("#### 📑 카테고리별 합계")
    summary = df.groupby(["대분류", "소분류"])[amount_col].agg(["sum", "count"]).reset_index()
    summary.columns = ["대분류", "소분류", "합계", "건수"]
    summary = summary.sort_values("합계", ascending=False)
    summary["합계"] = summary["합계"].apply(lambda x: f"₩{x:,.0f}")
    st.dataframe(summary, use_container_width=True, hide_index=True)

# --- 4. 다운로드 ---
st.markdown("---")
st.subheader("💾 다운로드")

buffer = BytesIO()
df.to_excel(buffer, index=False, engine="openpyxl")
st.download_button(
    label="📥 편집된 데이터 다운로드 (.xlsx)",
    data=buffer.getvalue(),
    file_name="가계부_편집본.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
