import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from utils.ocr_processor import extract_text_from_file
from utils.data_parser import parse_receipt_text, parse_policy_text
from utils.claim_processor import process_claim, format_rupiah
import tempfile

st.set_page_config(page_title="AI Insurance Claim Automation", layout="centered")
st.title("AI-Powered Insurance Claim Automation")

st.write("Upload a hospital receipt and an insurance policy document to analyze claim eligibility.")

receipt_file = st.file_uploader("Upload Hospital Receipt (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"], key="receipt")
policy_file = st.file_uploader("Upload Insurance Policy (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"], key="policy")

if st.button("Process Claim"):
    if not receipt_file or not policy_file:
        st.error("Please upload both documents.")
    else:
        with st.spinner("Processing documents..."):
            # Extract text directly from uploaded files
            receipt_text = extract_text_from_file(receipt_file)
            policy_text = extract_text_from_file(policy_file)
            st.subheader("Raw Receipt Text")
            st.text(receipt_text)
            st.subheader("Raw Policy Text")
            st.text(policy_text)
            # Parse structured data
            receipt_data = parse_receipt_text(receipt_text)
            policy_data = parse_policy_text(policy_text)

            # Show extracted data
            st.subheader("Extracted Hospital Receipt Data")
            st.json(receipt_data)
            st.subheader("Extracted Insurance Policy Data")
            st.json(policy_data)

            # Process claim
            claim_result = process_claim(receipt_data, policy_data)

            st.subheader("Claim Summary")
            st.write(f"**Eligibility:** {claim_result['overall_eligibility']}")
            st.write(f"**Estimated Payout:** {format_rupiah(claim_result['estimated_payout'])}")

            st.subheader("Claim Breakdown")
            st.dataframe(claim_result['claim_breakdown'])

            st.subheader("Detailed Reasoning")
            st.write(claim_result['overall_reasoning'])
            for service in claim_result['claim_breakdown']:
                with st.expander(f"Reasoning for {service['service_description']}"):
                    st.write(service['reasoning'])

    if st.button("New Claim"):
        st.experimental_rerun() 