import streamlit as st
import pandas as pd
import requests
import io
import streamlit.components.v1 as components

# ---------------- CONFIG ----------------
GOOGLE_SHEET_FILE_ID = "1cH7emSI1m0VZf205GADUqj0sANHZAU0jnttpS4HYCWg"

# ---------------- GOOGLE SHEET LOADER ----------------
@st.cache_data(ttl=300)
def download_sheet(file_id):
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    r = requests.get(url)
    r.raise_for_status()
    return r.content


def load_excel(file_id):
    content = download_sheet(file_id)
    return pd.ExcelFile(io.BytesIO(content), engine="openpyxl")


def read_sheet(file_id, sheet_name):
    content = download_sheet(file_id)
    return pd.read_excel(io.BytesIO(content), sheet_name=sheet_name, engine="openpyxl")


# ---------------- PARSE SHEET NAME ----------------
def parse_sheet(name):
    parts = name.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], parts[1], name
    return name, "", name


# ---------------- MAIN ----------------
def main():
    st.set_page_config(page_title="Student Report", layout="wide")

    # -------- PRINT STYLE --------
    st.markdown("""
    <style>
    @media print {
        header, footer, .stDeployButton, .stToolbar {
            display: none !important;
        }
        button {
            display: none !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # -------- HEADER --------
    try:
        st.image("banner.png", use_container_width=True)
    except:
        pass

    st.markdown("<h3 style='text-align:center;'>SMART ATTENDANCE SYSTEM</h3>", unsafe_allow_html=True)
    st.markdown("---")

    # -------- LOAD SHEETS --------
    try:
        xls = load_excel(GOOGLE_SHEET_FILE_ID)
        sheets = xls.sheet_names
    except Exception as e:
        st.error(f"Error loading sheet: {e}")
        return

    parsed = [parse_sheet(s) for s in sheets]
    universities = sorted({u for u, sem, _ in parsed})

    col1, col2 = st.columns(2)

    with col1:
        uni = st.selectbox("University", universities)

    with col2:
        sems = sorted({sem for u, sem, _ in parsed if u == uni})
        sem = st.selectbox("Semester", sems)

    sheet_name = [orig for u, s, orig in parsed if u == uni and s == sem][0]

    # -------- LOAD SHEET DATA --------
    df = read_sheet(GOOGLE_SHEET_FILE_ID, sheet_name)

    # -------- STUDENT LIST (Column C, row 7 onwards) --------
    students_df = df.iloc[6:, 2].dropna()
    students = students_df.tolist()

    student = st.selectbox("Select Student", students)

    # -------- GET ROW INDEX --------
    row_index = students_df[students_df == student].index[0]

    # -------- STUDENT DETAILS --------
    roll_no = df.iloc[row_index, 0]
    admission_no = df.iloc[row_index, 1]
    name = df.iloc[row_index, 2]
    father_name = df.iloc[row_index, 3] if len(df.columns) > 3 else ""

    st.markdown("---")
    st.subheader("Student Details")

    c1, c2 = st.columns(2)

    with c1:
        st.text_input("Name", name, disabled=True)
        st.text_input("Admission No", admission_no, disabled=True)
        st.text_input("Father Name", father_name, disabled=True)

    with c2:
        st.text_input("Roll No", roll_no, disabled=True)

    st.markdown("---")

    # -------- SUBJECTS (Row 6) --------
    subjects = df.iloc[5, 13:18].tolist()   # N–R

    # -------- MARKS --------
    sessional_marks = df.iloc[row_index, 13:18]   # N–R
    put_marks = df.iloc[row_index, 20:25]         # U–Y

    # -------- RESULT TABLE --------
    st.subheader("Result")

    result_df = pd.DataFrame({
        "Subject": subjects,
        "Sessional": sessional_marks.values,
        "PUT": put_marks.values
    })

    result_df = result_df.fillna("")

    st.table(result_df)

    st.markdown("---")

    # -------- PRINT BUTTON --------
    if st.button("🖨️ Print / Save as PDF"):
        components.html("<script>window.print();</script>", height=0)


if __name__ == "__main__":
    main()
