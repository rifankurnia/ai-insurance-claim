from datetime import datetime
import difflib
import re

# Map specific service keywords to broader policy categories
SERVICE_CATEGORY_MAP = {
    "tes darah": ["laboratorium", "pemeriksaan laboratorium", "laboratorium dan radiologi"],
    "cbc": ["laboratorium", "pemeriksaan laboratorium"],
    "rontgen": ["radiologi", "pemeriksaan radiologi", "laboratorium dan radiologi"],
    "x-ray": ["radiologi", "laboratorium dan radiologi"],
    "obat": ["obat", "resep dokter"],
    "paracetamol": ["obat", "resep dokter"],
    "konsultasi": ["konsultasi dokter umum dan spesialis"],
    "resep obat": ["obat", "resep dokter"],
    "resep": ["obat", "resep dokter"],
    # Add more mappings as needed
}

# Keywords to filter out non-service lines (removed 'biaya fasilitas')
NON_SERVICE_KEYWORDS = [
    "total tagihan", "jumlah dibayar", "pajak", "total", "metode pembayaran", "tanggal pembayaran"
]

def format_rupiah(amount):
    try:
        amount = float(amount)
        return f"Rp {int(amount):,}".replace(",", ".")
    except Exception:
        return f"Rp {amount}"

def clean_service_desc(desc):
    # Remove dates, numbers, and punctuation except dash, then lowercase and strip
    desc = re.sub(r'\d{4}-\d{2}-\d{2}', '', desc)  # Remove dates
    desc = re.sub(r'\d+', '', desc)  # Remove numbers
    desc = re.sub(r'[^\w\s-]', '', desc)  # Remove punctuation except dash
    desc = desc.replace('-', ' ')  # Replace dashes with space
    desc = re.sub(r'\s+', ' ', desc)  # Collapse multiple spaces
    return desc.strip().lower()

def is_non_service_line(desc):
    desc_clean = desc.lower()
    return any(kw in desc_clean for kw in NON_SERVICE_KEYWORDS)

