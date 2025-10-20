import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random, os, time

# ------------------------ SETTINGS ------------------------
st.set_page_config(page_title="SGS Annual Function 2025", layout="wide", page_icon="🎉")

# Event Date
EVENT_DATETIME = datetime(2025, 12, 20, 0, 0, 0)

# File Names
REG_FILE = "registrations.csv"
NOTICE_FILE = "notices.csv"
ALLOWED_FILE = "allowed_users.csv"

# Admin Password
ADMIN_PASSWORD = "sgs2025"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------ FUNCTIONS ------------------------
def safe_path(file):
    return os.path.join(BASE_DIR, file)

def load_csv(file, columns):
    try:
        return pd.read_csv(file)
    except:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df

def normalize_number(series):
    return (series.astype(str)
            .str.replace(" ", "", regex=False)
            .str.replace("+91", "", regex=False)
            .str.strip()
            .str[-10:])

def safe_show_image(filename, width=None):
    path = safe_path(filename)
    if os.path.exists(path):
        st.image(path, width=width)
    else:
        st.warning(f"⚠ Image not found: {filename}")

def time_remaining():
    diff = EVENT_DATETIME - datetime.now()
    if diff.total_seconds() <= 0:
        return "🎉 Today is the Annual Function!"
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    mins, secs = divmod(rem, 60)
    return f"{days} days, {hours} hours, {mins} mins, {secs} secs"

st.markdown("""
<style>
.countdown {
    font-size: 24px;
    font-weight: bold;
    color: #b22222;
}
.title-main {
    font-size: 40px;
    font-weight: bold;
}
.subtitle {
    font-size: 24px;
    color: #444;
}
.notice-box {
    background: #fff3cd;
    padding: 10px;
    border-radius: 10px;
    border: 1px solid #ffeeba;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------ LOAD DATA ------------------------
allowed_df = load_csv(safe_path(ALLOWED_FILE), ["mobile_number","name"])
allowed_df["mobile_number"] = normalize_number(allowed_df["mobile_number"])

# Session States
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "mobile" not in st.session_state:
    st.session_state.mobile = ""
if "otp" not in st.session_state:
    st.session_state.otp = None
if "welcomed" not in st.session_state:
    st.session_state.welcomed = False

# ------------------------ LOGIN SYSTEM ------------------------
def login_sidebar():
    st.sidebar.title("Login")

    if not st.session_state.logged_in:
        mobile = st.sidebar.text_input("Enter 10-digit mobile number").strip()
        if len(mobile) > 10:
            mobile = mobile[-10:]

        if st.sidebar.button("Send OTP"):
            if mobile in allowed_df["mobile_number"].values:
                otp = str(random.randint(100000, 999999))
                st.session_state.otp = otp
                st.sidebar.success(f"OTP (Test Mode): {otp}")
                st.session_state.mobile = mobile
            else:
                st.sidebar.error("❌ Number not registered")

        if st.session_state.otp:
            code = st.sidebar.text_input("Enter OTP")
            if st.sidebar.button("Verify"):
                if code == st.session_state.otp:
                    st.session_state.logged_in = True
                    st.sidebar.success("✅ Login Successful!")
                else:
                    st.sidebar.error("❌ Incorrect OTP")

    else:
        st.sidebar.success(f"Logged in as: {st.session_state.mobile}")
        if st.sidebar.button("Logout"):
            for k in ["logged_in","mobile","otp","welcomed"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

login_sidebar()
if not st.session_state.logged_in:
    st.stop()

# ------------------------ WELCOME SPLASH ------------------------
if not st.session_state.welcomed:
    st.title("🎉 Welcome to SGS Annual Function Portal")
    for i in range(3, 0, -1):
        st.write(f"Redirecting to Home in {i}...")
        time.sleep(1)
    st.session_state.welcomed = True
    st.rerun()

# ------------------------ TABS ------------------------
tabs = st.tabs(["Home", "Registration", "List", "Notices", "Admin"])

# ------------------------ HOME TAB ------------------------
with tabs[0]:
    left, right = st.columns([1,3])
    with left:
        safe_show_image("mascot.png", width=300)
    with right:
        safe_show_image("logo.png", width=450)

    st.markdown("<div class='title-main'>St. Gregorios H.S. School</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>45th Annual Day – Talent Meets Opportunity</div>", unsafe_allow_html=True)

    # Latest Notice
    notice_df = load_csv(NOTICE_FILE, ["Timestamp","Title","Message","PostedBy"])
    if not notice_df.empty:
        latest = notice_df.iloc[-1]
        st.markdown(f"<div class='notice-box'><b>📢 {latest['Title']}</b><br>{latest['Message']}</div>",
                    unsafe_allow_html=True)

    st.markdown(f"<div class='countdown'>⏳ Countdown: {time_remaining()}</div>", unsafe_allow_html=True)

# ------------------------ REGISTRATION TAB ------------------------
with tabs[1]:
    st.header("Register for Participation")
    with st.form("reg_form"):
        name = st.text_input("Name")
        clas = st.text_input("Class")
        sec = st.text_input("Section")
        item = st.text_input("Event")
        addr = st.text_area("Address")
        bus = st.radio("Using School Bus?", ["Yes","No"])
        contact = st.text_input("Contact", value=st.session_state.mobile)
        submitted = st.form_submit_button("Submit")
        if submitted:
            df = load_csv(REG_FILE, ["Timestamp","Name","Class","Section","Item","Contact","Address","Bus","Status"])
            df.loc[len(df)] = [datetime.now(), name, clas, sec, item, contact, addr, bus, "Pending"]
            df.to_csv(REG_FILE, index=False)
            st.success("✅ Registered Successfully!")

# ------------------------ LIST TAB ------------------------
with tabs[2]:
    st.header("Registered Students")
    df = load_csv(REG_FILE, ["Timestamp","Name","Class","Section","Item","Contact","Address","Bus","Status"])
    st.dataframe(df, use_container_width=True)

    # ✅ CSV Export (No Errors, No Libraries Needed)
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Download CSV", data=csv_data, file_name="registrations.csv", mime="text/csv")

# ------------------------ NOTICES TAB ------------------------
with tabs[3]:
    st.header("Notices & Announcements")
    df = load_csv(NOTICE_FILE, ["Timestamp","Title","Message","PostedBy"])
    if df.empty:
        st.info("No notices yet")
    else:
        for _, r in df.iterrows():
            st.write(f"### {r['Title']}\n{r['Message']}\n*Posted by {r['PostedBy']}*")

# ------------------------ ADMIN TAB ------------------------
# ------------------------ ADMIN TAB ------------------------
with tabs[4]:
    st.header("Admin Panel")

    # ✅ Keep track of Admin login state
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    # ✅ Show login box if admin is not logged in
    if not st.session_state.admin_logged_in:
        pw = st.text_input("Enter Admin Password", type="password")
        if st.button("Login as Admin"):
            if pw == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("✅ Admin Logged In Successfully!")
            else:
                st.error("❌ Incorrect Password")

    # ✅ If admin is logged in, show notice posting
