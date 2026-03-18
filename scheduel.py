import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="스케줄 앱", layout="wide")

st.title("오늘의 스케줄 앱")

# 날짜 선택
selected_date = st.date_input("날짜를 선택하세요", value=date.today())

st.subheader(f"{selected_date} 할 일 관리")

st.write("할 일을 입력하고, 완료 여부와 중요도를 선택하세요.")

# 기본 할 일 개수
task_count = st.number_input("할 일 개수", min_value=1, max_value=20, value=5, step=1)

tasks_data = []

for i in range(int(task_count)):
    st.markdown(f"### 할 일 {i+1}")

    col1, col2, col3, col4 = st.columns([4, 1, 1, 1.5])

    with col1:
        task_name = st.text_input(f"할 일 내용 {i+1}", key=f"task_name_{i}")

    with col2:
        completed = st.checkbox("완료", key=f"completed_{i}")

    with col3:
        priority = st.selectbox("중요도", ["상", "중", "하"], key=f"priority_{i}")

    with col4:
        status = "완료" if completed else "진행중"
        st.write("")
        st.write("")
        st.markdown(f"**{status}**")

    tasks_data.append({
        "날짜": selected_date,
        "할 일": task_name,
        "완료 여부": "완료" if completed else "미완료",
        "중요도": priority,
        "상태": status
    })

st.markdown("---")
st.subheader("할 일 요약")

df = pd.DataFrame(tasks_data)

# 빈 할 일은 표시 제외
filtered_df = df[df["할 일"].str.strip() != ""]

if not filtered_df.empty:
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
else:
    st.info("입력된 할 일이 아직 없습니다.")
