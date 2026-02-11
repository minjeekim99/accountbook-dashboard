import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from collections import OrderedDict

st.set_page_config(page_title="가계부 대시보드", page_icon="💰", layout="wide")

# --- 카테고리 체계 (대분류 → 소분류 리스트) ---
CATEGORY_TREE: OrderedDict[str, list[str]] = OrderedDict([
    ("금융보험비", ["보험료", "금융이자", "적금", "상환금", "상품권", "투자", "연금"]),
    ("식비", ["식사/간식", "차/커피", "회사점심", "식재료"]),
    ("주거생활비", ["집세/관리비", "통신비", "기타세금", "전자기기"]),
    ("생활용품비", ["생활용품", "더모아충전"]),
    ("의류미용비", ["의류/잡화", "미용"]),
    ("문화생활비", ["영화/공연/OTT/전시", "게임/음악", "전자제품", "도서"]),
    ("건강관리비", ["운동/다이어트", "병원/약값", "기타요양", "보험청구"]),
    ("교통비", ["대중교통", "택시비", "장거리경비"]),
    ("학비", ["학원/강의", "교재비", "모임공간이용료", "문구류", "응시료", "유학수속관련비용"]),
    ("사회생활비", ["경조사비", "선물/용돈", "모임회비"]),
    ("유흥비", ["술값", "기타유흥"]),
    ("사업", ["고정지출비", "초기투자비"]),
    ("생활유지비", ["기름값", "정비/세차", "주차/통행", "자동차", "보험료",
                  "과외관련비용", "이사비용", "세탁비", "고정비/구독료"]),
])

# 전체 대분류 리스트
ALL_MAJOR = list(CATEGORY_TREE.keys())
# 전체 소분류 리스트 (중복 제거)
ALL_MINOR = list(dict.fromkeys(sub for subs in CATEGORY_TREE.values() for sub in subs))

# 키워드 → (대분류, 소분류) 자동 매핑
AUTO_CLASSIFY = {
    "커피": ("식비", "차/커피"), "카페": ("식비", "차/커피"), "스타벅스": ("식비", "차/커피"),
    "점심": ("식비", "회사점심"), "식당": ("식비", "식사/간식"), "배달": ("식비", "식사/간식"),
    "편의점": ("식비", "식사/간식"), "마트": ("식비", "식재료"), "식료품": ("식비", "식재료"),
    "치킨": ("식비", "식사/간식"), "피자": ("식비", "식사/간식"), "빵": ("식비", "식사/간식"),
    "버스": ("교통비", "대중교통"), "지하철": ("교통비", "대중교통"), "교통": ("교통비", "대중교통"),
    "택시": ("교통비", "택시비"), "카카오택시": ("교통비", "택시비"),
    "주유": ("생활유지비", "기름값"), "기름": ("생활유지비", "기름값"),
    "세차": ("생활유지비", "정비/세차"), "정비": ("생활유지비", "정비/세차"),
    "주차": ("생활유지비", "주차/통행"), "톨게이트": ("생활유지비", "주차/통행"),
    "넷플릭스": ("문화생활", "영화/공연/OTT/전시"), "영화": ("문화생활", "영화/공연/OTT/전시"),
    "유튜브": ("문화생활", "영화/공연/OTT/전시"), "구독": ("생활유지비", "고정비/구독료"),
    "게임": ("문화생활", "게임/음악"), "도서": ("문화생활", "도서"), "책": ("문화생활", "도서"),
    "옷": ("의료미용비(쇼핑)", "의류/잡화"), "의류": ("의료미용비(쇼핑)", "의류/잡화"),
    "쇼핑": ("의료미용비(쇼핑)", "의류/잡화"), "쿠팡": ("의료미용비(쇼핑)", "의류/잡화"),
    "무신사": ("의료미용비(쇼핑)", "의류/잡화"), "올리브영": ("의료미용비(쇼핑)", "미용"),
    "화장품": ("의료미용비(쇼핑)", "미용"),
    "병원": ("건강관리비", "병원/약값"), "약국": ("건강관리비", "병원/약값"),
    "치과": ("건강관리비", "병원/약값"), "안과": ("건강관리비", "병원/약값"),
    "운동": ("건강관리비", "운동/다이어트"), "헬스": ("건강관리비", "운동/다이어트"),
    "월세": ("주거생활비", "집세/관리비"), "관리비": ("주거생활비", "집세/관리비"),
    "전기": ("주거생활비", "집세/관리비"), "가스": ("주거생활비", "집세/관리비"),
    "통신": ("주거생활비", "통신비"), "핸드폰": ("주거생활비", "통신비"),
    "인터넷": ("주거생활비", "통신비"),
    "학원": ("학비", "학원/강의"), "강의": ("학비", "학원/강의"),
    "보험": ("금융보험비", "보험료"), "적금": ("금융보험비", "적금"),
    "이자": ("금융보험비", "금융이자"), "대출": ("금융보험비", "상환금"),
    "술": ("유흥비", "술값"), "회식": ("유흥비", "술값"),
    "선물": ("사회생활비", "선물/용돈"), "축의금": ("사회생활비", "경조사비"),
    "여행": ("여행비", "취미"), "숙박": ("여행비", "취미"), "항공": ("여행비", "취미"),
}


