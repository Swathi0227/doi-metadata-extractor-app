import streamlit as st
import zipfile
import os
import fitz  # PyMuPDF
import re
import pandas as pd
import tempfile

def extract_metadata_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    text = text.replace("\n", " ")
    metadata = {"Filename": os.path.basename(pdf_path)}

    doc = fitz.open(pdf_path)
    first_page_text = doc[0].get_text("text").split("\n")
    doc.close()

    metadata["Title"] = first_page_text[0] if first_page_text else "Not found"
    metadata["Authors"] = first_page_text[1] if len(first_page_text) > 1 else "Not found"

    doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", text, re.I)
    metadata["DOI"] = doi_match.group(0) if doi_match else "Not found"

    publisher_match = re.search(r"(Elsevier|Springer|IEEE|Wiley|ACM|Taylor & Francis|Nature|Science|AMS)", text, re.I)
    metadata["Publisher"] = publisher_match.group(0) if publisher_match else "Not found"

    volume_match = re.search(r"Vol\.?\s*(\d+)", text, re.I)
    metadata["Volume"] = volume_match.group(1) if volume_match else "Not found"

    issue_match = re.search(r"No\.?\s*(\d+)", text, re.I)
    metadata["Issue"] = issue_match.group(1) if issue_match else "Not found"

    pages_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", text)
    metadata["Pages"] = pages_match.group(0) if pages_match else "Not found"

    year_match = re.search(r"\b(19\d{2}|20\d{2}|2025)\b", text)
    metadata["Year"] = year_match.group(0) if year_match else "Not found"

    pub_date_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}", text, re.I)
    metadata["Publication Date"] = pub_date_match.group(0) if pub_date_match else "Not found"

    return metadata

st.title("📄 DOI Metadata Extractor")
st.write("Upload a ZIP file of PDFs. Extracted metadata will be available as an Excel file.")

uploaded_file = st.file_uploader("📤 Upload ZIP file", type="zip")

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.read())

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        metadata_list = []
        for file in os.listdir(tmpdir):
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(tmpdir, file)
                metadata = extract_metadata_from_pdf(pdf_path)
                metadata_list.append(metadata)

        if metadata_list:
            df = pd.DataFrame(metadata_list)
            excel_path = os.path.join(tmpdir, "metadata_output.xlsx")
            df.to_excel(excel_path, index=False)

            with open(excel_path, "rb") as f:
                st.success("✅ Excel Report Generated!")
                st.download_button("⬇️ Download Excel File", f, file_name="metadata_output.xlsx")
        else:
            st.warning("No PDFs found or DOI metadata not extracted.")
