"""
Math functions for mortgage calculations.
These are pure Python functions that will be called via function calling (tools).
No LLM should perform these calculations directly.
"""

import math
from typing import Dict, Any
from app.tracing import trace_tool_execution


@trace_tool_execution("calculate_emi")
def calculate_emi(loan_amount: float, interest_rate: float, tenure_years: int) -> Dict[str, Any]:
    """
    Calculate Equated Monthly Installment (EMI).
    
    Formula: EMI = P × r × (1+r)^n / ((1+r)^n - 1)
    Where:
    - P = Loan amount
    - r = Monthly interest rate (annual/12)
    - n = Number of months
    
    Args:
        loan_amount: Principal loan amount in AED
        interest_rate: Annual interest rate (e.g., 4.5 for 4.5%)
        tenure_years: Loan tenure in years (max 25)
    
    Returns:
        Dictionary with EMI, total amount, total interest
    """
    if loan_amount <= 0:
        return {"error": "Loan amount must be positive"}
    
    if tenure_years <= 0 or tenure_years > 25:
        return {"error": "Tenure must be between 1 and 25 years"}
    
    if interest_rate < 0:
        return {"error": "Interest rate cannot be negative"}
    
    # Convert to monthly
    monthly_rate = (interest_rate / 100) / 12
    num_months = tenure_years * 12
    
    # Calculate EMI
    if monthly_rate == 0:
        emi = loan_amount / num_months
    else:
        emi = loan_amount * monthly_rate * ((1 + monthly_rate) ** num_months) / (((1 + monthly_rate) ** num_months) - 1)
    
    total_amount = emi * num_months
    total_interest = total_amount - loan_amount
    
    return {
        "emi": round(emi, 2),
        "total_amount": round(total_amount, 2),
        "total_interest": round(total_interest, 2),
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "tenure_years": tenure_years,
        "tenure_months": num_months
    }


@trace_tool_execution("check_ltv")
def check_ltv(property_price: float, down_payment: float) -> Dict[str, Any]:
    """
    Check Loan-to-Value (LTV) ratio and validate 80% maximum rule for expats.
    
    Args:
        property_price: Total property price in AED
        down_payment: Down payment amount in AED
    
    Returns:
        Dictionary with LTV, max loanable amount, validation result
    """
    if property_price <= 0:
        return {"error": "Property price must be positive"}
    
    if down_payment < 0:
        return {"error": "Down payment cannot be negative"}
    
    if down_payment >= property_price:
        return {"error": "Down payment cannot exceed property price"}
    
    loan_amount = property_price - down_payment
    ltv_ratio = (loan_amount / property_price) * 100
    
    # Maximum LTV for expats is 80%
    max_ltv = 80
    max_loanable = property_price * (max_ltv / 100)
    min_down_payment_required = property_price - max_loanable
    
    is_valid = ltv_ratio <= max_ltv
    
    return {
        "ltv_ratio": round(ltv_ratio, 2),
        "loan_amount": round(loan_amount, 2),
        "max_loanable": round(max_loanable, 2),
        "min_down_payment_required": round(min_down_payment_required, 2),
        "is_valid": is_valid,
        "property_price": property_price,
        "down_payment": down_payment,
        "message": "Valid" if is_valid else f"LTV exceeds {max_ltv}%. Minimum down payment required: {min_down_payment_required:,.0f} AED"
    }


@trace_tool_execution("calculate_upfront_costs")
def calculate_upfront_costs(property_price: float) -> Dict[str, Any]:
    """
    Calculate upfront costs for property purchase in UAE.
    
    Breakdown:
    - Transfer Fee: 4% of property price
    - Agency Fee: 2% of property price
    - Miscellaneous: 1% of property price
    - Total: 7% of property price
    
    Args:
        property_price: Total property price in AED
    
    Returns:
        Dictionary with cost breakdown
    """
    if property_price <= 0:
        return {"error": "Property price must be positive"}
    
    transfer_fee = property_price * 0.04  # 4%
    agency_fee = property_price * 0.02     # 2%
    misc_fee = property_price * 0.01       # 1%
    total_upfront = transfer_fee + agency_fee + misc_fee
    
    return {
        "property_price": property_price,
        "transfer_fee": round(transfer_fee, 2),
        "agency_fee": round(agency_fee, 2),
        "misc_fee": round(misc_fee, 2),
        "total_upfront_costs": round(total_upfront, 2),
        "percentage": 7.0,
        "total_with_costs": round(property_price + total_upfront, 2)
    }


