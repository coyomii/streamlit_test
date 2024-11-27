import json
import os
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import streamlit as st
from chardet import detect
from chardet.universaldetector import UniversalDetector


def trim_quotes(path): # 去除路径两端的引号
    if path.startswith('"') and path.endswith('"'):
        return path[1:-1]
    return path

def is_gibberish(text): # 检测是否包含非ASCII字符, 判断读取excel编码是否对
    return any(ord(char) > 127 for char in text)

@st.cache_data
def read_excel_file(file, **kwargs):
    try:
        file_extension = file.name.split('.')[-1]
        if file_extension == 'csv':
            detector = UniversalDetector()
            for line in file:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
            encoding = detector.result['encoding']
            file.seek(0)
            df = pd.read_csv(file, encoding=encoding, **kwargs)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(file, **kwargs)
        else:
            st.warning(f"不支持的文件格式: {file.name}")
            return None
        return df
    except UnicodeDecodeError as e:
        st.error(f"解码错误: {e}. 尝试使用其他编码方式，大概率加密问题。")
    except Exception as e:
        st.error(f"发生未知错误: {e}")

@st.cache_data
def read_excel_filepath(file_path, n=0):
    file_path = trim_quotes(file_path)
    try:
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.csv':
            with open(file_path, 'rb') as f:
                raw = f.read(10000)
                result = detect(raw)
            detected_encoding = result['encoding']
            # with open(file_path, 'rb') as f:  # 读取大型文件时候速度过慢且会出错，弃用
            #     detector = UniversalDetector()
            #     for line in f.readlines():
            #         detector.feed(line)
            #         if detector.done:            
            #             break
            #     detector.close()

            # detected_encoding = detector.result['encoding']

            # 尝试使用检测到的编码读取文件
            try:
                df = pd.read_csv(file_path, encoding = detected_encoding)
                if not any(is_gibberish(col) for col in df.columns):
                    return df
            except UnicodeDecodeError:
                pass
            
            # 如果检测到乱码，尝试使用其他常见编码
            for encoding in ['ANSI', 'UTF-8', 'GBK', 'ISO-8859-1']:
                try:
                    df = pd.read_csv(file_path, encoding = encoding)
                    return df
                except UnicodeDecodeError:
                    continue
            
            st.error("无法使用常见编码读取文件，可能需要手动指定正确的编码或者另存为xlsx")
            
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, sheet_name = n)
            return df
    except UnicodeDecodeError as e:
        st.error(f"解码错误: {e}. 尝试使用其他编码方式, 大概率加密问题。")
    except Exception as e:
        st.error(f"发生未知错误: {e}")
    return None

def load_data(file_path, n = 0):
    if st.button('重新加载Excel数据'):
        st.cache_data.clear() # 清除缓存
        df = read_excel_filepath(file_path, n) # 重新加载数据

        st.success('数据已重新加载')
    else:
        df = read_excel_filepath(file_path, n) # 正常加载数据
    return df

# @st.cache_data
def read_json(uploaded_file):
    try:
        file_content = uploaded_file.read()
        encoding = detect(file_content)['encoding']
        
        # 如果检测失败，默认使用 utf-8
        if not encoding:
            encoding = 'utf-8'

        content = file_content.decode(encoding)
        data = json.loads(content)
        
        return data
    except json.JSONDecodeError as e:
        st.error(f"JSON 解析错误: {e}")
    except UnicodeDecodeError as e:
        st.error(f"解码错误: {e}. 尝试使用其他编码方式。")
    except Exception as e:
        st.error(f"发生未知错误: {e}")
    
        return None

# @st.cache_data
def read_json_path(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
            encoding = detect(file_content)['encoding']
            
            # 如果检测失败，默认使用 utf-8
            if not encoding:
                encoding = 'utf-8'

            content = file_content.decode(encoding)
            data = json.loads(content)
            return data
    except:
        st.error(f"配置文件读取失败")
        return None

@st.experimental_fragment()
def save_and_download_file(df, file_name="output_file.xlsx"):
    output = BytesIO()
    
    # 只提供 Excel (.xlsx) 格式
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0) # 重新定位到文件开头，否则可能导致下载的文件大小为 0
    # 提供下载链接
    st.download_button(
        label="下载处理后的Excel(.xslx)文件",
        data=output.getvalue(),
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.success("点击按钮下载！")

@st.experimental_fragment()
def save_and_download_csv(df, file_name="output_file.csv"):
    csv = df.to_csv(index=False)
    st.download_button(
        label="下载处理后的CSV文件",
        data=csv,
        file_name=file_name,
        mime="text/csv",
    )
    st.success("点击按钮下载！")

@st.experimental_fragment()  
def save_and_download_images(image_buffers):
    if not image_buffers:
        st.warning("没有可下载的图片")
        return

    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "a", ZIP_DEFLATED, False) as zip_file:
        for i, img_buffer in enumerate(image_buffers):
            zip_file.writestr(f"figure_{i}.png", img_buffer.getvalue())
    
    st.download_button(
        label="下载所有图片",
        data=zip_buffer.getvalue(),
        file_name="figures.zip",
        mime="application/zip"
    )