def categorize_item(text: str) -> tuple[str, str]:
    """항목명으로 대분류/소분류 자동 분류"""
    if not isinstance(text, str):
        return ("기타", "시발/멍청비용")
    text_lower = text.lower()
    for kw, (major, minor) in AUTO_CLASSIFY.items():
        if kw in text_lower:
            return (major, minor)
    return ("기타", "시발/멍청비용")


# --- 고정 칼럼 매핑 (위치 기반) ---
COLUMN_RENAME = {
    0: "날짜",
    1: "결제수단",
    2: "항목",
    3: "이용금액",
    4: "대분류",
    5: "소분류",
    6: "할부/회차",
    7: "적립/할인율",
    8: "예상적립 / 할인",
    9: "결제원금",
    10: "결제 후 잔액",
}
EXPECTED_COLS = list(COLUMN_RENAME.values())


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """데이터프레임 전처리 및 카테고리 자동 분류"""
    # 1) 완전히 비어있는 열 먼저 제거
    df = df.dropna(axis=1, how="all")
    # 열 이름이 전부 NaN이거나 빈 문자열인 열도 제거
    df = df.loc[:, ~df.columns.astype(str).str.match(r"^\s*$")]
    
    # 2) 칼럼 수에 맞춰 이름 강제 지정
    new_cols = []
    for i in range(len(df.columns)):
        if i in COLUMN_RENAME:
            new_cols.append(COLUMN_RENAME[i])
        else:
            new_cols.append(f"_drop_{i}")
    df.columns = new_cols
    df = df.loc[:, ~df.columns.str.startswith("_drop_")]
    
    # 3) 헤더/비데이터 행 제거 — 이용금액이 숫자가 아닌 행 삭제
    if "이용금액" in df.columns:
        def is_not_number(v):
            if pd.isna(v):
                return True
            try:
                float(str(v).replace(",", "").replace("원", "").strip())
                return False
            except (ValueError, TypeError):
                return True
        mask = df["이용금액"].apply(is_not_number)
        df = df[~mask].reset_index(drop=True)
    
    # 4) 완전히 비어있는 행 제거
    df = df.dropna(how="all").reset_index(drop=True)
    
    # 5) 날짜 변환
    if "날짜" in df.columns:
        def parse_date(v):
            if pd.isna(v):
                return pd.NaT
            # 이미 datetime이면 그대로
            if isinstance(v, pd.Timestamp):
                return v
            s = str(v).strip()
            if not s:
                return pd.NaT
            # 엑셀 시리얼 넘버
            try:
                num = float(s)
                if 1 < num < 100000:
                    return pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(num))
            except (ValueError, TypeError):
                pass
            # 다양한 날짜 포맷
            for fmt in ["%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%m/%d/%Y",
                        "%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M",
                        "%Y년 %m월 %d일", "%Y년%m월%d일"]:
                try:
                    return pd.to_datetime(s, format=fmt)
                except (ValueError, TypeError):
                    continue
            return pd.to_datetime(s, errors="coerce")
        df["날짜"] = df["날짜"].apply(parse_date)
    
    # 6) 금액 컬럼 숫자 변환
    money_cols = ["이용금액", "예상적립 / 할인", "결제원금", "결제 후 잔액"]
    for col in money_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "").str.replace("원", "").str.strip(),
                errors="coerce"
            )
    
    # 7) 대분류/소분류 자동 분류 (비어있는 셀만)
    item_col = "항목" if "항목" in df.columns else None
    if item_col:
        categories = df[item_col].apply(categorize_item)
        if "대분류" not in df.columns:
            df["대분류"] = categories.apply(lambda x: x[0])
        else:
            mask = df["대분류"].isna() | (df["대분류"].astype(str).str.strip() == "")
            df.loc[mask, "대분류"] = categories[mask].apply(lambda x: x[0])
        if "소분류" not in df.columns:
            df["소분류"] = categories.apply(lambda x: x[1])
        else:
            mask = df["소분류"].isna() | (df["소분류"].astype(str).str.strip() == "")
            df.loc[mask, "소분류"] = categories[mask].apply(lambda x: x[1])
    
    # 대분류/소분류를 문자열로 통일 (NaN → 빈 문자열)
    if "대분류" in df.columns:
        df["대분류"] = df["대분류"].fillna("").astype(str).str.strip()
    if "소분류" in df.columns:
        df["소분류"] = df["소분류"].fillna("").astype(str).str.strip()
    
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
        raw_df = pd.read_excel(uploaded_file, header=None)
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
            "결제수단": ["신용카드"] * 20,
            "항목": ["커피", "점심 식당", "버스", "쿠팡 쇼핑", "넷플릭스 구독",
                     "전기세", "택시", "편의점", "치과 진료", "학원비",
                     "월세", "치킨 배달", "주유", "옷 구매", "약국",
                     "영화 관람", "인터넷 요금", "마트 장보기", "보험료", "카페"],
            "이용금액": [4500, 12000, 1400, 35000, 17000,
                      45000, 8800, 3200, 50000, 200000,
                      500000, 22000, 60000, 89000, 5600,
                      14000, 33000, 67000, 150000, 6500],
            "대분류": [""] * 20,
            "소분류": [""] * 20,
        })
        st.session_state.df = process_dataframe(sample)
        st.rerun()

