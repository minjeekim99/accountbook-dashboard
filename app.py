import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from collections import OrderedDict

st.set_page_config(page_title="가계부 대시보드", page_icon="💰", layout="wide")

# ===================== 카테고리 & 결제수단 설정 =====================

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

ALL_MAJOR = list(CATEGORY_TREE.keys())
ALL_MINOR = list(dict.fromkeys(sub for subs in CATEGORY_TREE.values() for sub in subs))

PAYMENT_METHODS = [
    "", "계좌이체", "현금", "롯데카드신용", "온누리상품권체크", "신한카드-더모아",
    "신한은행", "우리체크카드", "우리카드", "PAYCO", "현대카드", "현아플",
    "새마을금고", "네이버페이", "카카오뱅크", "모빌리언스카드", "삼성카드",
    "롯데체크카드", "신한카드", "KB국민카드", "우리카드연세", "우리은행",
    "케이뱅크", "지역화페", "카카오페이", "롯데카드", "온누리상품권",
]

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
    "넷플릭스": ("문화생활비", "영화/공연/OTT/전시"), "영화": ("문화생활비", "영화/공연/OTT/전시"),
    "유튜브": ("문화생활비", "영화/공연/OTT/전시"), "구독": ("생활유지비", "고정비/구독료"),
    "게임": ("문화생활비", "게임/음악"), "도서": ("문화생활비", "도서"), "책": ("문화생활비", "도서"),
    "옷": ("의류미용비", "의류/잡화"), "의류": ("의류미용비", "의류/잡화"),
    "쇼핑": ("의류미용비", "의류/잡화"), "쿠팡": ("의류미용비", "의류/잡화"),
    "무신사": ("의류미용비", "의류/잡화"), "올리브영": ("의류미용비", "미용"),
    "화장품": ("의류미용비", "미용"),
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
}

INCOME_CATEGORIES = ["급여", "이자소득", "상여", "투자수익", "처분소득", "부수익", "페이백", "기타 수입"]
MONTHS = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
DATA_COLUMNS = ["날짜", "결제수단", "대분류", "소분류", "지출 내용", "결제금액", "할인", "실지출", "비고"]

# ===================== 유틸 함수 =====================

COLUMN_RENAME = {i: c for i, c in enumerate(DATA_COLUMNS)}


def categorize_item(text: str) -> tuple[str, str]:
    if not isinstance(text, str):
        return ("", "")
    text_lower = text.lower()
    for kw, (major, minor) in AUTO_CLASSIFY.items():
        if kw in text_lower:
            return (major, minor)
    return ("", "")


