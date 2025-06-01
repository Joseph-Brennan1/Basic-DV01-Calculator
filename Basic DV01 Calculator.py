# Please note that this was run in a virtual environment on my pc so do install the relevant packages beforehand in a virtual environment: 
# pip install numpy pandas matplotlib scipy
# This is a basic yield curve construction code. It uses made up yields, a 1bp parallel shift in the yield curve.
# In the future I hope to add floating leg valuation and connect some code to BBG to get real time data.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Made up market data for Treasury yields
bond_data = pd.DataFrame({
    'Tenor (Years)': [0.5, 1, 2, 3, 5, 7, 10],
    'Yield (%)': [5.0, 5.1, 5.2, 5.3, 5.5, 5.6, 5.7]  # mock yields
})

# Converting the zero-coupon rates (simplified assumption: same as par yields)
bond_data['Zero Rate'] = bond_data['Yield (%)'] / 100

# Interpolating the zero curve here.
tenors = bond_data['Tenor (Years)']
zero_rates = bond_data['Zero Rate']
interp_curve = interp1d(tenors, zero_rates, kind='cubic', fill_value="extrapolate")

# Defining the bond price and DV01

def bond_price(face, coupon_rate, maturity, zero_curve_func, freq=1):
    times = np.arange(1, maturity * freq + 1) / freq
    cashflows = np.full_like(times, face * coupon_rate / freq)
    cashflows[-1] += face  # Add principal at maturity
    discounts = np.exp(-zero_curve_func(times) * times)
    return np.sum(cashflows * discounts)

def bond_dv01(face, coupon_rate, maturity, zero_curve_func, freq=1):
    base_price = bond_price(face, coupon_rate, maturity, zero_curve_func, freq)
    
    def bumped_curve(t):
        return zero_curve_func(t) + 0.0001  # +1bp bump
    
    bumped_price = bond_price(face, coupon_rate, maturity, bumped_curve, freq)
    dv01 = base_price - bumped_price
    return dv01

# Basic Swap Fixed Leg DV01

def swap_fixed_leg_dv01(notional, fixed_rate, maturity, zero_curve_func, freq=1):
    times = np.arange(1, maturity * freq + 1) / freq
    cashflows = np.full_like(times, notional * fixed_rate / freq)
    discounts = np.exp(-zero_curve_func(times) * times)
    pv = np.sum(cashflows * discounts)
    
    def bumped_curve(t):
        return zero_curve_func(t) + 0.0001
    
    discounts_bumped = np.exp(-bumped_curve(times) * times)
    pv_bumped = np.sum(cashflows * discounts_bumped)
    
    dv01 = pv - pv_bumped
    return dv01

# Here is a made up example

face_value = 1_000_000
bond_coupon = 0.05
swap_fixed_rate = 0.05
maturity_years = 5

bond_dv01_val = bond_dv01(face=face_value, coupon_rate=bond_coupon, maturity=maturity_years, zero_curve_func=interp_curve)
swap_dv01_val = swap_fixed_leg_dv01(notional=face_value, fixed_rate=swap_fixed_rate, maturity=maturity_years, zero_curve_func=interp_curve)

# Print results
print("DV01 Results:")
print(f"5Y Fixed Bond DV01: ${bond_dv01_val:.2f}")
print(f"5Y IRS Fixed Leg DV01: ${swap_dv01_val:.2f}")

# Plotting the Yield Curve 

x_vals = np.linspace(0.5, 10, 100)
y_vals = interp_curve(x_vals) * 100

plt.figure(figsize=(8, 4))
plt.plot(x_vals, y_vals)
plt.title("Zero-Coupon Yield Curve")
plt.xlabel("Tenor (Years)")
plt.ylabel("Yield (%)")
plt.grid(True)
plt.tight_layout()
plt.show()
# Result should be a plotted zero-coupon yield curve, a 5 year fixed bond DV01 and a 5 Year IRS Fixed Leg DV01