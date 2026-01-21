import streamlit as st
import pandas as pd
from io import BytesIO
import re
from openpyxl import load_workbook

# 页面配置
st.set_page_config(page_title="BioMuse 订单助手", layout="wide")

# --- 隐藏 GitHub 图标和多余菜单 (隐身模式) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# --- 核心算法 ---
def get_rna_antisense(sense_seq):
    sense_seq = sense_seq.upper().replace(' ', '').replace('T', 'U')
    pairs = {'A': 'U', 'U': 'A', 'G': 'C', 'C': 'G'}
    complement = "".join([pairs.get(base, 'N') for base in sense_seq])
    antisense = complement[::-1]
    return sense_seq + "dTdT", antisense + "dTdT"

# --- 主界面开始 ---
st.title("🧬 BioMuse 订单一键转换")

# 1. 客户基础信息 (不再放在侧边栏，改为直接显示)
st.subheader("1. 基础信息")
col1, col2 = st.columns(2)
with col1:
    c_name = st.text_input("客户姓名", placeholder="例如：张三")
with col2:
    c_unit = st.text_input("客户单位", placeholder="例如：华东理工")
c_group = st.text_input("课题组", placeholder="例如：李老师")

order_type = st.radio("订单类型", ["DNA引物", "siRNA/RNA"], horizontal=True)

# 2. 需求粘贴区
st.subheader("2. 粘贴需求文字")
raw_input = st.text_area("直接粘贴需求文字(可包含名称、序列、OD等)", height=150)

# 3. 执行按钮
if st.button("🚀 开始解析并生成表格", use_container_width=True): # 按钮宽度自适应手机
    data_list = []
    
    if order_type == "DNA引物":
        matches = re.findall(r'([FR\d\w-]+)[:\s]+([ATCGatcg]+)', raw_input)
        for name, seq in matches:
            data_list.append({"名称": name, "序列": seq.upper(), "纯化": "PAGE", "OD": 2})
    else:
        matches = re.findall(r'(?:Sense|正义链)?[:\s]*([AUCGaucgu]+)', raw_input)
        for seq in matches:
            if len(seq) > 10:
                s_final, a_final = get_rna_antisense(seq)
                data_list.append({"名称": "siRNA-S", "正义": s_final, "反义": a_final, "纯化": "HPLC", "OD": 2})

    if data_list:
        st.success("解析成功！")
        st.table(pd.DataFrame(data_list))
        
        # 填充逻辑 (保持不变)
        template_file = "template_dna.xlsx" if order_type == "DNA引物" else "template_rna.xlsx"
        try:
            wb = load_workbook(template_file)
            ws = wb.active
            ws['B5'], ws['B6'], ws['B7'] = c_name, c_unit, c_group
            
            start_row = 20
            for i, item in enumerate(data_list):
                curr_row = start_row + i
                if order_type == "DNA引物":
                    ws.cell(row=curr_row, column=2, value=item["名称"])
                    ws.cell(row=curr_row, column=3, value=item["序列"])
                    ws.cell(row=curr_row, column=4, value=item["纯化"])
                    ws.cell(row=curr_row, column=8, value=item["OD"])
                else:
                    ws.cell(row=curr_row, column=1, value=item["名称"])
                    ws.cell(row=curr_row, column=2, value=item["正义"])
                    ws.cell(row=curr_row, column=3, value=item["反义"])
                    ws.cell(row=curr_row, column=4, value=item["纯化"])

            output = BytesIO()
            wb.save(output)
            st.download_button(
                label="💾 下载百力格订单 Excel",
                data=output.getvalue(),
                file_name=f"百力格订购表_{c_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"填充失败}")
    else:
        st.warning("未识别到有效序列，请检查输入内容格式。")