# 엑셀 헤더 → 표준 칼럼명 매핑
HEADER_ALIASES = {
    # 날짜
    "날짜": "날짜", "일자": "날짜", "거래일": "날짜", "거래일자": "날짜", "이용일": "날짜",
    "이용일자": "날짜", "이용일": "날짜", "지출일": "날짜", "date": "날짜",
    # 결제수단
    "결제수단": "결제수단", "카드": "결제수단", "카드명": "결제수단", "결제카드": "결제수단",
    "결제": "결제수단", "이용카드": "결제수단",
    # 지출 내용
    "항목": "지출 내용", "내역": "지출 내용", "적요": "지출 내용", "사용처": "지출 내용",
    "가맹점": "지출 내용", "가맹점명": "지출 내용", "내용": "지출 내용",
    "지출내역": "지출 내용", "이용가맹점": "지출 내용", "지출 내용": "지출 내용",
    # 결제금액
    "이용금액": "결제금액", "금액": "결제금액", "지출금액": "결제금액", "결제금액": "결제금액",
    "이용 금액": "결제금액", "amount": "결제금액",
    # 대분류/소분류
    "대분류": "대분류", "카테고리": "대분류",
    "소분류": "소분류", "세부카테고리": "소분류",
    # 할인/실지출/비고
    # 할인 — 엑셀에서 가져오지 않음 (수동 입력만)
    "실지출": "실지출", "결제원금": "실지출", "원금": "실지출",
    "비고": "비고", "메모": "비고",
}


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, ~df.columns.astype(str).str.match(r"^\s*$")]

    # 1) 헤더 행 찾기 — 처음 10행 내에서 2개 이상 HEADER_ALIASES에 매칭되는 행
    header_row_idx = None
    for i in range(min(10, len(df))):
        row_vals = [str(v).strip() for v in df.iloc[i] if pd.notna(v)]
        matches = sum(1 for v in row_vals if v in HEADER_ALIASES)
        if matches >= 2:
            header_row_idx = i
            break

    if header_row_idx is not None:
        # 헤더 행 사용
        header_row = [str(v).strip() for v in df.iloc[header_row_idx]]
        df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
        # 헤더명 → 표준 칼럼명 매핑
        new_cols = []
        used = set()
        for h in header_row:
            standard = HEADER_ALIASES.get(h)
            if standard and standard not in used:
                new_cols.append(standard)
                used.add(standard)
            else:
                new_cols.append(f"_orig_{h}")
        df.columns = new_cols
    else:
        # 위치 기반 매핑 (fallback)
        new_cols = [COLUMN_RENAME.get(i, f"_drop_{i}") for i in range(len(df.columns))]
        df.columns = new_cols

    df = df.loc[:, ~df.columns.str.startswith("_drop_")]
    df = df.loc[:, ~df.columns.str.startswith("_orig_")]

    if "결제금액" in df.columns:
        def is_not_number(v):
            if pd.isna(v):
                return True
            try:
                float(str(v).replace(",", "").replace("원", "").strip())
                return False
            except (ValueError, TypeError):
                return True
        df = df[~df["결제금액"].apply(is_not_number)].reset_index(drop=True)

    df = df.dropna(how="all").reset_index(drop=True)

    if "날짜" in df.columns:
        def parse_date(v):
            if pd.isna(v):
                return pd.NaT
            if isinstance(v, pd.Timestamp):
                return v
            s = str(v).strip()
            if not s:
                return pd.NaT
            # 괄호 안의 요일 제거: "2026.01.01 (목)" → "2026.01.01"
            import re
            s = re.sub(r"\s*\(.*?\)\s*$", "", s).strip()
            try:
                num = float(s)
                if 1 < num < 100000:
                    return pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(num))
            except (ValueError, TypeError):
                pass
            for fmt in ["%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%m/%d/%Y",
                        "%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M",
                        "%Y년 %m월 %d일", "%Y년%m월%d일"]:
                try:
                    return pd.to_datetime(s, format=fmt)
                except (ValueError, TypeError):
                    continue
            return pd.to_datetime(s, errors="coerce")
        df["날짜"] = df["날짜"].apply(parse_date)

    money_cols = ["결제금액", "할인", "실지출"]
    for col in money_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "").str.replace("원", "").str.strip(),
                errors="coerce"
            )

    item_col = "지출 내용" if "지출 내용" in df.columns else None
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

    for c in ["대분류", "소분류"]:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str).str.strip()

    # 모든 칼럼이 항상 존재하도록 보장
    for col in DATA_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # 음수 결제금액 처리: -금액 → 결제금액=abs, 할인=abs, 실지출=0
    if "결제금액" in df.columns:
        df["결제금액"] = pd.to_numeric(df["결제금액"], errors="coerce").fillna(0)
        neg_mask = df["결제금액"] < 0
        df.loc[neg_mask, "할인"] = df.loc[neg_mask, "결제금액"].abs()
        df.loc[neg_mask, "결제금액"] = df.loc[neg_mask, "결제금액"].abs()

    # 실지출 = 결제금액 - 할인
    if "결제금액" in df.columns and "할인" in df.columns:
        df["할인"] = pd.to_numeric(df["할인"], errors="coerce").fillna(0)
        df["실지출"] = df["결제금액"] - df["할인"]

    # 칼럼 순서 정렬
    df = df[[c for c in DATA_COLUMNS if c in df.columns]]

    return df


