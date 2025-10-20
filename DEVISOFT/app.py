import streamlit as st
import pandas as pd
from datetime import datetime
import os, random, time, re
from io import BytesIO

# ===================== PAGE CONFIG =====================
st.set_page_config(page_title="SGS Annual Function 2025", layout="wide", page_icon="🎉")

# ===================== CONSTANTS =======================
ADMIN_PASSWORD = "sgs2025"
EVENT_DATETIME = datetime(2025, 12, 20, 0, 0, 0)

REG_FILE = "registrations.csv"
NOTICE_FILE = "notices.csv"
ALLOWED_FILE = "allowed_users.csv"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GALLERY_DIR = os.path.join(BASE_DIR, "gallery")

# ===================== HELPERS =========================
def safe_path(name: str) -> str:
    return os.path.join(BASE_DIR, name)

def load_csv(file, columns):
    try:
        return pd.read_csv(file)
    except Exception:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df

def normalize_number(series: pd.Series) -> pd.Series:
    return (series.astype(str)
            .str.replace(" ", "", regex=False)
            .str.replace("+91", "", regex=False)
            .str.replace("-", "", regex=False)
            .str.strip()
            .str[-10:])

def safe_show_image(filename: str, width=None):
    path = safe_path(filename)
    if os.path.exists(path):
        st.image(path, width=width)

def time_remaining_text() -> str:
    diff = EVENT_DATETIME - datetime.now()
    if diff.total_seconds() <= 0:
        return "🎉 Today is the Annual Function!"
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    mins, secs = divmod(rem, 60)
    return f"{days} days, {hours} hours, {mins} mins, {secs} secs"

def ensure_gallery():
    if not os.path.isdir(GALLERY_DIR):
        os.makedirs(GALLERY_DIR, exist_ok=True)

def list_gallery_images():
    ensure_gallery()
    exts = (".png", ".jpg", ".jpeg", ".gif", ".webp")
    files = [f for f in sorted(os.listdir(GALLERY_DIR)) if f.lower().endswith(exts)]
    # return relative paths so Streamlit can serve
    return [os.path.join("gallery", f) for f in files]

def sanitize_filename(name: str) -> str:
    # keep only letters, numbers, dot, dash, underscore
    name = os.path.basename(name)
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)

# ===================== BASIC STYLES ====================
st.markdown("""
<style>
.title-main {font-size: 40px; font-weight: 800;}
.subtitle   {font-size: 22px; color:#333;}
.countdown  {font-size: 24px; font-weight: 700; color:#b22222;}
.notice-box {background:#fff3cd;border:1px solid #ffeeba;padding:10px;border-radius:10px;margin:8px 0 16px;}
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { padding:10px 16px; border-radius:10px; background:#ffffffaa; }
.stButton>button { border-radius:10px; }
</style>
""", unsafe_allow_html=True)

# ===================== LOAD DATA =======================
allowed_df = load_csv(safe_path(ALLOWED_FILE), ["mobile_number","name"])
allowed_df["mobile_number"] = normalize_number(allowed_df["mobile_number"])

# ===================== SESSION STATE ===================
ss = st.session_state
if "logged_in" not in ss: ss.logged_in = False
if "mobile" not in ss: ss.mobile = ""
if "otp" not in ss: ss.otp = None
if "welcomed" not in ss: ss.welcomed = False
if "admin_logged_in" not in ss: ss.admin_logged_in = False

# ===================== SIDEBAR LOGIN ===================
def login_sidebar():
    st.sidebar.title("Login")

    if not ss.logged_in:
        mobile = st.sidebar.text_input("Enter 10-digit mobile number").strip()
        if len(mobile) > 10:
            mobile = mobile[-10:]

        if st.sidebar.button("Send OTP"):
            if mobile in allowed_df["mobile_number"].values:
                ss.otp = str(random.randint(100000, 999999))
                ss.mobile = mobile
                st.sidebar.success(f"OTP (Test Mode): {ss.otp}")
            else:
                st.sidebar.error("❌ Number not registered")

        if ss.otp:
            code = st.sidebar.text_input("Enter OTP")
            if st.sidebar.button("Verify"):
                if code == ss.otp:
                    ss.logged_in = True
                    st.sidebar.success("✅ Login Successful!")
                else:
                    st.sidebar.error("❌ Incorrect OTP")
    else:
        st.sidebar.success(f"Logged in as: {ss.mobile}")
        if st.sidebar.button("Logout"):
            for k in ["logged_in","mobile","otp","welcomed","admin_logged_in"]:
                if k in ss: del ss[k]
            st.rerun()

login_sidebar()
if not ss.logged_in:
    st.stop()

# One-time welcome splash
if not ss.welcomed:
    safe_show_image("mascot.png", width=280)
    st.subheader(f"🎉 Welcome, {ss.mobile}!")
    st.write("Redirecting to Home...")
    for i in range(3, 0, -1):
        st.write(f"Redirecting in {i}...")
        time.sleep(1)
    ss.welcomed = True
    st.rerun()

# ===================== TABS ============================
tabs = st.tabs(["Home", "Registration", "Gallery", "Announcements", "Admin"])

