import os
from io import BytesIO

import pandas as pd
import streamlit as st
from chardet import detect


def main():
    st.sidebar.title("效率")
    pages = {
        "Excel处理": excel_processing_page,
        "Word处理": None

    }

    page = st.sidebar.radio("功能", list(pages.keys()))
    func = pages[page]

    if func:
        func()
    else:
        st.title(page)
        st.info("该功能正在开发中...")

def is_gibberish(text):
    # 检测是否包含非ASCII字符
    return any(ord(char) > 127 for char in text)

def trim_quotes(path):
    if path.startswith('"') and path.endswith('"'):
        return path[1:-1]
    return path


def read_excel_filepath(file_path, n=0):
    file_path = trim_quotes(file_path)
    try:
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.csv':
            with open(file_path, 'rb') as f:
                raw = f.read(10000)
                result = detect(raw)
            detected_encoding = result['encoding']

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

def excel_processing_page():
    st.title("Excel处理")
    st.write("选择需要的Excel处理功能")

    excel_function = st.selectbox("选择功能", ["合并Excel文件", "合并单个Excel的sheet", "拆分Excel的多个sheet", "CSV转Excel"])

    if excel_function == "合并Excel文件":
        merge_folder_excel()
    elif excel_function == "拆分Excel的多个sheet":
        split_excel_sheets()
    elif excel_function == "合并单个Excel的sheet":
        merge_excel_sheets()
    elif excel_function == "CSV转Excel":
        csv_to_excel()

def merge_folder_excel():  
    st.subheader("合并Excel")
    st.write("还在✌手动复制粘贴合并计算的数据？")
    st.write("将需要合并的excel放至一个 **文件夹** 里，然后输入文件夹路径")
    folder_path = st.text_input("请输入文件夹路径：")
    folder_path = trim_quotes(folder_path)
    if folder_path:
        if st.button("合并文件"):
            dfs = []
            headers = set()
            
            for file in os.listdir(folder_path):
                if file.endswith(('.xlsx', '.xls', '.csv')):
                    filepath = os.path.join(folder_path, file)
                    df = read_excel_filepath(filepath)
                    if df is not None:
                        headers.add(tuple(df.columns))
                        dfs.append(df)
            
            if len(headers) > 1:
                st.warning("警告：上传的文件表头不一致，强行合并的话也不是不行🤭。")
                if st.button("我就要合并"):
                    merged_df = pd.concat(dfs, ignore_index=True)
                    save_and_download_file(merged_df)
            else:
                merged_df = pd.concat(dfs, ignore_index=True)
                save_and_download_file(merged_df)
    else:
        st.info("请选择文件夹路径")

def split_excel_sheets():
    st.subheader("拆分Excel的多个sheets")
    uploaded_file = st.text_input("请输入文件路径：")
    uploaded_file = trim_quotes(uploaded_file)

    if uploaded_file:
        excel = pd.ExcelFile(uploaded_file)
        sheet_names = excel.sheet_names
        
        dir_path = os.path.dirname(uploaded_file) # 获取文件所在目录
        
        if st.button("拆分工作表"):
            for sheet in sheet_names:
                df = pd.read_excel(uploaded_file, sheet_name=sheet)
                output_file = os.path.join(dir_path, f"{sheet}.xlsx")
                df.to_excel(output_file, index=False)
                st.write(f"Sheet '{sheet}' 已保存至 '{output_file}'")

            st.success("已拆分所有工作表")

def merge_excel_sheets():
    st.subheader("合并单个Excel的sheet")
    uploaded_file = st.text_input("请输入文件路径：")
    uploaded_file = trim_quotes(uploaded_file)
    
    if uploaded_file:
        excel = pd.ExcelFile(uploaded_file)
        sheet_names = excel.sheet_names
        
        if st.button("合并工作表"):
            dfs = []
            for sheet in sheet_names:
                df = pd.read_excel(uploaded_file, sheet_name=sheet)
                dfs.append(df)
            
            merged_df = pd.concat(dfs, ignore_index=True)
            save_and_download_file(merged_df)
            st.success("已合并所有工作表")

def csv_to_excel():
    st.subheader("CSV转Excel")
    folder_path = st.text_input("输入包含CSV文件的文件夹路径：")
    folder_path = trim_quotes(folder_path)

    if folder_path:
        csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        
        if not csv_files:
            st.warning("指定文件夹中没有找到CSV文件")
        else:
            st.write(f"找到 {len(csv_files)} 个CSV文件")
            
            if st.button("转换为Excel"):
                for csv_file in csv_files:
                    file_path = os.path.join(folder_path, csv_file)
                    df = read_excel_filepath(file_path)
                    excel_file = csv_file.rsplit('.', 1)[0] + '.xlsx'
                    excel_path = os.path.join(folder_path, excel_file)
                    df.to_excel(excel_path, index=False)
                
                st.success(f"已将 {len(csv_files)} 个CSV文件转换为Excel文件")
                st.info(f"转换后的Excel文件保存在: {folder_path}")
    else:
        st.info("请输入文件夹路径")

if __name__ == "__main__":
    main()
