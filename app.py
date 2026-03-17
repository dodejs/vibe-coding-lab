import streamlit as st

st.title("My First Vibe Coding App")

name = st.text_input("이름을 입력하세요")

if name:
    st.write(f"안녕하세요, {name}님!")