# --------------------- HOME ----------------------------
with tabs[0]:
    col1, col2 = st.columns([1,3], vertical_alignment="center")
    with col1:
        safe_show_image("mascot.png", width=320)
    with col2:
        safe_show_image("logo.png", width=520)
        st.markdown("<div class='title-main'>St. Gregorios H.S. School</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle'>45th Annual Day – Talent Meets Opportunity</div>", unsafe_allow_html=True)

    # Latest announcement preview
    notices_df = load_csv(NOTICE_FILE, ["Timestamp","Title","Message","PostedBy"])
    if not notices_df.empty:
        latest = notices_df.iloc[-1]
        st.markdown(
            f"<div class='notice-box'><b>📢 {latest['Title']}</b><br>{latest['Message']}</div>",
            unsafe_allow_html=True
        )

    st.markdown(f"<div class='countdown'>⏳ Countdown: {time_remaining_text()}</div>", unsafe_allow_html=True)

# ------------------- REGISTRATION ----------------------
with tabs[1]:
    st.header("Register Participation")
    with st.form("reg_form"):
        name = st.text_input("Name")
        clas = st.text_input("Class")
        sec = st.text_input("Section")
        item = st.text_input("Event / Item")
        addr = st.text_area("Address")
        bus = st.radio("Using School Bus?", ["Yes","No"])
        contact = st.text_input("Contact", value=ss.mobile)

        if st.form_submit_button("Submit"):
            df = load_csv(REG_FILE, ["Timestamp","Name","Class","Section","Item","Contact","Address","Bus","Status"])
            df.loc[len(df)] = [datetime.now(), name, clas, sec, item, contact, addr, bus, "Pending"]
            df.to_csv(REG_FILE, index=False)
            st.success("✅ Registered Successfully!")

    # View + CSV download
    st.subheader("Registered Students")
    view = load_csv(REG_FILE, ["Timestamp","Name","Class","Section","Item","Contact","Address","Bus","Status"])
    st.dataframe(view, use_container_width=True)
    csv_data = view.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download as CSV", data=csv_data, file_name="registrations.csv", mime="text/csv")

# ---------------------- GALLERY ------------------------
with tabs[2]:
    st.header("Gallery")
    ensure_gallery()
    imgs = list_gallery_images()
    if not imgs:
        st.info("No images yet. (Admin can upload in this tab.)")
    else:
        cols_per_row = 3
        for i in range(0, len(imgs), cols_per_row):
            row = st.columns(cols_per_row)
            for col, rel_img in zip(row, imgs[i:i+cols_per_row]):
                with col:
                    st.image(rel_img, use_container_width=True)

    # Admin-only upload
    if ss.admin_logged_in:
        st.subheader("Admin: Upload Image to Gallery")
        up = st.file_uploader("Choose an image (png/jpg/jpeg/gif/webp)", type=["png","jpg","jpeg","gif","webp"])
        if up is not None:
            filename = sanitize_filename(up.name)
            save_path = os.path.join(GALLERY_DIR, filename)
            try:
                with open(save_path, "wb") as f:
                    f.write(up.read())
                st.success(f"✅ Uploaded: {filename}")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to save file: {e}")

# ------------------- ANNOUNCEMENTS ---------------------
with tabs[3]:
    st.header("Announcements")
    n = load_csv(NOTICE_FILE, ["Timestamp","Title","Message","PostedBy"])
    if n.empty:
        st.info("No announcements yet.")
    else:
        for _, r in n.iterrows():
            ts = r["Timestamp"] if "Timestamp" in r and pd.notnull(r["Timestamp"]) else ""
            ts_fmt = ""
            try:
                if ts:
                    ts_fmt = pd.to_datetime(ts).strftime("%d-%b-%Y %I:%M %p")
            except Exception:
                pass
            st.write(f"### {r['Title']}\n{r['Message']}\n*By {r['PostedBy']}{(' on ' + ts_fmt) if ts_fmt else ''}*")

    # Admin-only post form (inside Announcements tab)
    if ss.admin_logged_in:
        st.subheader("Post a New Announcement (Admin)")
        title = st.text_input("Title")
        msg = st.text_area("Message")
        by = st.text_input("Posted By", value="Admin")
        if st.button("Post Announcement"):
            df = load_csv(NOTICE_FILE, ["Timestamp","Title","Message","PostedBy"])
            df.loc[len(df)] = [datetime.now(), title, msg, by]
            df.to_csv(NOTICE_FILE, index=False)
            st.success("✅ Announcement Posted!")
            st.experimental_rerun()

# ------------------------ ADMIN ------------------------
with tabs[4]:
    st.header("Admin")
    if not ss.admin_logged_in:
        pw = st.text_input("Enter Admin Password", type="password")
        if st.button("Login as Admin"):
            if pw == ADMIN_PASSWORD:
                ss.admin_logged_in = True
                st.success("✅ Admin Logged In!")
            else:
                st.error("❌ Incorrect Password")
    else:
        st.success("✅ Admin Access Granted")
        st.write("You can post announcements in the **Announcements** tab and upload gallery images in the **Gallery** tab.")
        if st.button("Logout Admin"):
            ss.admin_logged_in = False
            st.rerun()
