import os
import google.generativeai as genai
from dotenv import load_dotenv
import re
import json
# Remove openai import
# import openai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def gemini_llm(prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text

def llm_parse_receipt_text(receipt_text):
    """
    Use Gemini LLM to correct OCR errors and extract structured receipt data.
    """
    prompt = f"""
You are an expert in reading hospital receipts. The following is a raw OCR output from a hospital receipt, which may contain errors or misread words. Your job is to:
- Correct any OCR errors or misread words.
- Extract the following fields as JSON:
  - patient_name
  - date_of_service
  - hospital_name
  - total_bill_amount
  - services_rendered (list of objects with description, code, cost)
If a field is missing, use null or an empty list.

Raw OCR Text:
{receipt_text}

Return only the JSON object.
"""
    try:
        response = gemini_llm(prompt)
        return json.loads(response)
    except Exception as e:
        return None


def llm_parse_policy_text(policy_text):
    """
    Use Gemini LLM to correct OCR errors and extract structured policy data.
    """
    prompt = f"""
You are an expert in reading insurance policy documents. The following is a raw OCR output from an insurance policy, which may contain errors or misread words. Your job is to:
- Correct any OCR errors or misread words.
- Extract the following fields as JSON:
  - policy_holder_name
  - policy_number
  - effective_date
  - expiration_date
  - deductible_amount
  - copay_percentage
  - copay_fixed_amount
  - annual_limit
  - covered_services (list)
  - excluded_services (list)
  - pre_authorization_required_for (list)
If a field is missing, use null or an empty list.

Raw OCR Text:
{policy_text}

Return only the JSON object.
"""
    try:
        response = gemini_llm(prompt)
        return json.loads(response)
    except Exception as e:
        return None

def parse_receipt_text(receipt_text):
    llm_result = llm_parse_receipt_text(receipt_text)
    if llm_result:
        return llm_result
    # fallback to regex-based parsing
    patient_name = re.search(r"(?:Nama Pasien|Patient Name)\s*[:：]?\s*(.*)", receipt_text, re.IGNORECASE)
    date_of_service = re.search(r"(?:Tanggal Pelayanan|Date of Service)\s*[:：]?\s*(.*)", receipt_text, re.IGNORECASE)
    hospital_name = re.search(r"(?:Nama Rumah Sakit|Hospital Name)\s*[:：]?\s*(.*)", receipt_text, re.IGNORECASE)
    # Try to get total from 'Total Tagihan' or 'Jumlah Dibayar'
    total_bill_amount = re.search(r"(?:Total Tagihan|Jumlah Dibayar|Total Bill Amount)\s*[:：]?\s*Rp?\s*([\d\.,]+)", receipt_text, re.IGNORECASE)
    # Services rendered: extract lines under 'Layanan yang Diberikan'
    services = []
    layanan_section = re.search(r"Layanan yang Diberikan:(.*?)(?:Detail Pembayaran:|$)", receipt_text, re.IGNORECASE | re.DOTALL)
    if layanan_section:
        layanan_lines = layanan_section.group(1).splitlines()
        for line in layanan_lines:
            # Try to match: ServiceName [date] [qty] [unit price] [total]
            m = re.match(r"([\w\s\-()]+)\s+(\d{4}-\d{2}-\d{2})?\s*(\d+)?\s*([\d\.]+)?\s*([\d\.]+)?", line.strip())
            if m:
                desc = m.group(1).strip()
                date = m.group(2)
                qty = m.group(3)
                unit_price = m.group(4)
                total = m.group(5)
                # Use total if available, else unit price
                cost = None
                if total:
                    try:
                        cost = float(total.replace('.', '').replace(',', '.'))
                    except:
                        cost = None
                elif unit_price:
                    try:
                        cost = float(unit_price.replace('.', '').replace(',', '.'))
                    except:
                        cost = None
                if desc and cost:
                    services.append({
                        "service_description": desc,
                        "service_code": None,
                        "cost": cost
                    })
    return {
        "patient_name": patient_name.group(1).strip() if patient_name else None,
        "date_of_service": date_of_service.group(1).strip() if date_of_service else None,
        "hospital_name": hospital_name.group(1).strip() if hospital_name else None,
        "total_bill_amount": float(total_bill_amount.group(1).replace('.', '').replace(',', '.')) if total_bill_amount else None,
        "services_rendered": services
    }

