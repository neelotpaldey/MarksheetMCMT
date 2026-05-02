import streamlit as st
import pandas as pd

# Future use (Google Sheets)
'''import gspread
from oauth2client.service_account import ServiceAccountCredentials'''


def main():
    st.set_page_config(page_title="Student Report", layout="wide")

    # Banner Image (Place banner.png in same folder)
    st.image("banner.png", use_container_width=True)

    st.markdown("---")

    # Student Info Section
    st.subheader("Student Details")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Name")
        father_name = st.text_input("Father's Name")
        admission_no = st.text_input("Admission Number")

    with col2:
        roll_no = st.text_input("Roll Number")
        university_roll = st.text_input("University Roll No")

    st.markdown("---")

    # Attendance Section
    st.subheader("Attendance")

    attendance_data = pd.DataFrame({
        "Semester 2": ["", "", ""],
        "Semester 3": ["", "", ""],
        "Semester 4": ["", "", ""],
        "Semester 5": ["", "", ""],
        "Semester 6": ["", "", ""],
    }, index=["Present", "Out of", "Percentage"])

    st.dataframe(attendance_data, use_container_width=True)

    st.markdown("---")

    # Result Section
    st.subheader("Result")

    result_data = pd.DataFrame({
        "Subject": ["Subject 1", "Subject 2", "Subject 3", "Subject 4", "Subject 5", "Total", "Percentage"],
        "Sessional": [""] * 7,
        "PUT": [""] * 7,
        "Subject Teacher": [""] * 7,
        "Remark": [""] * 7
    })

    st.dataframe(result_data, use_container_width=True)


if __name__ == "__main__":
    main()