def process_claim(receipt_data, policy_data):
    # Helper to parse dates
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except Exception:
                return None

    # Policy validity
    date_of_service = parse_date(receipt_data.get("date_of_service", ""))
    effective_date = parse_date(policy_data.get("effective_date", ""))
    expiration_date = parse_date(policy_data.get("expiration_date", ""))
    policy_active = (
        date_of_service and effective_date and expiration_date and
        effective_date <= date_of_service <= expiration_date
    )

    deductible = policy_data.get("deductible_amount") or 0.0
    copay_pct = policy_data.get("copay_percentage") or 0.0
    copay_fixed = policy_data.get("copay_fixed_amount") or 0.0
    annual_limit = policy_data.get("annual_limit") or float('inf')
    covered_services = [clean_service_desc(s) for s in policy_data.get("covered_services", [])]
    excluded_services = [clean_service_desc(s) for s in policy_data.get("excluded_services", [])]
    preauth_services = [clean_service_desc(s) for s in policy_data.get("pre_authorization_required_for", [])]

    claim_breakdown = []
    total_covered = 0.0
    overall_eligibility = "Fully Eligible"
    explanations = []

    def fuzzy_match(desc, service_list, threshold=0.6):
        desc_clean = clean_service_desc(desc)
        for s in service_list:
            s_clean = clean_service_desc(str(s))
            # Direct substring match
            if desc_clean in s_clean or s_clean in desc_clean:
                return True
            # Fuzzy ratio match
            if difflib.SequenceMatcher(None, desc_clean, s_clean).ratio() > threshold:
                return True
        return False

    for service in receipt_data.get("services_rendered", []):
        desc = clean_service_desc(service.get("description", "") or str(service))
        cost = service.get("cost", 0)  # Ensure cost is defined for each service
        if not desc or is_non_service_line(desc):
            continue
        service['service_description'] = desc  # Only the cleaned service name

        # Direct fuzzy match to covered services (lower threshold, add substring check)
        best_match = 0
        substring_match = False
        for covered in covered_services:
            score = difflib.SequenceMatcher(None, desc, covered).ratio()
            if score > best_match:
                best_match = score
            if desc in covered or covered in desc:
                substring_match = True
        # If direct match is strong enough, or substring match, consider covered
        if best_match > 0.4 or substring_match:
            eligibility_status = "Covered"
            reasoning = "Service directly matched covered list."
        else:
            # Try category mapping (improved logic)
            mapped = False
            for keyword, categories in SERVICE_CATEGORY_MAP.items():
                if keyword in desc or desc in keyword:
                    for cat in categories:
                        for covered in covered_services:
                            score = difflib.SequenceMatcher(None, cat, covered).ratio()
                            if score > 0.6:
                                eligibility_status = "Covered (by category)"
                                reasoning = f"Service '{service.get('description', '')}' mapped to category '{cat}' which is covered."
                                mapped = True
                                break
                        if mapped:
                            break
                    if mapped:
                        break
            if not mapped:
                # Exclusion check
                excluded = False
                for excl in excluded_services:
                    if excl and excl in desc:
                        eligibility_status = "Not Covered - Excluded"
                        reasoning = f"Service '{desc}' is explicitly excluded in the policy."
                        excluded = True
                        break
                if not excluded:
                    # Not covered
                    eligibility_status = "Not Covered - Not Listed"
                    reasoning = f"Service '{desc}' is not listed as covered in the policy."

        # Pre-authorization check
        pre_auth = fuzzy_match(desc, preauth_services)
        if pre_auth:
            eligibility_status = "Not Covered - Pre-auth Missing"
            reasoning += f" Service '{desc}' requires pre-authorization."

        # Apply deductible
        if deductible > 0:
            if cost <= deductible:
                eligibility_status = "Not Covered - Deductible"
                reasoning += f" Cost ({format_rupiah(cost)}) does not exceed deductible ({format_rupiah(deductible)})."
                deductible -= cost
                covered_amount = 0.0
                overall_eligibility = "Partially Eligible"
            else:
                cost_after_deductible = cost - deductible
                deductible = 0
                # Apply copay
                if copay_pct > 0:
                    covered_amount = cost_after_deductible * (1 - copay_pct)
                    reasoning += f" Deductible applied. Copay of {copay_pct*100:.0f}% applied."
                elif copay_fixed > 0:
                    covered_amount = max(0, cost_after_deductible - copay_fixed)
                    reasoning += f" Deductible applied. Fixed copay of {format_rupiah(copay_fixed)} applied."
                else:
                    covered_amount = cost_after_deductible
                    reasoning += " Deductible applied. No copay."
        else:
            # No deductible
            if copay_pct > 0:
                covered_amount = cost * (1 - copay_pct)
                reasoning += f" Copay of {copay_pct*100:.0f}% applied."
            elif copay_fixed > 0:
                covered_amount = max(0, cost - copay_fixed)
                reasoning += f" Fixed copay of {format_rupiah(copay_fixed)} applied."
            else:
                covered_amount = cost
                reasoning += " No deductible or copay."

        # Apply annual limit
        if total_covered + covered_amount > annual_limit:
            covered_amount = max(0, annual_limit - total_covered)
            eligibility_status = "Not Covered - Annual Limit"
            reasoning += f" Annual limit of {format_rupiah(annual_limit)} reached."
            overall_eligibility = "Partially Eligible"
        total_covered += covered_amount
        claim_breakdown.append({
            "service_description": desc,
            "billed_cost": cost,
            "eligibility_status": eligibility_status,
            "covered_amount": covered_amount,
            "reasoning": reasoning
        })
        explanations.append(reasoning)

    estimated_payout = sum(s["covered_amount"] for s in claim_breakdown)
    if all(s["eligibility_status"] == "Not Covered - Policy Inactive" for s in claim_breakdown):
        overall_eligibility = "Not Eligible"
    elif any(s["eligibility_status"].startswith("Not Covered") for s in claim_breakdown):
        overall_eligibility = "Partially Eligible"
    else:
        overall_eligibility = "Fully Eligible"

    overall_reasoning = "\n".join(explanations)
    return {
        "overall_eligibility": overall_eligibility,
        "estimated_payout": estimated_payout,
        "claim_breakdown": claim_breakdown,
        "overall_reasoning": overall_reasoning
    } 