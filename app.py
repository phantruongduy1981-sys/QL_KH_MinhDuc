import streamlit as st
import pandas as pd
import datetime
import time

# --- CẤU HÌNH TRANG & CSS HIỆN ĐẠI ---
st.set_page_config(
    page_title="Hệ Thống Quản Lý Giáo Dục THPT Minh Đức",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS để giao diện đẹp, khoa học
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #4361ee, #3a0ca3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center; color: #6c757d; font-size: 1.1rem; margin-bottom: 2rem;
    }
    .stCard {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem; color: #4361ee;
    }
</style>
""", unsafe_allow_html=True)

# --- KHỞI TẠO DỮ LIỆU GIẢ LẬP (MOCK DATA) ---
if 'data_students' not in st.session_state:
    st.session_state.data_students = pd.DataFrame([
        {"maHS": "HS001", "tenHS": "Nguyễn Minh Khang", "lop": "10A1", "he": "Nội trú", "gioiTinh": "Nam"},
        {"maHS": "HS002", "tenHS": "Lê Thị Hoa", "lop": "10A1", "he": "Bán trú", "gioiTinh": "Nữ"},
        {"maHS": "HS003", "tenHS": "Trần Văn Nam", "lop": "10A2", "he": "Hai buổi", "gioiTinh": "Nam"},
        {"maHS": "HS004", "tenHS": "Phạm Quỳnh Anh", "lop": "11A1", "he": "Nội trú", "gioiTinh": "Nữ"},
        {"maHS": "HS005", "tenHS": "Đỗ Hùng Dũng", "lop": "12A1", "he": "Bán trú", "gioiTinh": "Nam"},
    ])

if 'data_violations' not in st.session_state:
    st.session_state.data_violations = pd.DataFrame(columns=["Ngay", "Lop", "HocSinh", "Loi", "Diem", "GhiChu", "NguoiBao"])

if 'data_plans' not in st.session_state:
    st.session_state.data_plans = pd.DataFrame(columns=["Tuan", "GiaoVien", "Lop", "NgayNop", "TrangThai", "TenFile", "GhiChu"])

if 'data_teachers' not in st.session_state:
    st.session_state.data_teachers = pd.DataFrame([
        {"username": "admin", "password": "123", "fullname": "Thầy Quản Trị", "role": "ADMIN", "class": ""},
        {"username": "gv01", "password": "123", "fullname": "Cô Nguyễn Thị Lan", "role": "GVQN", "class": "10A1"},
        {"username": "gv02", "password": "123", "fullname": "Thầy Trần Minh", "role": "GVQN", "class": "11A1"},
    ])

if 'criteria_violations' not in st.session_state:
    st.session_state.criteria_violations = pd.DataFrame([
        {"Loi": "Vắng học (Sáng)", "Diem": 5},
        {"Loi": "Vắng học (Chiều)", "Diem": 5},
        {"Loi": "Đi trễ", "Diem": 2},
        {"Loi": "Không đồng phục", "Diem": 3},
        {"Loi": "Mất trật tự", "Diem": 2},
    ])

# --- HÀM XỬ LÝ LOGIC ---
def login(username, password):
    users = st.session_state.data_teachers
    user = users[(users['username'] == username) & (users['password'] == password)]
    if not user.empty: return user.iloc[0].to_dict()
    return None

def save_violation(date, lop, hs_name, loi, diem, note, user):
    new_row = {"Ngay": date, "Lop": lop, "HocSinh": hs_name, "Loi": loi, "Diem": diem, "GhiChu": note, "NguoiBao": user}
    st.session_state.data_violations = pd.concat([st.session_state.data_violations, pd.DataFrame([new_row])], ignore_index=True)

def save_plan(tuan, gv, lop, file_obj, note):
    now = datetime.datetime.now()
    status = "Đúng hạn" if now.weekday() == 0 and now.hour < 10 else "Trễ hạn" # Demo logic: Thứ 2 trước 10h
    # Nếu đang chạy demo thì coi như đúng hạn để test
    status = "Đúng hạn" 
    
    file_name = file_obj.name
    new_row = {
        "Tuan": tuan, "GiaoVien": gv, "Lop": lop, 
        "NgayNop": now.strftime("%d/%m/%Y %H:%M"), 
        "TrangThai": status, "TenFile": file_name, "GhiChu": note
    }
    st.session_state.data_plans = pd.concat([st.session_state.data_plans, pd.DataFrame([new_row])], ignore_index=True)

# --- GIAO DIỆN: LOGIN ---
if 'user' not in st.session_state:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='main-header'>TRƯỜNG THPT MINH ĐỨC</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>HỆ THỐNG QUẢN LÝ TÍCH HỢP</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("### Đăng nhập hệ thống")
            username = st.text_input("Tài khoản (admin / gv01)")
            password = st.text_input("Mật khẩu (123)", type="password")
            submit = st.form_submit_button("Đăng Nhập", use_container_width=True)
            if submit:
                user_info = login(username, password)
                if user_info:
                    st.session_state.user = user_info
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu")

# --- GIAO DIỆN CHÍNH ---
else:
    user = st.session_state.user
    
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        st.title(f"Xin chào,\n{user['fullname']}")
        st.info(f"Vai trò: {user['role']}")
        if user['class']: st.success(f"Chủ nhiệm: {user['class']}")
        if st.button("Đăng xuất", type="primary"):
            del st.session_state.user
            st.rerun()
        st.markdown("---")
        st.caption("© 2025 THPT Minh Đức")

    st.markdown("<div class='main-header'>CỔNG THÔNG TIN ĐIỆN TỬ</div>", unsafe_allow_html=True)

    # --- VIEW GIÁO VIÊN ---
    if user['role'] == 'GVQN':
        tab1, tab2, tab3 = st.tabs(["📝 BÁO CÁO THI ĐUA", "🕰 LỊCH SỬ VI PHẠM", "📂 KẾ HOẠCH / GIÁO ÁN"])
        
        with tab1:
            st.subheader(f"Ghi nhận thi đua - Lớp {user['class']}")
            col1, col2 = st.columns(2)
            with col1:
                students = st.session_state.data_students[st.session_state.data_students['lop'] == user['class']]
                selected_std = st.selectbox("Chọn Học sinh", students['tenHS'].tolist())
            with col2:
                criteria = st.session_state.criteria_violations
                selected_err = st.selectbox("Lỗi vi phạm", criteria['Loi'].tolist())
                score = criteria[criteria['Loi'] == selected_err]['Diem'].values[0]
                st.metric("Điểm trừ", f"-{score}")
            note = st.text_area("Ghi chú")
            if st.button("Lưu Vi Phạm", type="primary", use_container_width=True):
                save_violation(datetime.date.today(), user['class'], selected_std, selected_err, score, note, user['username'])
                st.success("Đã lưu!")
                time.sleep(0.5); st.rerun()

        with tab2:
            st.subheader("Lịch sử ghi nhận")
            df_hist = st.session_state.data_violations[st.session_state.data_violations['Lop'] == user['class']]
            st.dataframe(df_hist, use_container_width=True) if not df_hist.empty else st.info("Chưa có dữ liệu.")

        with tab3:
            st.markdown("### 📤 Nộp Kế Hoạch Tuần")
            col1, col2 = st.columns([1, 2])
            with col1: week_upload = st.selectbox("Chọn Tuần", [f"Tuần {i}" for i in range(1, 21)], index=14)
            with col2: note_upload = st.text_input("Ghi chú file")
            uploaded_file = st.file_uploader("Chọn file (PDF, Word)", type=['pdf', 'docx'])
            if uploaded_file and st.button("Nộp Kế Hoạch", type="primary"):
                save_plan(week_upload, user['fullname'], user['class'], uploaded_file, note_upload)
                st.success("Nộp thành công!")
                time.sleep(0.5); st.rerun()
            
            st.divider()
            st.subheader("Lịch sử nộp")
            my_plans = st.session_state.data_plans[st.session_state.data_plans['GiaoVien'] == user['fullname']]
            st.dataframe(my_plans, use_container_width=True) if not my_plans.empty else st.caption("Chưa có dữ liệu.")

    # --- VIEW ADMIN ---
    elif user['role'] == 'ADMIN':
        tab1, tab2, tab3, tab4 = st.tabs(["📊 QUẢN LÝ THI ĐUA", "📈 THỐNG KÊ GIÁO VIÊN", "📑 KHO KẾ HOẠCH", "🍲 BÁO CƠM"])
        
        with tab1:
            st.subheader("Dữ liệu vi phạm toàn trường")
            filter_class = st.selectbox("Lọc lớp", ["Tất cả"] + sorted(st.session_state.data_students['lop'].unique().tolist()))
            df_view = st.session_state.data_violations
            if filter_class != "Tất cả": df_view = df_view[df_view['Lop'] == filter_class]
            st.dataframe(df_view, use_container_width=True)

        with tab2:
            st.subheader("Thống Kê Giáo Viên (Thi đua & Kế hoạch)")
            stats_data = []
            teachers = st.session_state.data_teachers[st.session_state.data_teachers['role'] != 'ADMIN']
            for _, t in teachers.iterrows():
                late = len(st.session_state.data_plans[(st.session_state.data_plans['GiaoVien'] == t['fullname']) & (st.session_state.data_plans['TrangThai'] == 'Trễ hạn')])
                vio_pts = st.session_state.data_violations[st.session_state.data_violations['Lop'] == t['class']]['Diem'].sum() if t['class'] else 0
                stats_data.append({"Giáo Viên": t['fullname'], "Lớp CN": t['class'], "Nộp Trễ": late, "Điểm Trừ Lớp": vio_pts})
            
            df_stats = pd.DataFrame(stats_data)
            c1, c2 = st.columns([1, 2])
            with c1: st.dataframe(df_stats, use_container_width=True)
            with c2: st.bar_chart(df_stats.set_index("Giáo Viên")[["Nộp Trễ", "Điểm Trừ Lớp"]])

        with tab3:
            st.subheader("Kho Kế Hoạch Đã Nộp")
            st.dataframe(st.session_state.data_plans, use_container_width=True)

        with tab4:
            st.subheader("Báo Cơm")
            c1, c2, c3 = st.columns(3)
            c1.metric("Nội trú", "150"); c2.metric("Bán trú", "320"); c3.metric("Tổng", "470")
