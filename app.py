from dotenv import load_dotenv
import streamlit as st
import os
from PIL import Image
import google.generativeai as genai
import pandas as pd

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# System prompt
input_prompt = """
You are an expert in understanding invoices.
You will receive input images as invoices &
you will have to return invoice number, date, buyer's address, item name, quantity, rate, total, taxable amount and total amount.
"""

# Streamlit UI
st.set_page_config(page_title="Gemini Invoice Analyzer")
st.title("🧾 Gemini Invoice Analyzer")

uploaded_file = st.file_uploader("📤 Upload an invoice image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(Image.open(uploaded_file), caption="Uploaded Invoice", use_container_width=True)

# Convert image for Gemini
def input_image_setup(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    return [{"mime_type": uploaded_file.type, "data": bytes_data}]

# Gemini response function
def get_gemini_response(image_parts, system_prompt, user_prompt=None):
    model = genai.GenerativeModel('gemini-1.5-flash')
    inputs = [system_prompt, image_parts[0]]
    if user_prompt:
        inputs.append(user_prompt)
    response = model.generate_content(inputs)
    return response.text

# Store image once
if uploaded_file:
    image_data = input_image_setup(uploaded_file)

# Buttons
analyze_button = st.button("🧠 Analyze Invoice")
user_prompt = st.text_input("❓ Ask a follow-up question about the invoice:")
ask_button = st.button("🔍 Ask Your Question")

# --- ANALYZE BUTTON ---
if analyze_button and uploaded_file:
    st.subheader("🧾 Invoice Summary")
    summary = get_gemini_response(image_data, input_prompt)
    st.write(summary)

    # Store summary in session state
    st.session_state.invoice_summary = summary

    # Parse for CSV saving
    parsed_summary = {}
    lines = summary.strip().split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            parsed_summary[key.strip()] = value.strip()

    df_summary = pd.DataFrame([parsed_summary]) if parsed_summary else pd.DataFrame([{"Summary": summary}])
    summary_csv_path = "invoice_summary.csv"
    df_summary.to_csv(summary_csv_path, index=False)

    with open(summary_csv_path, "rb") as f:
        st.download_button("📥 Download Summary as CSV", f, file_name="invoice_summary.csv", mime="text/csv")

# --- ASK BUTTON ---
if ask_button:
    if not user_prompt:
        st.warning("⚠️ Please enter a question before clicking 'Ask Your Question'.")
    else:
        if "invoice_summary" in st.session_state:
            st.subheader("🧾 Previous Invoice Summary")
            st.write(st.session_state.invoice_summary)
        else:
            st.info("ℹ️ Please analyze an invoice first to generate a summary.")

        st.subheader("❓ Answer to Your Question")
        answer = get_gemini_response(image_data, input_prompt, user_prompt)
        st.write(answer)

        # Save Q&A
        structured_data = {"User Prompt": user_prompt, "Response": answer}
        df = pd.DataFrame([structured_data])
        csv_path = "invoice_response.csv"
        df.to_csv(csv_path, index=False)

        with open(csv_path, "rb") as f:
            st.download_button("📥 Download Q&A as CSV", f, file_name="invoice_response.csv", mime="text/csv")