def make_column_config(df):
    """데이터 테이블용 column_config 생성"""
    cc = {}
    if "결제수단" in df.columns:
        existing_pay = [str(v).strip() for v in df["결제수단"].dropna().unique() if str(v).strip()]
        cc["결제수단"] = st.column_config.SelectboxColumn(
            "결제수단", options=list(dict.fromkeys(PAYMENT_METHODS + existing_pay)), required=False)
    if "대분류" in df.columns:
        cc["대분류"] = st.column_config.SelectboxColumn(
            "대분류", options=[""] + ALL_MAJOR, required=False)
    if "소분류" in df.columns:
        existing_minor = [str(v).strip() for v in df["소분류"].dropna().unique() if str(v).strip()]
        cc["소분류"] = st.column_config.SelectboxColumn(
            "소분류", options=list(dict.fromkeys([""] + ALL_MINOR + existing_minor)), required=False)
    for col in ["결제금액", "할인", "실지출"]:
        if col in df.columns:
            cc[col] = st.column_config.NumberColumn(col, format="₩%d")
    if "날짜" in df.columns:
        cc["날짜"] = st.column_config.DateColumn("날짜")
    return cc


def render_data_table(df, key_prefix):
    """데이터 편집 테이블 렌더"""
    cc = make_column_config(df)
    edited = st.data_editor(
        df, column_config=cc, num_rows="dynamic",
        use_container_width=True, key=f"{key_prefix}_editor"
    )
    # 실지출 자동 계산: 결제금액 - 할인
    if "결제금액" in edited.columns and "할인" in edited.columns:
        edited["결제금액"] = pd.to_numeric(edited["결제금액"], errors="coerce").fillna(0)
        edited["할인"] = pd.to_numeric(edited["할인"], errors="coerce").fillna(0)
        edited["실지출"] = edited["결제금액"] - edited["할인"]

    # 대분류-소분류 자동 교정
    if "대분류" in edited.columns and "소분류" in edited.columns:
        for idx in edited.index:
            major = str(edited.at[idx, "대분류"]).strip()
            minor = str(edited.at[idx, "소분류"]).strip()
            if major in CATEGORY_TREE and minor and minor not in CATEGORY_TREE[major]:
                edited.at[idx, "소분류"] = CATEGORY_TREE[major][0]
    return edited


def render_category_editor(df, key_prefix):
    """카테고리 종속 드롭다운 편집"""
    if "대분류" not in df.columns or "소분류" not in df.columns or len(df) == 0:
        return df

    with st.expander("🏷️ 카테고리 편집 (종속 드롭다운)"):
        row_options = list(df.index)
        def fmt_row(i):
            item = df.at[i, "지출 내용"] if "지출 내용" in df.columns else ""
            return f"[{i}] {item} — {df.at[i, '대분류']}/{df.at[i, '소분류']}"

        selected = st.selectbox("행 선택", row_options, format_func=fmt_row, key=f"{key_prefix}_row")
        picked_major = st.selectbox("대분류", ALL_MAJOR, key=f"{key_prefix}_major")
        sub_options = CATEGORY_TREE.get(picked_major, [""])
        picked_minor = st.selectbox("소분류", sub_options, key=f"{key_prefix}_minor")

        if st.button("✅ 적용", key=f"{key_prefix}_apply"):
            df.at[selected, "대분류"] = picked_major
            df.at[selected, "소분류"] = picked_minor
            st.toast(f"✅ 행 {selected} → {picked_major} / {picked_minor}")
            st.rerun()
    return df


def empty_data_df():
    return pd.DataFrame(columns=DATA_COLUMNS)


# ===================== 세션 상태 초기화 =====================

# 월별 데이터 (지출)
for m in range(1, 13):
    key = f"month_{m}"
    if key not in st.session_state:
        st.session_state[key] = empty_data_df()