def parse_policy_text(policy_text):
    llm_result = llm_parse_policy_text(policy_text)
    if llm_result:
        return llm_result
    # fallback to regex-based parsing
    policy_holder_name = re.search(r"(?:Nama Pemegang Polis|Policyholder|Policy Holder)\s*[:：]?\s*(.*)", policy_text, re.IGNORECASE)
    policy_number = re.search(r"(?:Nomor Polis|Policy Number)\s*[:：]?\s*(.*)", policy_text, re.IGNORECASE)
    effective_date = re.search(r"(?:Tanggal Efektif|Effective Date|Tanggal Mulai)\s*[:：]?\s*(.*)", policy_text, re.IGNORECASE)
    expiration_date = re.search(r"(?:Tanggal Kedaluwarsa|Expiry Date|Expiration Date|Tanggal Berakhir)\s*[:：]?\s*(.*)", policy_text, re.IGNORECASE)
    deductible_amount = re.search(r"(?:Jumlah Deductible|Batasan Tanggungan Sendiri|Deductible|Excess)\s*[:：]?\s*Rp?\s*([\d\.,]+)", policy_text, re.IGNORECASE)
    copay_percentage = re.search(r"(?:Persentase Co-pay|Copay Percentage)\s*[:：]?\s*(\d+)%", policy_text, re.IGNORECASE)
    copay_fixed_amount = re.search(r"(?:Jumlah Co-pay Tetap|Copay Fixed Amount)\s*[:：]?\s*Rp?\s*([\d\.,]+)", policy_text, re.IGNORECASE)
    annual_limit = re.search(r"(?:Batas Tahunan|Annual Limit|Insured Value|Sum Insured)\s*[:：]?\s*Rp?\s*([\d\.,]+)", policy_text, re.IGNORECASE)
    # Covered services
    covered_services = []
    covered_section = re.search(r"Layanan yang Ditanggung:(.*?)(?:Layanan yang Dikecualikan:|$)", policy_text, re.IGNORECASE | re.DOTALL)
    if covered_section:
        for line in covered_section.group(1).splitlines():
            line = line.strip("•*e- ").strip()
            if line:
                covered_services.append(line)
    # Excluded services
    excluded_services = []
    excluded_section = re.search(r"Layanan yang Dikecualikan:(.*?)(?:Layanan yang Membutuhkan Pra-Otorisasi:|$)", policy_text, re.IGNORECASE | re.DOTALL)
    if excluded_section:
        for line in excluded_section.group(1).splitlines():
            line = line.strip("•*e- ").strip()
            if line:
                excluded_services.append(line)
    # Pre-authorization required
    pre_auth = []
    preauth_section = re.search(r"Layanan yang Membutuhkan Pra-Otorisasi:(.*?)(?:\n\S|$)", policy_text, re.IGNORECASE | re.DOTALL)
    if preauth_section:
        for line in preauth_section.group(1).splitlines():
            line = line.strip("•*e- ").strip()
            if line:
                pre_auth.append(line)
    return {
        "policy_holder_name": policy_holder_name.group(1).strip() if policy_holder_name else None,
        "policy_number": policy_number.group(1).strip() if policy_number else None,
        "effective_date": effective_date.group(1).strip() if effective_date else None,
        "expiration_date": expiration_date.group(1).strip() if expiration_date else None,
        "deductible_amount": float(deductible_amount.group(1).replace('.', '').replace(',', '.')) if deductible_amount else None,
        "copay_percentage": float(copay_percentage.group(1)) if copay_percentage else None,
        "copay_fixed_amount": float(copay_fixed_amount.group(1).replace('.', '').replace(',', '.')) if copay_fixed_amount else None,
        "annual_limit": float(annual_limit.group(1).replace('.', '').replace(',', '.')) if annual_limit else None,
        "covered_services": covered_services,
        "excluded_services": excluded_services,
        "pre_authorization_required_for": pre_auth
    } 