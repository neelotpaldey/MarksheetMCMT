import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def main():
    st.set_page_config(page_title="Student Report", layout="wide")

    # ---------------- PRINT STYLE ----------------
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

    # ---------------- BANNER ----------------
    st.image("banner.png", use_container_width=True)
    st.markdown("---")

    # ---------------- STUDENT DETAILS ----------------
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

    # ---------------- ATTENDANCE ----------------
    st.subheader("Attendance")

    attendance_df = pd.DataFrame({
        "Semester 2": ["", "", ""],
        "Semester 3": ["", "", ""],
        "Semester 4": ["", "", ""],
        "Semester 5": ["", "", ""],
        "Semester 6": ["", "", ""],
    }, index=["Present", "Out of", "Percentage"])

    attendance = st.data_editor(attendance_df, use_container_width=True)

    st.markdown("---")

    # ---------------- RESULT ----------------
    st.subheader("Result")

    result_df = pd.DataFrame({
        "Subject": ["Subject 1", "Subject 2", "Subject 3", "Subject 4", "Subject 5"],
        "Sessional": [""] * 5,
        "PUT": [""] * 5,
        "Subject Teacher": [""] * 5,
        "Remark": [""] * 5
    })

    result = st.data_editor(result_df, use_container_width=True)

    st.markdown("---")

    # ---------------- PRINT BUTTON ----------------
    if st.button("🖨️ Print / Save as PDF"):
        components.html(
            """
            <script>
                window.print();
            </script>
            """,
            height=0,
        )


if __name__ == "__main__":
    main()