@trace_tool_execution("buy_vs_rent_analysis")
def buy_vs_rent_analysis(
    monthly_rent: float,
    property_price: float,
    stay_years: int,
    income: float,
    down_payment: float,
    interest_rate: float = 4.5
) -> Dict[str, Any]:
    """
    Analyze whether buying or renting is better based on user's situation.
    
    Logic:
    - If stay < 3 years: Advise Renting (transaction fees kill profit)
    - If stay > 5 years: Advise Buying (equity buildup beats rent)
    - Compare: Monthly Rent vs (Monthly Mortgage Interest + Maintenance)
    
    Args:
        monthly_rent: Current monthly rent in AED
        property_price: Property price in AED
        stay_years: How long user plans to stay (years)
        income: Monthly income in AED
        down_payment: Available down payment in AED
        interest_rate: Annual interest rate (default 4.5%)
    
    Returns:
        Dictionary with analysis and recommendation
    """
    if monthly_rent <= 0:
        return {"error": "Monthly rent must be positive"}
    
    if property_price <= 0:
        return {"error": "Property price must be positive"}
    
    if stay_years <= 0:
        return {"error": "Stay duration must be positive"}
    
    if income <= 0:
        return {"error": "Income must be positive"}
    
    # Calculate loan details
    loan_amount = property_price - down_payment
    ltv_check = check_ltv(property_price, down_payment)
    
    if not ltv_check.get("is_valid", False):
        return {
            "error": ltv_check.get("message", "Invalid LTV ratio"),
            "ltv_details": ltv_check
        }
    
    # Calculate EMI
    emi_result = calculate_emi(loan_amount, interest_rate, 25)  # Max tenure
    if "error" in emi_result:
        return emi_result
    
    emi = emi_result["emi"]
    
    # Calculate monthly interest portion (approximation for first year)
    monthly_interest = (loan_amount * interest_rate / 100) / 12
    maintenance_estimate = property_price * 0.001 / 12  # 0.1% of property value per year, monthly
    
    monthly_ownership_cost = monthly_interest + maintenance_estimate
    
    # Calculate upfront costs
    upfront_costs = calculate_upfront_costs(property_price)
    total_upfront = upfront_costs["total_upfront_costs"]
    
    # Decision logic
    recommendation = "RENT"
    reasoning = []
    
    if stay_years < 3:
        recommendation = "RENT"
        reasoning.append(f"Planning to stay less than 3 years. Transaction costs ({total_upfront:,.0f} AED) would outweigh benefits.")
    elif stay_years > 5:
        recommendation = "BUY"
        reasoning.append(f"Planning to stay more than 5 years. Equity buildup and long-term savings favor buying.")
    else:
        # 3-5 years: Compare costs
        if monthly_ownership_cost < monthly_rent:
            recommendation = "BUY"
            reasoning.append(f"Monthly ownership cost ({monthly_ownership_cost:,.0f} AED) is less than rent ({monthly_rent:,.0f} AED).")
        else:
            recommendation = "RENT"
            reasoning.append(f"Monthly rent ({monthly_rent:,.0f} AED) is less than ownership cost ({monthly_ownership_cost:,.0f} AED) for now.")
    
    # Affordability check
    affordability_ratio = (emi / income) * 100
    is_affordable = affordability_ratio <= 30  # General rule: EMI should be max 30% of income
    
    if not is_affordable:
        recommendation = "RENT"  # Override if not affordable
        reasoning.append(f"EMI ({emi:,.0f} AED) is {affordability_ratio:.1f}% of income. Recommended max is 30%.")
    
    return {
        "recommendation": recommendation,
        "reasoning": reasoning,
        "monthly_rent": monthly_rent,
        "monthly_ownership_cost": round(monthly_ownership_cost, 2),
        "monthly_interest": round(monthly_interest, 2),
        "maintenance_estimate": round(maintenance_estimate, 2),
        "emi": emi,
        "affordability_ratio": round(affordability_ratio, 2),
        "is_affordable": is_affordable,
        "stay_years": stay_years,
        "upfront_costs": total_upfront,
        "ltv_details": ltv_check,
        "emi_details": emi_result
    }