# 월별 아이폰 결제내역
for m in range(1, 13):
    key = f"iphone_{m}"
    if key not in st.session_state:
        st.session_state[key] = empty_data_df()

# 수입
if "income_df" not in st.session_state:
    data = {"수입 카테고리": INCOME_CATEGORIES}
    for m_name in MONTHS:
        data[m_name] = [0] * len(INCOME_CATEGORIES)
    st.session_state.income_df = pd.DataFrame(data)


# ===================== 사이드바: 엑셀 업로드 =====================

st.sidebar.header("📂 엑셀 업로드")
upload_month = st.sidebar.selectbox("업로드할 월", range(1, 13), format_func=lambda m: f"{m}월")
uploaded_files = st.sidebar.file_uploader(
    "엑셀 파일 (.xlsx, .xls) — 여러 개 가능",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if uploaded_files:
    try:
        all_dfs = []
        for f in uploaded_files:
            raw_df = pd.read_excel(f, header=None)
            processed = process_dataframe(raw_df)
            all_dfs.append(processed)
        
        if len(all_dfs) == 1:
            combined = all_dfs[0]
        else:
            combined = pd.concat(all_dfs, ignore_index=True)
        
        # 날짜순 정렬
        if "날짜" in combined.columns:
            combined["날짜"] = pd.to_datetime(combined["날짜"], errors="coerce")
            combined = combined.sort_values("날짜", na_position="last").reset_index(drop=True)
        
        st.session_state[f"month_{upload_month}"] = combined
        st.sidebar.success(f"✅ {upload_month}월에 {len(combined)}건 로드 완료 ({len(uploaded_files)}개 파일 합침)")
    except Exception as e:
        st.sidebar.error(f"파일 읽기 실패: {e}")


# ===================== 탭 구성 =====================

st.title("💰 가계부 대시보드")

tab_names = ["🏠 홈"] + [f"{m}월" for m in range(1, 13)] + ["💵 수입"]
tabs = st.tabs(tab_names)

# ===================== 홈 탭 (Summary Dashboard) =====================

with tabs[0]:
    st.subheader("📊 연간 요약 대시보드")

    # 전체 월 데이터 합치기
    all_data = []
    for m in range(1, 13):
        mdf = st.session_state[f"month_{m}"]
        if len(mdf) > 0:
            mdf_copy = mdf.copy()
            mdf_copy["월"] = f"{m}월"
            all_data.append(mdf_copy)

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        amount_col = "결제금액" if "결제금액" in combined.columns else None

        if amount_col and len(combined) > 0:
            # 메트릭 카드
            col1, col2, col3 = st.columns(3)
            total = combined[amount_col].sum()
            count = len(combined)
            avg = combined[amount_col].mean()
            col1.metric("💵 총 지출", f"₩{total:,.0f}")
            col2.metric("📝 건수", f"{count}건")
            col3.metric("📈 평균", f"₩{avg:,.0f}")

            # 월별 지출 바차트
            st.markdown("#### 📅 월별 지출")
            monthly = combined.groupby("월")[amount_col].sum().reindex(MONTHS).fillna(0)
            fig_m = px.bar(x=monthly.index, y=monthly.values, labels={"x": "월", "y": "금액"},
                          text=monthly.values)
            fig_m.update_traces(texttemplate="₩%{text:,.0f}", textposition="outside")
            st.plotly_chart(fig_m, use_container_width=True)

            # 대분류별 파이차트
            chart_col1, chart_col2 = st.columns(2)
            if "대분류" in combined.columns:
                with chart_col1:
                    st.markdown("#### 대분류별 지출")
                    major_sum = combined.groupby("대분류")[amount_col].sum().reset_index()
                    major_sum = major_sum[major_sum[amount_col] > 0]
                    if len(major_sum) > 0:
                        fig1 = px.pie(major_sum, values=amount_col, names="대분류", hole=0.4,
                                      color_discrete_sequence=px.colors.qualitative.Set2)
                        fig1.update_traces(textinfo="label+percent+value",
                                          texttemplate="%{label}<br>%{percent}<br>₩%{value:,.0f}")
                        st.plotly_chart(fig1, use_container_width=True)

            if "소분류" in combined.columns:
                with chart_col2:
                    st.markdown("#### 소분류별 지출")
                    minor_sum = combined.groupby("소분류")[amount_col].sum().reset_index()
                    minor_sum = minor_sum[minor_sum[amount_col] > 0].sort_values(amount_col, ascending=True)
                    if len(minor_sum) > 0:
                        fig2 = px.bar(minor_sum, x=amount_col, y="소분류", orientation="h",
                                      color=amount_col, color_continuous_scale="Blues",
                                      text=minor_sum[amount_col].apply(lambda x: f"₩{x:,.0f}"))
                        fig2.update_layout(showlegend=False, coloraxis_showscale=False)
                        st.plotly_chart(fig2, use_container_width=True)

            # 카테고리별 합계
            if "대분류" in combined.columns and "소분류" in combined.columns:
                st.markdown("#### 📑 카테고리별 합계")
                summary = combined.groupby(["대분류", "소분류"])[amount_col].agg(["sum", "count"]).reset_index()
                summary.columns = ["대분류", "소분류", "합계", "건수"]
                summary = summary.sort_values("합계", ascending=False)
                summary["합계"] = summary["합계"].apply(lambda x: f"₩{x:,.0f}")
                st.dataframe(summary, use_container_width=True, hide_index=True)

            # 수입 요약
            income = st.session_state.income_df
            total_income = income[MONTHS].sum().sum()
            if total_income > 0:
                st.markdown("---")
                st.markdown(f"#### 💵 총 수입: ₩{total_income:,.0f}")
                st.markdown(f"#### 💰 수지 (수입-지출): ₩{total_income - total:,.0f}")
    else:
        st.info("데이터를 업로드하면 연간 요약이 표시됩니다.")


# ===================== 월별 탭 (1~12월) =====================

for m in range(1, 13):
    with tabs[m]:
        st.subheader(f"📋 {m}월 데이터")

        # 지출 데이터 테이블
        month_key = f"month_{m}"
        df = st.session_state[month_key]
        edited = render_data_table(df, key_prefix=f"m{m}")
        st.session_state[month_key] = edited
        edited = render_category_editor(edited, key_prefix=f"m{m}_cat")
        st.session_state[month_key] = edited

        # 월 요약
        if len(edited) > 0 and "결제금액" in edited.columns:
            total = edited["결제금액"].sum()
            st.metric(f"{m}월 총 지출", f"₩{total:,.0f}")

        # 다운로드
        if len(edited) > 0:
            buf = BytesIO()
            edited.to_excel(buf, index=False, engine="openpyxl")
            st.download_button(
                f"📥 {m}월 데이터 다운로드", buf.getvalue(),
                file_name=f"가계부_{m}월.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{m}"
            )

        # 아이폰 결제내역
        st.markdown("---")
        st.subheader(f"📱 {m}월 아이폰 결제내역")
        st.caption("iMessage 결제 알림 자동 정리 (준비 중)")

        iphone_key = f"iphone_{m}"
        iphone_df = st.session_state[iphone_key]
        edited_iphone = render_data_table(iphone_df, key_prefix=f"ip{m}")
        st.session_state[iphone_key] = edited_iphone


# ===================== 수입 탭 =====================

with tabs[13]:
    st.subheader("💵 수입")

    edited_income = st.data_editor(
        st.session_state.income_df,
        num_rows="dynamic",
        use_container_width=True,
        key="income_editor"
    )
    st.session_state.income_df = edited_income

    total_income = edited_income[MONTHS].sum().sum()
    monthly_totals = edited_income[MONTHS].sum(axis=0)
    st.markdown(f"**총 수입: ₩{total_income:,.0f}**")
    st.bar_chart(monthly_totals)
