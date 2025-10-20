import streamlit as st
import pandas as pd
import os, random, time
from datetime import datetime

# ==================== CONFIGURATION ====================
st.set_page_config(page_title="SGS Annual Function 2025", layout="wide", page_icon="🎉")

ADMIN_PASSWORD = "sgs2025"
EVENT_DATETIME = datetime(2025, 12, 20, 0, 0, 0)  # 20-Dec-2025
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REG_FILE = "registrations.csv"
NOTICE_FILE = "notices.csv"
ALLOWED_FILE = "allowed_users.csv"
GALLERY_DIR = os.path.join(BASE_DIR, "gallery")

# ==================== HELPER FUNCTIONS ====================
def safe_path(filename: str) -> str:
    return os.path.join(BASE_DIR, filename)

def load_csv(file, columns):
    try:
        return pd.read_csv(file)
    except:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df

def normalize_number(series):
    return (
        series.astype(str)
        .str.replace(" ", "", regex=False)
        .str.replace("+91", "", regex=False)
        .str.strip()
        .str[-10:]
    )

def ensure_gallery():
    if not os.path.exists(GALLERY_DIR):
        os.makedirs(GALLERY_DIR)

def list_gallery_images():
    ensure_gallery()
    files = []
    for f in os.listdir(GALLERY_DIR):
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            files.append(os.path.join("gallery", f))
    return files

def safe_show_image(filename, width=None):
    path = safe_path(filename)
    if os.path.exists(path):
        st.image(path, width=width)
    else:
        st.error(f"❌ Image not found: {filename}")

def time_remaining():
    diff = EVENT_DATETIME - datetime.now()
    if diff.total_seconds() <= 0:
        return "🎉 Today is the Annual Function!"
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    mins, secs = divmod(rem, 60)
    return f"{days} days, {hours} hrs, {mins} mins, {secs} secs"

# ==================== LOAD ALLOWED USERS ====================
allowed_df = load_csv(safe_path(ALLOWED_FILE), ["mobile_number","name"])
allowed_df["mobile_number"] = normalize_number(allowed_df["mobile_number"])

# ==================== SESSION STATE ====================
ss = st.session_state
for key, val in {
    "logged_in": False,
    "mobile": "",
    "otp": None,
    "welcomed": False,
    "admin_logged_in": False,
}.items():
    if key not in ss:
        ss[key] = val

# ==================== LOGIN SIDEBAR ====================
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
            otp_entered = st.sidebar.text_input("Enter OTP")
            if st.sidebar.button("Verify OTP"):
                if otp_entered == ss.otp:
                    ss.logged_in = True
                    st.sidebar.success("✅ Login successful!")
                else:
                    st.sidebar.error("❌ Incorrect OTP")
    else:
        st.sidebar.success(f"Logged in as: {ss.mobile}")
        if st.sidebar.button("Logout"):
            for k in ["logged_in","mobile","otp","welcomed","admin_logged_in"]:
                if k in ss:
                    del ss[k]
            st.experimental_rerun()

login_sidebar()
if not ss.logged_in:
    st.stop()

# Show Welcome once
if not ss.welcomed:
    safe_show_image("mascot.png", width=250)
    st.subheader(f"🎉 Welcome, {ss.mobile}!")
    time.sleep(1)
    ss.welcomed = True
    st.experimental_rerun()

# ==================== TABS ====================
tabs = st.tabs(["Home", "Registration", "Gallery", "Announcements", "Admin"])

# -------------------- HOME TAB --------------------
with tabs[0]:
    col1, col2 = st.columns([1,3])
    with col1:
        safe_show_image("mascot.png", width=300)
    with col2:
        safe_show_image("logo.png", width=450)
        st.markdown("### 45th Annual Day – Talent Meets Opportunity")
    notices = load_csv(NOTICE_FILE, ["Timestamp","Title","Message","PostedBy"])
    if not notices.empty:
        latest = notices.iloc[-1]
        st.info(f"📢 **{latest['Title']}**\n{latest['Message']}")
    st.success(f"⏳ Countdown: {time_remaining()}")

# -------------------- REGISTRATION TAB --------------------
with tabs[1]:
    st.header("Register")
    with st.form("register_form"):
        name = st.text_input("Student Name")
        clas = st.text_input("Class")
        sec = st.text_input("Section")
        item = st.text_input("Event/Item")
        addr = st.text_area("Address")
        bus = st.radio("Using Bus?", ["Yes","No"])
        contact = st.text_input("Contact", value=ss.mobile)
        if st.form_submit_button("Submit"):
            df = load_csv(REG_FILE, ["Timestamp","Name","Class","Section","Item","Address","Bus","Contact","Status"])
            df.loc[len(df)] = [datetime.now(), name, clas, sec, item, addr, bus, contact, "Pending"]
            df.to_csv(REG_FILE, index=False)
            st.success("✅ Registered Successfully!")

    st.subheader("Registered Students")
    data = load_csv(REG_FILE, ["Timestamp","Name","Class","Section","Item","Address","Bus","Contact","Status"])
    st.dataframe(data, use_container_width=True)
    csv_data = data.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download CSV", csv_data, "registrations.csv", "text/csv")

# -------------------- GALLERY TAB --------------------
with tabs[2]:
    st.header("Gallery")
    ensure_gallery()
    images = list_gallery_images()

    if not images:
        st.error("📁 No images found in the `gallery` folder.")
    else:
        cols = st.columns(3)
        for idx, img in enumerate(images):
            try:
                cols[idx % 3].image(img, use_container_width=True)
            except:
                cols[idx % 3].warning(f"⚠ Could not load: {img}")

    if ss.admin_logged_in:
        st.subheader("Admin: Upload to Gallery")
        file = st.file_uploader("Upload Image", type=["png","jpg","jpeg","gif","webp"])
        if file:
            path = os.path.join(GALLERY_DIR, file.name)
            with open(path, "wb") as f:
                f.write(file.read())
            st.success(f"✅ Uploaded {file.name}")
            st.experimental_rerun()

# -------------------- ANNOUNCEMENTS TAB --------------------
with tabs[3]:
    st.header("Announcements")
    data = load_csv(NOTICE_FILE, ["Timestamp","Title","Message","PostedBy"])

    if data.empty:
        st.info("No announcements yet.")
    else:
        for _, row in data.iterrows():
            st.write(f"### {row['Title']}\n{row['Message']}\n*— {row['PostedBy']} on {row['Timestamp']}*")

    if ss.admin_logged_in:
        st.subheader("Post Announcement (Admin Only)")
        title = st.text_input("Title")
        msg = st.text_area("Message")
        by = st.text_input("Posted By", "Admin")
        if st.button("Post Announcement"):
            df = load_csv(NOTICE_FILE, ["Timestamp","Title","Message","PostedBy"])
            df.loc[len(df)] = [datetime.now(), title, msg, by]
            df.to_csv(NOTICE_FILE, index=False)
            st.success("✅ Announcement Posted")
            st.experimental_rerun()

# -------------------- ADMIN TAB --------------------
with tabs[4]:
    st.header("Admin Panel")
    if not ss.admin_logged_in:
        pw = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if pw == ADMIN_PASSWORD:
                ss.admin_logged_in = True
                st.success("✅ Admin Logged In")
            else:
                st.error("❌ Wrong Password")
    else:
        st.success("✅ You are logged in as Admin")
        if st.button("Logout Admin"):
            ss.admin_logged_in = False
            st.experimental_rerun()
