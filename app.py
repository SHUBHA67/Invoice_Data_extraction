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

# System prompt for invoice understanding
input_prompt = """
You are an expert in understanding invoices.
You will receive input images as invoices &
you will have to return inovice number,date,buyer's address,item name,quantity,rate,total,taxable amount and total amount.
"""

# Streamlit UI
st.set_page_config(page_title="Gemini Invoice Analyzer")
st.title("🧾 Gemini Invoice Analyzer")

uploaded_file = st.file_uploader("📤 Upload an invoice image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(Image.open(uploaded_file), caption="Uploaded Invoice", use_container_width=True)

analyze_button = st.button("🧠 Analyze Invoice")

user_prompt = st.text_input("❓ Ask a follow-up question about the invoice:")
ask_button = st.button("🔍 Ask Your Question")

# Convert image for Gemini
def input_image_setup(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    return [{"mime_type": uploaded_file.type, "data": bytes_data}]

# Generate Gemini response
def get_gemini_response(image_parts, system_prompt, user_prompt=None):
    model = genai.GenerativeModel('gemini-1.5-flash')
    inputs = [system_prompt, image_parts[0]]
    if user_prompt:
        inputs.append(user_prompt)
    response = model.generate_content(inputs)
    return response.text

# Store image for reuse across buttons
if uploaded_file:
    image_data = input_image_setup(uploaded_file)

    if analyze_button:
        st.subheader("🧾 Invoice Summary")
        summary = get_gemini_response(image_data, input_prompt)
        st.write(summary)
        # Try parsing summary into key-value pairs
        parsed_summary = {}
        lines = summary.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                parsed_summary[key.strip()] = value.strip()

        # Save to CSV (even if parsing fails)
        if parsed_summary:
            df_summary = pd.DataFrame([parsed_summary])
        else:
            df_summary = pd.DataFrame([{"Summary": summary}])

        summary_csv_path = "invoice_summary.csv"
        df_summary.to_csv(summary_csv_path, index=False)

        with open(summary_csv_path, "rb") as f:
            st.download_button("📥 Download Summary as CSV", f, file_name="invoice_summary.csv", mime="text/csv")

    if ask_button and user_prompt:
        st.subheader("❓ Answer to Your Question")
        answer = get_gemini_response(image_data, input_prompt, user_prompt)
        st.write(answer)

        # Save Q&A to CSV
        structured_data = {"User Prompt": user_prompt, "Response": answer}
        df = pd.DataFrame([structured_data])
        csv_path = "invoice_response.csv"
        df.to_csv(csv_path, index=False)

        with open(csv_path, "rb") as f:
            st.download_button("📥 Download Q&A as CSV", f, file_name="invoice_response.csv", mime="text/csv")

    elif ask_button and not user_prompt:
        st.warning("⚠️ Please enter a question before clicking 'Ask Your Question'.")