if st.session_state.df is None:
    st.info("👈 사이드바에서 엑셀 파일을 업로드하거나 샘플 데이터로 시작하세요.")
    st.stop()

df = st.session_state.df

# --- 2. 데이터 편집 ---
st.subheader("📋 데이터")
st.caption("대분류/소분류를 드롭다운에서 선택하세요. 소분류가 대분류에 안 맞으면 자동 교정됩니다.")

PAYMENT_METHODS = [
    "", "계좌이체", "현금", "롯데카드신용", "온누리상품권체크", "신한카드-더모아",
    "신한은행", "우리체크카드", "우리카드", "PAYCO", "현대카드", "현아플",
    "새마을금고", "네이버페이", "카카오뱅크", "모빌리언스카드", "삼성카드",
    "롯데체크카드", "신한카드", "KB국민카드", "우리카드연세", "우리은행",
    "케이뱅크", "지역화페", "카카오페이", "롯데카드", "온누리상품권",
]

column_config = {}
if "결제수단" in df.columns:
    existing_pay = [str(v).strip() for v in df["결제수단"].dropna().unique() if str(v).strip()]
    pay_options = list(dict.fromkeys(PAYMENT_METHODS + existing_pay))
    column_config["결제수단"] = st.column_config.SelectboxColumn(
        "결제수단", options=pay_options, required=False,
    )
if "대분류" in df.columns:
    column_config["대분류"] = st.column_config.SelectboxColumn(
        "대분류", options=[""] + ALL_MAJOR, required=False,
    )
if "소분류" in df.columns:
    # 기존 데이터에 있는 소분류 값도 옵션에 포함 (없는 값이 있으면 드롭다운이 안 뜰 수 있음)
    existing_minor = [str(v).strip() for v in df["소분류"].dropna().unique() if str(v).strip()]
    all_minor_options = list(dict.fromkeys([""] + ALL_MINOR + existing_minor))
    column_config["소분류"] = st.column_config.SelectboxColumn(
        "소분류", options=all_minor_options, required=False,
    )
