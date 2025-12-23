import streamlit as st
import pandas as pd
import datetime
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

# --- 1. CẤU HÌNH KẾT NỐI GOOGLE SHEETS ---
@st.cache_resource
def get_gsheet_connection():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Lỗi cấu hình Secret: {e}")
        return None

SHEET_NAME = "DB_MinhDuc" 

def load_data(tab_name):
    try:
        client = get_gsheet_connection()
        if not client: return pd.DataFrame()
        sheet = client.open(SHEET_NAME).worksheet(tab_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        # st.warning(f"Đang tải dữ liệu '{tab_name}'...")
        return pd.DataFrame()

def add_row_to_sheet(tab_name, row_data_list):
    try:
        client = get_gsheet_connection()
        sheet = client.open(SHEET_NAME).worksheet(tab_name)
        sheet.append_row(row_data_list)
        return True
    except Exception as e:
        st.error(f"Lỗi lưu dữ liệu: {e}")
        return False

# --- 2. CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="Hệ Thống Thi Đua THPT Minh Đức",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 800; color: #1a73e8; text-align: center; margin-bottom: 10px; }
    .role-badge { padding: 5px 10px; border-radius: 15px; font-weight: bold; color: white; }
    /* Tô màu điểm số */
    .score-pos { color: #0f9d58; font-weight: bold; }
    .score-neg { color: #ea4335; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. HÀM LOGIN ---
def login(username, password):
    df_users = load_data("GiaoVien")
    if df_users.empty: return None
    user = df_users[
        (df_users['username'].astype(str) == str(username)) & 
        (df_users['password'].astype(str) == str(password))
    ]
    if not user.empty: return user.iloc[0].to_dict()
    return None

# --- 4. GIAO DIỆN ĐĂNG NHẬP ---
if 'user' not in st.session_state:
    st.markdown("<div class='main-header'>TRƯỜNG THPT MINH ĐỨC</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        with st.form("login_form"):
            st.subheader("Đăng Nhập")
            username = st.text_input("Tài khoản")
            password = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Đăng nhập", use_container_width=True):
                user_info = login(username, password)
                if user_info:
                    st.session_state.user = user_info
                    st.success(f"Xin chào {user_info['fullname']}")
                    time.sleep(0.5); st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu")

# --- 5. GIAO DIỆN CHÍNH ---
else:
    user = st.session_state.user
    role = user['role']
    
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
        st.title(user['fullname'])
        color = "#ea4335" if role == "ADMIN" else "#34a853" if role == "GVQN" else "#fbbc05"
        st.markdown(f'<span class="role-badge" style="background-color:{color}">{role}</span>', unsafe_allow_html=True)
        if user['lop_chu_nhiem']: st.info(f"Chủ nhiệm: {user['lop_chu_nhiem']}")
        st.divider()
        if st.button("Đăng xuất"):
            del st.session_state.user; st.rerun()

    st.markdown(f"<div class='main-header'>CỔNG QUẢN LÝ - {role}</div>", unsafe_allow_html=True)

    # ==================== 1. GVQN ====================
    if role == 'GVQN':
        tab1, tab2, tab3 = st.tabs(["📢 GHI NHẬN THI ĐUA", "📤 NỘP KẾ HOẠCH", "📊 LỊCH SỬ LỚP"])
        
        with tab1: # Báo thi đua (Cộng/Trừ)
            st.subheader(f"Ghi nhận cho lớp {user['lop_chu_nhiem']}")
            df_hs = load_data("HocSinh")
            my_students = df_hs[df_hs['lop'] == user['lop_chu_nhiem']]
            
            with st.form("gvqn_report"):
                col_a, col_b = st.columns(2)
                with col_a:
                    std_list = my_students['ho_ten'].tolist() if not my_students.empty else []
                    selected_std = st.selectbox("Chọn Học Sinh", std_list)
                with col_b:
                    df_tieuchi = load_data("TieuChiHS")
                    list_tc = df_tieuchi['noi_dung'].tolist() if not df_tieuchi.empty else []
                    selected_tc = st.selectbox("Tiêu chí (Cộng/Trừ)", list_tc)
                
                note = st.text_input("Ghi chú")
                
                # Hiển thị trước điểm số sẽ ghi
                score_preview = 0
                if not df_tieuchi.empty and selected_tc:
                    r = df_tieuchi[df_tieuchi['noi_dung'] == selected_tc]
                    if not r.empty: score_preview = int(r.iloc[0]['diem_tru'])
                
                if score_preview > 0:
                    st.markdown(f"Điểm dự kiến: :green[**+{score_preview}**] (Điểm Cộng)")
                else:
                    st.markdown(f"Điểm dự kiến: :red[**{score_preview}**] (Điểm Trừ)")

                if st.form_submit_button("Gửi Ghi Nhận"):
                    he_dt = ""
                    if not my_students.empty and selected_std:
                         he_dt = my_students[my_students['ho_ten'] == selected_std].iloc[0]['he_dao_tao']
                    
                    row = [str(datetime.date.today()), user['username'], user['lop_chu_nhiem'], selected_std, selected_tc, score_preview, he_dt, note]
                    if add_row_to_sheet("ViPhamHS", row):
                        st.success(f"Đã ghi nhận: {selected_tc} ({score_preview}đ)")

        with tab2: # Nộp kế hoạch (Giữ nguyên)
            st.subheader("Nộp Kế Hoạch Tuần")
            with st.form("upload_plan"):
                week = st.selectbox("Tuần học", [f"Tuần {i}" for i in range(1, 36)])
                link_file = st.text_input("Link File (Drive/OneDrive)")
                note_plan = st.text_input("Ghi chú")
                if st.form_submit_button("Nộp"):
                    if link_file:
                        row_plan = [week, user['fullname'], user['lop_chu_nhiem'], str(datetime.datetime.now()), "Đã nộp", link_file, note_plan]
                        add_row_to_sheet("KeHoach", row_plan)
                        st.success("Đã nộp thành công!")
                    else: st.warning("Thiếu link file!")

        with tab3: # Lịch sử (Cập nhật logic hiển thị màu)
            st.subheader(f"Lịch sử thi đua lớp {user['lop_chu_nhiem']}")
            df_vp = load_data("ViPhamHS")
            if not df_vp.empty:
                my_data = df_vp[df_vp['lop'] == user['lop_chu_nhiem']]
                if not my_data.empty:
                    # Tính tổng điểm (Net Score)
                    total_score = my_data['diem_tru'].sum()
                    st.metric("TỔNG ĐIỂM THI ĐUA (Net)", f"{total_score} điểm", 
                              delta_color="normal" if total_score >= 0 else "inverse")
                    
                    st.dataframe(my_data[['thoi_gian', 'hoc_sinh', 'noi_dung', 'diem_tru', 'ghi_chu']], use_container_width=True)
                else: st.info("Chưa có dữ liệu.")

    # ==================== 2. GIAMTHI ====================
    elif role == 'GIAMTHI':
        tab1, tab2 = st.tabs(["📝 NHẬP LIỆU", "🔎 TRA CỨU"])
        with tab1:
            st.subheader("Ghi nhận thi đua (Giám thị)")
            df_hs = load_data("HocSinh")
            df_tieuchi = load_data("TieuChiHS")
            with st.form("gt_report"):
                c1, c2, c3 = st.columns(3)
                with c1: 
                    sel_lop = st.selectbox("Lớp", sorted(df_hs['lop'].unique()))
                with c2: 
                    hs_list = df_hs[df_hs['lop'] == sel_lop]['ho_ten'].tolist()
                    sel_hs = st.selectbox("Học Sinh", hs_list)
                with c3:
                    sel_tc = st.selectbox("Tiêu chí", df_tieuchi['noi_dung'].tolist() if not df_tieuchi.empty else [])
                
                note_gt = st.text_input("Ghi chú")
                
                if st.form_submit_button("Lưu"):
                    score = 0
                    if not df_tieuchi.empty:
                        r = df_tieuchi[df_tieuchi['noi_dung'] == sel_tc]
                        if not r.empty: score = int(r.iloc[0]['diem_tru'])
                    
                    he_dt = df_hs[(df_hs['lop'] == sel_lop) & (df_hs['ho_ten'] == sel_hs)].iloc[0]['he_dao_tao']
                    row = [str(datetime.date.today()), user['username'], sel_lop, sel_hs, sel_tc, score, he_dt, note_gt]
                    if add_row_to_sheet("ViPhamHS", row): st.success("Đã lưu thành công!")

        with tab2: # Tra cứu (Giữ nguyên)
            search = st.text_input("Nhập tên HS cần tìm:")
            if search:
                df_vp = load_data("ViPhamHS")
                if not df_vp.empty:
                    st.dataframe(df_vp[df_vp['hoc_sinh'].str.contains(search, case=False, na=False)], use_container_width=True)

    # ==================== 3. BEP ====================
    elif role == 'BEP':
        st.subheader("🍚 BÁO CÁO SUẤT ĂN")
        if st.button("🔄 Cập nhật"): st.rerun()
        
        today = str(datetime.date.today())
        df_hs = load_data("HocSinh")
        df_vp = load_data("ViPhamHS")
        
        # Chỉ tính những lỗi có chữ "Vắng" là trừ cơm
        absent_today = df_vp[
            (df_vp['thoi_gian'] == today) & 
            (df_vp['noi_dung'].str.contains("Vắng", case=False, na=False))
        ] if not df_vp.empty else pd.DataFrame()

        def calc_meal(he):
            total = len(df_hs[df_hs['he_dao_tao'] == he])
            absent = len(absent_today[absent_today['he_dao_tao'] == he]) if not absent_today.empty else 0
            return total, absent

        t_nt, a_nt = calc_meal("Nội trú")
        t_bt, a_bt = calc_meal("Bán trú")
        
        c1, c2 = st.columns(2)
        c1.metric("NỘI TRÚ", f"{t_nt - a_nt}", f"Vắng: {a_nt}")
        c2.metric("BÁN TRÚ", f"{t_bt - a_bt}", f"Vắng: {a_bt}")

    # ==================== 4. ADMIN ====================
    elif role == 'ADMIN':
        tab1, tab2, tab3 = st.tabs(["🏆 XẾP HẠNG THI ĐUA", "👩‍🏫 QUẢN LÝ GV", "⚙️ DỮ LIỆU"])
        
        with tab1:
            st.subheader("Bảng Xếp Hạng Thi Đua (Điểm Cao Xếp Trên)")
            df_vp = load_data("ViPhamHS")
            if not df_vp.empty:
                # Logic mới: Tổng điểm (Net Score) = Cộng - Trừ
                ranking = df_vp.groupby('lop')['diem_tru'].sum().reset_index()
                ranking.columns = ['Lớp', 'Tổng Điểm']
                # Sắp xếp giảm dần (Điểm cao nhất đứng đầu)
                ranking = ranking.sort_values('Tổng Điểm', ascending=False)
                
                c1, c2 = st.columns([1, 2])
                with c1: st.dataframe(ranking, use_container_width=True)
                with c2: st.bar_chart(ranking.set_index('Lớp'))
            else: st.info("Chưa có dữ liệu.")

        with tab2:
            st.subheader("Quản lý Giáo Viên")
            # Nhập lỗi/thưởng GV
            with st.expander("Ghi nhận Tiêu chí Giáo viên"):
                df_gv = load_data("GiaoVien")
                df_tc_gv = load_data("TieuChiGV")
                with st.form("adm_gv"):
                    sel_gv = st.selectbox("Giáo viên", df_gv['fullname'].tolist())
                    sel_tc = st.selectbox("Tiêu chí", df_tc_gv['noi_dung'].tolist() if not df_tc_gv.empty else [])
                    note = st.text_input("Ghi chú")
                    if st.form_submit_button("Lưu"):
                        score = 0
                        if not df_tc_gv.empty:
                            r = df_tc_gv[df_tc_gv['noi_dung'] == sel_tc]
                            if not r.empty: score = int(r.iloc[0]['diem_tru'])
                        add_row_to_sheet("ViPhamGV", [str(datetime.date.today()), user['username'], sel_gv, sel_tc, score, note])
                        st.success("Đã lưu!")
            
            st.write("Lịch sử nộp kế hoạch tuần:")
            st.dataframe(load_data("KeHoach"), use_container_width=True)

        with tab3:
            st.dataframe(load_data("ViPhamHS"), use_container_width=True)
