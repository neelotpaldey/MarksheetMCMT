# main.py
import streamlit as st
import pandas as pd
import requests
import io
import unicodedata
import streamlit.components.v1 as components

# ---------------- CONFIG ----------------
GOOGLE_SHEET_FILE_ID = "1MKgETtpCs4MOTL8ErQuPIjIR2peBXADx"

st.set_page_config(page_title="Marksheet Viewer", layout="wide")


# ---------------- GOOGLE SHEET LOADER ----------------
@st.cache_data(ttl=300)
def download_sheet_xlsx(file_id: str) -> bytes:
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def load_excel(file_id):
    content = download_sheet_xlsx(file_id)
    return pd.ExcelFile(io.BytesIO(content), engine="openpyxl")


def read_sheet(file_id, sheet_name):
    content = download_sheet_xlsx(file_id)
    return pd.read_excel(
        io.BytesIO(content),
        sheet_name=sheet_name,
        skiprows=6,   # 🔥 header is row 7
        engine="openpyxl"
    )


# ---------------- HELPERS ----------------
def to_float(val):
    try:
        if pd.isna(val):
            return None
    except:
        pass

    s = str(val).strip()
    if s == "":
        return None

    s = unicodedata.normalize("NFKC", s)

    try:
        return float(s.replace(",", "").replace("%", ""))
    except:
        return None


def parse_sheet(sheetname: str):
    parts = sheetname.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], parts[1], sheetname
    return sheetname, "", sheetname


def find_column(df, keywords):
    for col in df.columns:
        col_clean = col.strip().lower()
        for key in keywords:
            if key in col_clean:
                return col
    return None


# ---------------- MAIN ----------------
def main():

    # ---------- Banner ----------
    try:
        st.image("banner.png", use_container_width=True)
    except:
        pass

    st.title("📄 Marksheet Viewer")

    # ---------- Print Button ----------
    if st.button("🖨️ Print Marksheet"):
        components.html("<script>window.print();</script>", height=0)

    # ---------- Load Sheets ----------
    try:
        xls = load_excel(GOOGLE_SHEET_FILE_ID)
        sheets = xls.sheet_names
    except Exception as e:
        st.error(f"Error loading sheet: {e}")
        return

    parsed = [parse_sheet(s) for s in sheets]

    # ---------- University ----------
    universities = sorted({u for u, y, o in parsed})
    uni = st.selectbox("Select University", ["-- choose --"] + universities)
    if uni == "-- choose --":
        return

    # ---------- Admission Year ----------
    years = sorted({y for u, y, o in parsed if u == uni})
    year = st.selectbox("Select Admission Year", ["-- choose --"] + years)
    if year == "-- choose --":
        return

    # ---------- Get Sheet ----------
    sheet_name = [o for u, y, o in parsed if u == uni and y == year][0]

    # ---------- Load Data ----------
    df = read_sheet(GOOGLE_SHEET_FILE_ID, sheet_name)
    df.columns = [str(c).strip() for c in df.columns]

    # ---------- Detect Columns ----------
    student_col = find_column(df, ["student", "name"])
    admission_col = find_column(df, ["admission"])
    father_col = find_column(df, ["father"])

    if not student_col:
        st.error("Student name column not found")
        st.write("Available columns:", df.columns.tolist())
        return

    # ---------- Student Selection ----------
    students = df[student_col].dropna().astype(str).tolist()
    student = st.selectbox("Select Student", ["-- choose --"] + students)
    if student == "-- choose --":
        return

    row = df[df[student_col].astype(str) == student].iloc[0]

    # ---------- Student Details ----------
    st.subheader("👤 Student Details")
    st.write(f"**Name:** {row[student_col]}")

    if admission_col:
        st.write(f"**Admission No:** {row[admission_col]}")

    if father_col:
        st.write(f"**Father Name:** {row[father_col]}")

    # ---------- Attendance Placeholder ----------
    st.subheader("📅 Attendance")

    attendance_df = pd.DataFrame({
        " ": ["Present", "Out of", "Percentage"],
        "Semester 2": ["", "", ""],
        "Semester 3": ["", "", ""],
        "Semester 4": ["", "", ""],
        "Semester 5": ["", "", ""],
        "Semester 6": ["", "", ""],
    })

    st.table(attendance_df)

    # ---------- MARKS LOGIC ----------

    sessional_cols = df.columns[16:21]   # Q-U
    put_cols = df.columns[23:28]         # X-AB

    sessional_subjects, sessional_marks = [], []
    put_subjects, put_marks = [], []

    # Sessional
    for col in sessional_cols:
        subject = str(col).strip()
        value = to_float(row[col])

        if subject != "" and value is not None:
            sessional_subjects.append(subject)
            sessional_marks.append(value)

    # PUT
    for col in put_cols:
        subject = str(col).strip()
        value = to_float(row[col])

        if subject != "" and value is not None:
            put_subjects.append(subject)
            put_marks.append(value)

    # ---------- UNIVERSITY RULE ----------
    if "MGKVP" in uni.upper():
        sess_max = 25
        put_max = 75
    elif "VBSPU" in uni.upper():
        sess_max = 30
        put_max = 70
    else:
        sess_max = 25
        put_max = 75

    # ---------- CALCULATION ----------
    total_obtained = sum(sessional_marks) + sum(put_marks)

    total_max = (len(sessional_marks) * sess_max) + (len(put_marks) * put_max)

    percentage = round((total_obtained / total_max) * 100, 2) if total_max else 0

    # ---------- DISPLAY MARKS ----------

    st.subheader("📘 Sessional Marks")
    st.table(pd.DataFrame({
        "Subject": sessional_subjects,
        "Marks": sessional_marks
    }))

    st.subheader("📗 PUT Marks")
    st.table(pd.DataFrame({
        "Subject": put_subjects,
        "Marks": put_marks
    }))

    st.subheader("📊 Result Summary")
    st.table(pd.DataFrame({
        "Metric": ["Total Obtained", "Total Maximum", "Percentage"],
        "Value": [total_obtained, total_max, f"{percentage}%"]
    }))


if __name__ == "__main__":
    main()