for col in ["이용금액", "결제원금", "결제 후 잔액", "예상적립 / 할인"]:
    if col in df.columns:
        column_config[col] = st.column_config.NumberColumn(col, format="₩%d")
if "날짜" in df.columns:
    column_config["날짜"] = st.column_config.DateColumn("날짜")

edited_df = st.data_editor(
    df, column_config=column_config, num_rows="dynamic",
    use_container_width=True, key="data_editor"
)

# 대분류-소분류 자동 교정: 소분류가 대분류에 안 맞으면 해당 대분류의 첫 번째 소분류로 변경
if "대분류" in edited_df.columns and "소분류" in edited_df.columns:
    corrected = False
    for idx in edited_df.index:
        major = str(edited_df.at[idx, "대분류"]).strip()
        minor = str(edited_df.at[idx, "소분류"]).strip()
        if major in CATEGORY_TREE and minor not in CATEGORY_TREE[major]:
            edited_df.at[idx, "소분류"] = CATEGORY_TREE[major][0]
            corrected = True
    if corrected:
        st.info("ℹ️ 대분류에 맞지 않는 소분류가 자동 교정되었습니다.")

st.session_state.df = edited_df
df = edited_df

# --- 카테고리 편집 (종속 드롭다운) ---
if "대분류" in df.columns and "소분류" in df.columns and len(df) > 0:
    st.markdown("---")
    st.subheader("🏷️ 카테고리 편집")
    st.caption("대분류를 선택하면 소분류가 자동으로 바뀝니다.")

    row_options = list(df.index)
    def fmt_row(i):
        item = df.at[i, "항목"] if "항목" in df.columns else ""
        return f"[{i}] {item} — {df.at[i, '대분류']}/{df.at[i, '소분류']}"

    selected = st.selectbox("1️⃣ 행 선택", row_options, format_func=fmt_row, key="row_sel")
    picked_major = st.selectbox("2️⃣ 대분류", ALL_MAJOR, key="pick_major")
    sub_options = CATEGORY_TREE.get(picked_major, ["기타"])
    picked_minor = st.selectbox("3️⃣ 소분류", sub_options, key="pick_minor")

    if st.button("✅ 적용"):
        st.session_state.df.at[selected, "대분류"] = picked_major
        st.session_state.df.at[selected, "소분류"] = picked_minor
        st.toast(f"✅ 행 {selected} → {picked_major} / {picked_minor}")
        st.rerun()

    with st.expander("📦 일괄 편집"):
        bulk_rows = st.multiselect("행 선택", row_options, format_func=fmt_row, key="bulk_rows")
        if bulk_rows:
            b_major = st.selectbox("대분류", ALL_MAJOR, key="bulk_major")
            b_sub_options = CATEGORY_TREE.get(b_major, ["기타"])
            b_minor = st.selectbox("소분류", b_sub_options, key="bulk_minor")
            if st.button(f"✅ {len(bulk_rows)}건 적용", key="bulk_apply"):
                for ri in bulk_rows:
                    st.session_state.df.at[ri, "대분류"] = b_major
                    st.session_state.df.at[ri, "소분류"] = b_minor
                st.toast(f"✅ {len(bulk_rows)}건 → {b_major} / {b_minor}")
                st.rerun()

    df = st.session_state.df

# --- 3. 요약 & 차트 ---
st.markdown("---")
st.subheader("📊 분석 결과")

amount_col = "이용금액" if "이용금액" in df.columns else None
if amount_col is None:
    for col in df.columns:
        if any(k in col for k in ["금액", "지출", "수입", "amount"]):
            amount_col = col
            break

if amount_col is None:
    st.warning("금액 컬럼을 찾을 수 없습니다.")
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

