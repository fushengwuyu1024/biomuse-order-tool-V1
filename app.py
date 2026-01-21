import streamlit as st
import pandas as pd
from io import BytesIO
import re
from openpyxl import load_workbook

# 页面配置
st.set_page_config(page_title="BioMuse 订单助手", layout="wide")

import streamlit as st
import pandas as pd
from io import BytesIO
import re
from openpyxl import load_workbook

# 1. 基础配置
st.set_page_config(page_title="BioMuse 订单助手", layout="wide")

# 2. 【核心隐藏代码】粘贴在 set_page_config 之后
st.markdown("""
    <style>
    /* 隐藏右上角三个点菜单 */
    #MainMenu {visibility: hidden;}
    /* 隐藏底部 "Made with Streamlit" 水印 */
    footer {visibility: hidden;}
    /* 隐藏顶部装饰条 */
    header {visibility: hidden;}
    /* 核心：隐藏右上角的 GitHub 部署按钮 */
    .stAppDeployButton {display:none;}
    /* 隐藏“View Source”按钮（针对不同版本的适配） */
    .st-emotion-cache-12fmjuu {display: none;} 
    </style>
    """, unsafe_allow_html=True)

# 3. 授权验证（防止外人乱用）
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 BioMuse 访问授权")
    # 为了保护你的隐私，只有输入口令的人才能进入系统
    pwd = st.text_input("请输入专属授权码", type="password")
    if st.button("进入系统", use_container_width=True):
        if pwd == "BioMuse2026": # 这里可以设置你自己的口令
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("授权码不正确，请联系管理员")
    st.stop()

# --- 后续业务逻辑代码（如 st.title("🧬 BioMuse 自动化订单助手") 等）保持不变 ---

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
if st.button("🚀 开始解析并生成订购表格", use_container_width=True): # 按钮宽度自适应手机
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
            st.error(f"填充出错: {e}")
    else:
        st.warning("未识别到有效序列，请检查输入内容格式。")
