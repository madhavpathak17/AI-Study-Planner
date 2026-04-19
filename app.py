import streamlit as st
import pickle
import numpy as np
import pandas as pd
import csv
import re
import matplotlib.pyplot as plt

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="AI Study Planner", layout="centered")

# ------------------ STYLE ------------------
st.markdown("""
<style>
.main { background-color: #0E1117; }
h1, h2, h3 { text-align: center; }
</style>
""", unsafe_allow_html=True)

# ------------------ LOAD MODEL ------------------
model = pickle.load(open("model.pkl", "rb"))

USER_FILE = "users.csv"
DATA_FILE = "data_log.csv"

# ------------------ LOAD USERS ------------------
def load_users():
    try:
        return pd.read_csv(USER_FILE)
    except:
        return pd.DataFrame(columns=["username","password","role","name","email","mobile"])

# ------------------ SAVE USER ------------------
def save_user(user):
    df = load_users()
    df = pd.concat([df, pd.DataFrame([user])], ignore_index=True)
    df.to_csv(USER_FILE, index=False)

# ------------------ PASSWORD VALIDATION ------------------
def valid_password(p):
    return len(p) >= 8 and re.search(r"[!@#$%^&*]", p)

# ------------------ SESSION ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

# ------------------ LOGIN ------------------
def login():
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        df = load_users()
        user = df[(df.username==u) & (df.password==p)]
        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.username = u
            st.session_state.role = user.iloc[0]["role"]
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

# ------------------ SIGNUP ------------------
def signup():
    st.title("📝 Sign Up")

    name = st.text_input("Full Name")
    username = st.text_input("Username")
    email = st.text_input("Email")
    mobile = st.text_input("Mobile Number")
    password = st.text_input("Password", type="password")

    if st.button("Create Account"):
        df = load_users()

        if username in df.username.values:
            st.error("Username already exists")
            return

        if not valid_password(password):
            st.error("Password must be 8+ chars & contain special character")
            return

        st.info("📧 Email verified (simulation)")

        user = {
            "username": username,
            "password": password,
            "role": "user",
            "name": name,
            "email": email,
            "mobile": mobile
        }

        save_user(user)
        st.success("Account created! Please login.")

# ------------------ AUTH ------------------
if not st.session_state.logged_in:
    choice = st.radio("Select Option", ["Login", "Sign Up"])
    if choice == "Login":
        login()
    else:
        signup()
    st.stop()

# ------------------ SIDEBAR ------------------
st.sidebar.title("👤 Profile")
st.sidebar.write(f"User: {st.session_state.username}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ------------------ TITLE ------------------
st.title("🎓 AI Study Planner + Burnout Detector")
st.markdown("### 📌 Predict burnout based on your daily habits and get actionable suggestions")
st.markdown("---")

# ------------------ INPUT ------------------
col1, col2 = st.columns(2)

with col1:
    study = st.slider("Study Hours", 0, 12, 5)
    sleep = st.slider("Sleep Hours", 0, 12, 7)
    screen = st.slider("Screen Time", 0, 12, 4)

with col2:
    stress = st.slider("Stress Level", 1, 10, 5)
    activity = st.slider("Physical Activity", 0, 5, 2)

# ------------------ GRAPH ------------------
st.subheader("📊 Habit Overview")

fig, ax = plt.subplots(facecolor='#0E1117')
ax.set_facecolor('#0E1117')

features = ["Study", "Sleep", "Screen", "Stress", "Activity"]
values = [study, sleep, screen, stress, activity]

ax.bar(features, values, color='#4CAF50')

ax.set_ylabel("Hours / Level")
ax.set_title("Your Daily Habits")

ax.tick_params(colors='white')
ax.yaxis.label.set_color('white')
ax.title.set_color('white')

st.pyplot(fig)

# ------------------ LIVE ALERT ------------------
if sleep < 5:
    st.warning("⚠️ You are sleeping too less!")
elif sleep >= 7:
    st.success("✅ Good sleep habit!")

# ------------------ PREDICTION ------------------
if st.button("🚀 Predict"):

    input_data = np.array([[study, sleep, screen, stress, activity]])
    prediction = model.predict(input_data)
    proba = model.predict_proba(input_data)

    confidence = max(proba[0]) * 100

    if prediction[0] == 0:
        result = "Low"
        st.success("Low Burnout 😊")
    elif prediction[0] == 1:
        result = "Medium"
        st.warning("Medium Burnout ⚠️")
    else:
        result = "High"
        st.error("High Burnout 🔥")

    # -------- METRIC --------
    st.metric(label="Model Confidence", value=f"{confidence:.2f}%")

    # -------- SUMMARY --------
    st.markdown("### 📌 Summary")
    st.write(f"Burnout Level: **{result}**")
    st.write(f"Confidence: **{confidence:.2f}%")

    # -------- SAVE DATA --------
    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            st.session_state.username,
            study,
            sleep,
            screen,
            stress,
            activity,
            result
        ])

    # -------- SUGGESTIONS --------
    suggestions = []

    if sleep < 6:
        suggestions.append("Increase sleep for better focus")
    if screen > 6:
        suggestions.append("Reduce screen time")
    if activity < 2:
        suggestions.append("Do more physical activity")
    if study > 6:
        suggestions.append("Avoid over-studying")

    st.subheader("💡 Suggestions")

    if suggestions:
        for s in suggestions:
            st.info(f"👉 {s}")
    else:
        st.success("Great balance! Keep it up 👍")

    # -------- SCORE --------
    score = 100 - study*2 - screen*2 - stress*3 + sleep*2 + activity*3
    score = max(0, min(score, 100))

    if score >= 80:
        st.success(f"💯 Productivity Score: {score}")
    elif score >= 50:
        st.warning(f"⚖️ Productivity Score: {score}")
    else:
        st.error(f"⚠️ Productivity Score: {score}")

# ------------------ USER HISTORY ------------------
try:
    df = pd.read_csv(DATA_FILE)

    user_df = df[df["username"] == st.session_state.username]

    if not user_df.empty:
        st.subheader("📈 Your Progress Over Time")
        st.line_chart(user_df[["study","sleep","screen","stress","activity"]])

        st.subheader("📁 Recent Records")
        st.dataframe(user_df.tail(5))
except:
    st.info("📁 No history yet. Start using the app to track your progress!")


st.markdown("---")
st.markdown("Made by Madhav 🚀 | AI Study Planner Project")