if "대분류" in df.columns:
    with chart_col1:
        st.markdown("#### 대분류별 지출")
        major_sum = df.groupby("대분류")[amount_col].sum().reset_index()
        major_sum = major_sum[major_sum[amount_col] > 0]
        fig1 = px.pie(major_sum, values=amount_col, names="대분류", hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig1.update_traces(textinfo="label+percent+value",
                          texttemplate="%{label}<br>%{percent}<br>₩%{value:,.0f}")
        st.plotly_chart(fig1, use_container_width=True)

if "소분류" in df.columns:
    with chart_col2:
        st.markdown("#### 소분류별 지출")
        minor_sum = df.groupby("소분류")[amount_col].sum().reset_index()
        minor_sum = minor_sum[minor_sum[amount_col] > 0].sort_values(amount_col, ascending=True)
        fig2 = px.bar(minor_sum, x=amount_col, y="소분류", orientation="h",
                      color=amount_col, color_continuous_scale="Blues",
                      text=minor_sum[amount_col].apply(lambda x: f"₩{x:,.0f}"))
        fig2.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

# 날짜별 추이
if "날짜" in df.columns and pd.api.types.is_datetime64_any_dtype(df["날짜"]):
    valid_dates = df.dropna(subset=["날짜"])
    if len(valid_dates) > 0:
        st.markdown("#### 📅 일별 지출 추이")
        daily = valid_dates.groupby(valid_dates["날짜"].dt.date)[amount_col].sum().reset_index()
        daily.columns = ["날짜", "금액"]
        fig3 = px.line(daily, x="날짜", y="금액", markers=True,
                       text=daily["금액"].apply(lambda x: f"₩{x:,.0f}"))
        fig3.update_traces(textposition="top center")
        fig3.update_layout(yaxis_tickformat=",")
        st.plotly_chart(fig3, use_container_width=True)

# 카테고리별 합계
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

# --- 5. 아이폰 결제내역 ---
st.markdown("---")
st.subheader("📱 아이폰 결제내역")
st.caption("iMessage 결제 알림을 자동으로 읽어와 정리합니다. (준비 중)")

# 세션 상태 초기화
if "iphone_df" not in st.session_state:
    st.session_state.iphone_df = pd.DataFrame(columns=[
        "날짜", "결제수단", "항목", "이용금액", "대분류", "소분류",
        "할부/회차", "적립/할인율", "예상적립 / 할인", "결제원금", "결제 후 잔액"
    ])

iphone_df = st.session_state.iphone_df

# 테이블 (데이터 섹션과 동일한 형식)
iphone_config = {}
if "결제수단" in iphone_df.columns:
    iphone_config["결제수단"] = st.column_config.SelectboxColumn(
        "결제수단", options=PAYMENT_METHODS, required=False,
    )
if "대분류" in iphone_df.columns:
    iphone_config["대분류"] = st.column_config.SelectboxColumn(
        "대분류", options=[""] + ALL_MAJOR, required=False,
    )
if "소분류" in iphone_df.columns:
    iphone_config["소분류"] = st.column_config.SelectboxColumn(
        "소분류", options=[""] + ALL_MINOR, required=False,
    )
for col in ["이용금액", "결제원금", "결제 후 잔액", "예상적립 / 할인"]:
    if col in iphone_df.columns:
        iphone_config[col] = st.column_config.NumberColumn(col, format="₩%d")
if "날짜" in iphone_df.columns:
    iphone_config["날짜"] = st.column_config.DateColumn("날짜")

edited_iphone_df = st.data_editor(
    iphone_df,
    column_config=iphone_config,
    num_rows="dynamic",
    use_container_width=True,
    key="iphone_data_editor"
)
st.session_state.iphone_df = edited_iphone_df

# --- 6. 수입 ---
st.markdown("---")
st.subheader("💵 수입")

INCOME_CATEGORIES = ["급여", "이자소득", "상여", "투자수익", "처분소득", "부수익", "페이백", "기타 수입"]
MONTHS = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]

if "income_df" not in st.session_state:
    data = {"수입 카테고리": INCOME_CATEGORIES}
    for m in MONTHS:
        data[m] = [0] * len(INCOME_CATEGORIES)
    st.session_state.income_df = pd.DataFrame(data)

edited_income = st.data_editor(
    st.session_state.income_df,
    num_rows="dynamic",
    use_container_width=True,
    key="income_editor"
)
st.session_state.income_df = edited_income

# 수입 합계
total_income = edited_income[MONTHS].sum().sum()
monthly_totals = edited_income[MONTHS].sum(axis=0)
st.markdown(f"**총 수입: ₩{total_income:,.0f}**")
st.bar_chart(monthly_totals)
