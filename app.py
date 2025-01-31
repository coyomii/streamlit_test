import json
import os
import random
import shutil

import requests
import streamlit as st
from packaging.version import Version


st.set_page_config(page_title="数据分析工具", layout="wide")

# 应用程序标题与简介
def display_header():
    st.title("📊 数据分析与可视化应用")
    st.markdown("""
        欢迎使用！这个应用程序旨在帮助您更好地理解和展示数据，以及提高工作效率。
        使用左侧的导航栏探索不同的功能页面。
    """)
    st.markdown("---")

# 实时用户统计
def display_user_count():
    st.subheader("📈 实时数据统计")
    if 'user_count' not in st.session_state:
        st.session_state.user_count = random.randint(1, 7)
    placeholder = st.empty()
    with placeholder.container():
        st.metric("当前在线用户", st.session_state.user_count)
    st.session_state.user_count += random.randint(-2, 2) # 模拟人数变化
    st.session_state.user_count = max(1, st.session_state.user_count)


# 每日诗词
def fetch_daily_sentence():
    url = 'https://v1.jinrishici.com/all.json'
    # url = 'https://v1.hitokoto.cn/?c=i'
    try:
        response = requests.get(url)
        data = response.json()
        return f"「{data['content']}」 —— {data['author']}"
    except requests.exceptions.RequestException:
        # 如果请求失败，返回固定的诗词
        return "「月落乌啼霜满天，江枫渔火对愁眠」"

# 显示每日诗词
def display_daily_sentence():
    st.subheader("📖 每日诗词")
    sici = fetch_daily_sentence()
    st.info(sici)

def main():
    display_header()
    col1, col2 = st.columns(2)
    with col1:
        display_user_count()
    with col2:
        display_daily_sentence()
    st.markdown("---")
    st.markdown("👨‍💻 由您的数据团队倾情打造")


if __name__ == "__main__":
    main()
