import os

import pandas as pd
import streamlit as st

from utils.common_utils import *


def main():
    st.sidebar.title("效率")
    pages = {
        "Excel处理": excel_processing_page,
        "XX处理": None,

    }

    page = st.sidebar.radio("功能", list(pages.keys()))
    func = pages[page]  # 获取对应的函数对象

    if func:
        func()
    else:
        st.title(page)
        st.info("该功能正在开发中...")

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


if __name__ == '__main__':
    main()