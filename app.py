import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import time

st.set_page_config(page_title="Faculty Research Impact System",
                   page_icon="🎓",
                   layout="wide")

DB_NAME = "faculty.db"

# ---------------- DATABASE LAYER ----------------

def get_connection():
    conn = sqlite3.connect(
        DB_NAME,
        timeout=30,
        check_same_thread=False,
        isolation_level=None
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def execute_query(query, params=(), fetch=False, retries=3):
    for _ in range(retries):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall() if fetch else None
            conn.close()
            return result
        except sqlite3.OperationalError:
            time.sleep(0.3)
    st.error("Database busy. Try again.")
    return None

def fetch_dataframe(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# ---------------- TABLES ----------------

execute_query("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

execute_query("""
CREATE TABLE IF NOT EXISTS faculty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    email TEXT NOT NULL
)
""")

execute_query("""
CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER,
    title TEXT NOT NULL,
    year INTEGER,
    citations INTEGER,
    impact_factor REAL
)
""")

# ---------------- PASSWORD HASH ----------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Create default admin
try:
    execute_query(
        "INSERT INTO admin (username,password) VALUES (?,?)",
        ("admin", hash_password("admin123"))
    )
except:
    pass

# ---------------- SESSION ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.delete_confirm = False

# ---------------- LOGIN ----------------

def login_page():
    st.title("🎓 Faculty Research Impact System")
    st.subheader("Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = execute_query(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, hash_password(password)),
            fetch=True
        )

        if user:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid Credentials")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.write("👤 Logged in as Admin")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

menu = st.sidebar.selectbox("Navigation",
                            ["Dashboard",
                             "View Faculties",
                             "Add Faculty",
                             "Upload Faculty CSV",
                             "Add Publication",
                             "Faculty Ranking"])

# ---------------- DASHBOARD ----------------

if menu == "Dashboard":
    st.header("📊 Dashboard")

    pub = fetch_dataframe("SELECT * FROM publications")

    if not pub.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Publications", len(pub))
        col2.metric("Total Citations", pub["citations"].sum())
        col3.metric("Avg Impact",
                    round(pub["impact_factor"].mean(),2))

        st.bar_chart(pub.groupby("year")["citations"].sum())
    else:
        st.info("No publications available.")

# ---------------- VIEW FACULTIES ----------------

elif menu == "View Faculties":
    st.header("👨‍🏫 Active Faculties")

    df = fetch_dataframe("SELECT * FROM faculty")

    if not df.empty:

        search = st.text_input("🔍 Search by Name")
        if search:
            df = df[df["name"].str.contains(search,
                                            case=False,
                                            na=False)]

        dept_list = df["department"].unique()
        selected = st.selectbox("🏢 Filter by Department",
                                ["All"] + list(dept_list))

        if selected != "All":
            df = df[df["department"] == selected]

        st.dataframe(df, use_container_width=True)

        # Delete
        st.subheader("🗑 Delete Faculty")
        delete_id = st.number_input("Faculty ID", step=1)

        if st.button("Delete Faculty"):
            faculty = execute_query(
                "SELECT * FROM faculty WHERE id=?",
                (delete_id,), fetch=True
            )
            if faculty:
                st.session_state.delete_confirm = True
            else:
                st.error("Faculty not found")

        if st.session_state.delete_confirm:
            st.warning("Are you sure?")
            if st.button("Yes, Delete"):
                execute_query("DELETE FROM faculty WHERE id=?",
                              (delete_id,))
                st.success("Deleted")
                st.session_state.delete_confirm = False
                st.rerun()

    else:
        st.info("No faculty records.")

# ---------------- ADD FACULTY ----------------

elif menu == "Add Faculty":
    st.header("Add Faculty")

    name = st.text_input("Name")
    dept = st.text_input("Department")
    email = st.text_input("Email")

    if st.button("Add Faculty"):
        if name and dept and email:
            execute_query(
                "INSERT INTO faculty (name,department,email) VALUES (?,?,?)",
                (name, dept, email)
            )
            st.success("Faculty Added")
            st.rerun()
        else:
            st.warning("All fields required")

# ---------------- CSV UPLOAD ----------------

elif menu == "Upload Faculty CSV":
    st.header("📂 Upload Faculty CSV")

    file = st.file_uploader("Upload CSV", type=["csv"])

    if file:
        df = pd.read_csv(file)

        if {"name","department","email"}.issubset(df.columns):

            inserted = 0
            updated = 0

            for _, row in df.iterrows():

                name = str(row["name"]).strip()
                dept = str(row["department"]).strip()
                email = str(row["email"]).strip()

                existing = execute_query(
                    "SELECT * FROM faculty WHERE name=?",
                    (name,), fetch=True
                )

                if existing:
                    execute_query(
                        "UPDATE faculty SET department=?,email=? WHERE name=?",
                        (dept,email,name)
                    )
                    updated += 1
                else:
                    execute_query(
                        "INSERT INTO faculty (name,department,email) VALUES (?,?,?)",
                        (name,dept,email)
                    )
                    inserted += 1

            st.success(f"Inserted: {inserted} | Updated: {updated}")
            st.rerun()
        else:
            st.error("CSV must contain name, department, email")

# ---------------- ADD PUBLICATION ----------------

elif menu == "Add Publication":
    st.header("Add Publication")

    faculty = fetch_dataframe("SELECT * FROM faculty")

    if not faculty.empty:
        st.dataframe(faculty)

        fid = st.number_input("Faculty ID", step=1)
        title = st.text_input("Title")
        year = st.number_input("Year", 2000, 2030)
        citations = st.number_input("Citations", 0)
        impact = st.number_input("Impact Factor", 0.0)

        if st.button("Add Publication"):
            execute_query(
                """INSERT INTO publications
                   (faculty_id,title,year,citations,impact_factor)
                   VALUES (?,?,?,?,?)""",
                (fid,title,year,citations,impact)
            )
            st.success("Publication Added")
            st.rerun()
    else:
        st.warning("Add faculty first.")

# ---------------- RANKING ----------------

elif menu == "Faculty Ranking":
    st.header("🏆 Faculty Ranking")

    pub = fetch_dataframe("SELECT * FROM publications")

    if not pub.empty:
        ranking = pub.groupby("faculty_id").agg({
            "citations":"sum",
            "impact_factor":"mean",
            "title":"count"
        }).reset_index()

        ranking.columns = ["faculty_id",
                           "total_citations",
                           "avg_impact",
                           "publication_count"]

        ranking["research_score"] = (
            0.4*ranking["publication_count"] +
            0.3*ranking["total_citations"] +
            0.3*ranking["avg_impact"]
        )

        ranking = ranking.sort_values(by="research_score",
                                       ascending=False)

        st.dataframe(ranking, use_container_width=True)
    else:
        st.info("No publication data.")