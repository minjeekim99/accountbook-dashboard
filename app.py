import streamlit as st
import pandas as pd

st.title("📊 나의 가계부 대시보드")

uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    st.subheader("📋 업로드된 데이터")
    st.dataframe(df)

    st.subheader("💰 총 지출 합계")
    if "금액" in df.columns:
        st.write(df["금액"].sum())
    else:
        st.warning("금액 컬럼이 없습니다.")
