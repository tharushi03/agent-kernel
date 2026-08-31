"""
Financing Calculator for Vehicle Purchases
Provides EMI calculation and financing analysis
"""

def calculate_emi(price, down_payment, annual_interest_rate, tenure_months):
    """
    Calculate monthly EMI (Equated Monthly Installment)
    
    Args:
        price: Total vehicle price
        down_payment: Initial down payment amount
        annual_interest_rate: Annual interest rate (percentage)
        tenure_months: Loan tenure in months
    
    Returns:
        Monthly EMI amount (rounded to 2 decimal places)
    """
    loan_amount = price - down_payment
    
    if loan_amount <= 0:
        return 0
    
    if annual_interest_rate == 0:
        return round(loan_amount / tenure_months, 2)
    
    monthly_rate = annual_interest_rate / 12 / 100
    
    # EMI formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
    numerator = loan_amount * monthly_rate * ((1 + monthly_rate) ** tenure_months)
    denominator = ((1 + monthly_rate) ** tenure_months) - 1
    
    emi = numerator / denominator
    return round(emi, 2)


def calculate_total_cost(price, down_payment, annual_interest_rate, tenure_months):
    """
    Calculate total cost including interest
    
    Args:
        price: Total vehicle price
        down_payment: Initial down payment amount
        annual_interest_rate: Annual interest rate (percentage)
        tenure_months: Loan tenure in months
    
    Returns:
        Dictionary with EMI, total interest, and total cost
    """
    emi = calculate_emi(price, down_payment, annual_interest_rate, tenure_months)
    total_paid = (emi * tenure_months) + down_payment
    total_interest = total_paid - price
    
    return {
        'monthly_emi': emi,
        'total_interest': round(total_interest, 2),
        'total_cost': round(total_paid, 2),
        'down_payment': down_payment,
        'loan_amount': price - down_payment,
        'tenure_months': tenure_months
    }


def format_financing_info(vehicle, down_payment_percent=20, interest_rate=5.0, tenure_months=60):
    """
    Format financing information for a vehicle
    
    Args:
        vehicle: Vehicle dictionary with price info
        down_payment_percent: Down payment percentage (default 20%)
        interest_rate: Annual interest rate (default 5%)
        tenure_months: Loan duration in months (default 60)
    
    Returns:
        Formatted string with financing details
    """
    price = vehicle.get('price', 0)
    down_payment = (price * down_payment_percent) / 100
    
    financing = calculate_total_cost(price, down_payment, interest_rate, tenure_months)
    
    result = f"""
💰 FINANCING OPTIONS FOR {vehicle['make']} {vehicle['model']} (${price:,})
{'=' * 55}
Down Payment ({down_payment_percent}%):     ${financing['down_payment']:,.2f}
Loan Amount:                  ${financing['loan_amount']:,.2f}

Monthly Payment (EMI):        ${financing['monthly_emi']:,.2f}
Tenure:                       {financing['tenure_months']} months ({financing['tenure_months']//12} years)
Annual Interest Rate:         {interest_rate}%

Total Interest to Pay:        ${financing['total_interest']:,.2f}
Total Cost (with interest):   ${financing['total_cost']:,.2f}
{'=' * 55}
"""
    return result


def compare_financing(vehicles, down_payment_percent=20, interest_rate=5.0, tenure_months=60):
    """
    Compare financing for multiple vehicles
    
    Args:
        vehicles: List of vehicle dictionaries
        down_payment_percent: Down payment percentage
        interest_rate: Annual interest rate
        tenure_months: Loan duration
    
    Returns:
        List of financing comparisons
    """
    comparisons = []
    for vehicle in vehicles:
        financing = calculate_total_cost(
            vehicle.get('price', 0),
            (vehicle.get('price', 0) * down_payment_percent) / 100,
            interest_rate,
            tenure_months
        )
        comparisons.append({
            'vehicle': vehicle,
            'financing': financing
        })
    
    return comparisons
