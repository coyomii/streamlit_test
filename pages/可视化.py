from datetime import datetime, time
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib import font_manager

from utils.common_utils import *

# 临时注册新的全局字体
font_manager.fontManager.addfont(r'fonts\SimHei.ttf')
plt.rcParams['font.sans-serif']=['SimHei'] # 测试Linux正常显示中文标签
plt.rcParams['axes.unicode_minus']=False # 正常显示负号


def main():
    st.sidebar.title("可视化")
    pages = {
        "批量看流速分布": flow_display,

    }

    page = st.sidebar.radio("功能", list(pages.keys()))
    func = pages[page]

    if func:
        func()
    else:
        st.title(page)
        st.info("该功能正在开发中...")

def convert_to_datetime(df, column):
    try:
        df[column] = pd.to_datetime(df[column])
        return df, True
    except:
        return df, False

def flow_display():
    st.title("批量看流速分布")
    uploaded_file = st.file_uploader("上传文件", type=["csv", "xlsx", "xls"])

    if uploaded_file:
        df = read_excel_file(uploaded_file)
        
        if df is not None:
            time_columns = [col for col in df.columns if '时间' in col or '视频开始时间' in col]
            X_columns = [col for col in df.columns if '起点距' in col or '序号' in col]
            water_columns = [col for col in df.columns if '水位' in col]
            
            default_index = df.columns.get_loc(time_columns[0]) if time_columns else 0
            group_column = st.selectbox('选择分组列(一般为时间):', df.columns, index=default_index)

            df, conversion_success = convert_to_datetime(df, group_column)
            
            if not conversion_success:
                st.warning(f"无法自动将'{group_column}'列转换为日期时间格式。请指定日期时间格式。")
                date_format = st.text_input("请输入日期时间格式 (例如: %Y-%m-%d %H:%M:%S)", "%Y-%m-%d %H:%M:%S")
                try:
                    df[group_column] = pd.to_datetime(df[group_column], format=date_format)
                    conversion_success = True
                except:
                    st.error("无法使用提供的格式转换日期时间。请检查格式是否正确。")

            X_column = st.selectbox('选择X轴列:', df.columns, index=df.columns.get_loc(X_columns[0]) if X_columns else 0)
            selected_columns = st.multiselect('选择要绘制的列(Y轴列, 可多选):', df.columns)
            line_columns = st.multiselect('选择要绘制折线的列:', selected_columns)
            
            # 修改水位列选择逻辑
            water_column = st.selectbox('选择水位列 (可选):', [''] + list(df.columns), index=df.columns.get_loc(water_columns[0])+1 if water_columns else 0)
            use_water_column = water_column != ''
            
            df_filtered = df.copy()

            # 时间范围筛选
            use_time_filter = st.checkbox("启用时间范围筛选", value=False)
            if use_time_filter and pd.api.types.is_datetime64_any_dtype(df[group_column]):
                min_datetime, max_datetime = df[group_column].min(), df[group_column].max()
                
                # 添加时间筛选模式选择
                time_filter_mode = st.radio("选择时间筛选模式", ("按日期筛选", "按时间筛选(日期不起作用,可跨夜)"),horizontal=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("开始日期", min_datetime.date(), min_value=min_datetime.date(), max_value=max_datetime.date())
                    start_time = st.time_input("开始时间", time(hour=min_datetime.hour, minute=min_datetime.minute))
                with col2:
                    end_date = st.date_input("结束日期", max_datetime.date(), min_value=min_datetime.date(), max_value=max_datetime.date())
                    end_time = st.time_input("结束时间", time(hour=max_datetime.hour, minute=max_datetime.minute))
                
                # 组合日期和时间
                start_datetime = datetime.combine(start_date, start_time)
                end_datetime = datetime.combine(end_date, end_time)

                if time_filter_mode == "按日期筛选":
                    # 日期筛选，比较日期和时间
                    df_filtered = df_filtered[(df_filtered[group_column] >= start_datetime) & 
                                            (df_filtered[group_column] <= end_datetime)]
                else:
                    # 时间筛选，处理跨午夜的情况
                    mask = []
                    for dt in df_filtered[group_column]:
                        dt_time = dt.time()
                        if start_time <= end_time:
                            # 正常情况：开始时间小于结束时间
                            mask.append(start_time <= dt_time <= end_time)
                        else:
                            # 跨午夜情况
                            mask.append(start_time <= dt_time or dt_time <= end_time)
                    
                    df_filtered = df_filtered[mask]

            # 水位范围筛选
            use_water_filter = st.checkbox("启用水位范围筛选", value=False)
            if use_water_filter and use_water_column:
                min_water, max_water = st.columns(2)
                with min_water:
                    min_water_value = st.number_input("最小水位", value=float(df[water_column].min()), step=0.01)
                with max_water:
                    max_water_value = st.number_input("最大水位", value=float(df[water_column].max()), step=0.01)
                df_filtered = df_filtered[(df_filtered[water_column] >= min_water_value) & (df_filtered[water_column] <= max_water_value)]

            # 置信度流向夹角范围筛选
            use_confidence_angle_filter = st.checkbox("启用置信度流向夹角筛选", value=False)
            if use_confidence_angle_filter:
                confidence_columns = st.multiselect("选择置信度列（与Y轴列数量一致）:", df.columns)
                
                # 确保置信度列数量与Y轴列数量一致
                if len(confidence_columns) != len(selected_columns):
                    st.warning("请选择与Y轴列数量相对应的置信度列")
                else:
                    min_confidence, max_confidence = st.columns(2)
                    with min_confidence:
                        min_confidence_value = st.number_input("最小置信度", value=0.0, min_value=0.0, max_value=1.0, step=0.01)
                    with max_confidence:
                        max_confidence_value = st.number_input("最大置信度", value=1.0, min_value=0.0, max_value=1.0, step=0.01)
                    
                    for speed_col, conf_col in zip(selected_columns, confidence_columns): # zip函数用于同时遍历两个列表，一一对应，很妙
                        mask = (df_filtered[conf_col] < min_confidence_value) | (df_filtered[conf_col] > max_confidence_value)
                        df_filtered.loc[mask, speed_col] = np.nan # 将不满足条件的值赋值为None比较好

                angle_columns = [col for col in df.columns if '流向夹角' in col]
                angle_column = st.selectbox("选择流向夹角列:", [''] + list(df.columns), index=df.columns.get_loc(angle_columns[0])+1 if angle_columns else 0)
                
                if angle_column:
                    min_angle, max_angle = st.columns(2)
                    with min_angle:
                        min_angle_value = st.number_input("最小流向夹角", value=-180.00, step=0.1)
                    with max_angle:
                        max_angle_value = st.number_input("最大流向夹角", value=180.00, step=0.1)
                    df_filtered = df_filtered[(df_filtered[angle_column] >= min_angle_value) & (df_filtered[angle_column] <= max_angle_value)]

            st.subheader("筛选后的数据预览")
            st.dataframe(df_filtered)

            # 图表布局设置
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                charts_per_row = st.number_input("每行图表数量", min_value=1, max_value=6, value=3, step=1)
            with col2:
                fig_width = st.number_input("单个图表宽度", min_value=1, max_value=20, value=6, step=1)
            with col3:
                fig_height = st.number_input("单个图表高度", min_value=1, max_value=20, value=4, step=1)
            with col4:
                graph_mark = st.checkbox("是否显示图例", value=True)
            with col5:
                graph_grid = st.checkbox("是否显示网格", value=True)

            st.subheader("自定义坐标轴范围")
            col1, col2 = st.columns(2)
            with col1:
                use_custom_x = st.checkbox("自定义 X 轴范围", value=False)
                if use_custom_x:
                    x_min = st.number_input("X 轴最小值", value=float(df_filtered[X_column].min()), step=0.1)
                    x_max = st.number_input("X 轴最大值", value=float(df_filtered[X_column].max()), step=0.1)
            with col2:
                use_custom_y = st.checkbox("自定义 Y 轴范围", value=False)
                if use_custom_y:
                    y_min = st.number_input("Y 轴最小值", value=float(df_filtered[selected_columns].min().min()), step=0.1)
                    y_max = st.number_input("Y 轴最大值", value=float(df_filtered[selected_columns].max().max()), step=0.1)

            button_clicked = st.button('开始绘制')
            if button_clicked:
                if not selected_columns:
                    st.error("请先选择要绘制的列")
                else:
                    image_buffers = []
                    grouped = df_filtered.groupby(group_column)
                    cols = st.columns(charts_per_row)
                    
                    for i, (name, group) in enumerate(grouped):
                        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
                        
                        for column in selected_columns:
                            if column in line_columns:
                                ax.plot(group[X_column].values, group[column].values, label=column)
                            else:
                                ax.scatter(group[X_column].values, group[column].values, label=column)
                        
                        # 根据是否选择水位列来设置标题
                        if use_water_column:
                            ax.set_title(f"时间: {name} 水位: {(group[water_column].values[0]):.2f}m")
                        else:
                            ax.set_title(f"时间: {name}")
                        
                        ax.set_xlabel(X_column)
                        ax.set_ylabel("流速")
                        
                        if use_custom_x:
                            ax.set_xlim(x_min, x_max)
                        if use_custom_y:
                            ax.set_ylim(y_min, y_max)
                        
                        if graph_mark:
                            ax.legend()
                        if graph_grid:
                            ax.grid(True)
                        
                        cols[i % charts_per_row].pyplot(fig)
                        plt.close(fig)

                        img_buffer = BytesIO()
                        fig.savefig(img_buffer, format='png')
                        img_buffer.seek(0)
                        image_buffers.append(img_buffer)

                    save_and_download_images(image_buffers)


if __name__ == '__main__':
    main()