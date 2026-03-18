import streamlit as st

st.title("My First Vibe Coding App")

name = st.text_input("이름을 입력하세요")

if name:
    st.write(f"안녕하세요, {name}님!")
if st.button("인사하기"):
    st.write(f"{name}님, 좋은 하루 되세요! 😊")
