import json
from pathlib import Path

import pandas as pd
import streamlit as st
 

# ---------- Page Setup ----------
st.set_page_config(
    page_title="Green Steps — Carbon Footprint Calculator",
    page_icon="🌱",
    layout="centered",
)

# ---------- Load Factors ----------
FACTOR_FILE = Path(__file__).parent / "factors.json"
if not FACTOR_FILE.exists():
    st.error("factors.json not found. Please make sure it exists in the project folder.")
    st.stop()

with open(FACTOR_FILE, "r", encoding="utf-8") as f:
    FACTORS = json.load(f)

# ---------- Branding ----------
logo_path = Path(__file__).parent / "assets" / "Logo.png"
col1, col2 = st.columns([1,3])
with col1:
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
with col2:
    st.title("Green Steps — Carbon Footprint Calculator")
    st.caption("Quickly estimate your carbon footprint and discover reduction ideas. Defaults are illustrative; adjust factors for your region.")

st.divider()

# ---------- Sidebar Inputs ----------
st.sidebar.header("Inputs")
period = st.sidebar.selectbox("Time period", ["per day", "per week", "per month", "per year"], index=2)

# helper to get days in period
DAYS = {
    "per day": 1,
    "per week": 7,
    "per month": 30,
    "per year": 365,
}
period_days = DAYS[period]

st.sidebar.subheader("Home Energy")
elec_kwh = st.sidebar.number_input("Electricity usage (kWh in this period)", min_value=0.0, value=120.0, step=1.0)
lpg_cyl = st.sidebar.number_input("LPG cylinders (14.2 kg) used in this period", min_value=0.0, value=0.25, step=0.05)

st.sidebar.subheader("Travel (distance in km for this period)")
bike_km = st.sidebar.number_input("Two-wheeler (bike/scooter)", min_value=0.0, value=50.0, step=1.0)
car_type = st.sidebar.selectbox("Car fuel type", ["petrol", "diesel"], index=0)
car_km = st.sidebar.number_input("Car (any car of selected fuel type)", min_value=0.0, value=30.0, step=1.0)
bus_km = st.sidebar.number_input("Bus", min_value=0.0, value=20.0, step=1.0)
train_km = st.sidebar.number_input("Train", min_value=0.0, value=40.0, step=1.0)
flight_km = st.sidebar.number_input("Flights (economy)", min_value=0.0, value=0.0, step=10.0)

st.sidebar.subheader("Food")
diet = st.sidebar.selectbox("Diet profile", ["meat_heavy", "mixed", "vegetarian", "vegan"], index=1)

st.sidebar.caption("You can change default emission factors in factors.json.")

# ---------- Calculator ----------

def calc_emissions():
    ef = FACTORS
    data = {}

    # Home energy
    data["Electricity"] = elec_kwh * ef["electricity_kwh"]
    data["LPG (cylinders)"] = lpg_cyl * ef["lpg_cylinder_14_2kg"]

    # Travel
    data["Bike / Scooter"] = bike_km * ef["bike_km"]
    car_factor = ef["car_petrol_km"] if car_type == "petrol" else ef["car_diesel_km"]
    data["Car"] = car_km * car_factor
    data["Bus"] = bus_km * ef["bus_km"]
    data["Train"] = train_km * ef["train_km"]
    data["Flights"] = flight_km * ef["flight_km"]

    # Food — diet factor is per day; scale by number of days in the chosen period
    diet_factor_per_day = ef["diet_profiles"][diet]
    data["Food (diet)"] = diet_factor_per_day * DAYS[period]

    df = pd.DataFrame({"Category": list(data.keys()), "kg CO2e": list(data.values())})
    df = df.sort_values("kg CO2e", ascending=False).reset_index(drop=True)
    total = float(df["kg CO2e"].sum())
    return df, total


df, total = calc_emissions()

# ---------- Results ----------
st.subheader("Your results")
st.metric("Total emissions (kg CO₂e) " + period, f"{total:,.2f}")

st.bar_chart(df.set_index("Category"))

with st.expander("Breakdown (table)"):
    st.dataframe(df, use_container_width=True)

# ---------- Tips ----------
st.subheader("Suggestions to reduce")

biggest = df.iloc[0]
msg = ""
if biggest["Category"] == "Electricity":
    msg = "Switch to LED bulbs, turn off idle appliances, and consider efficient fans/AC settings."
elif biggest["Category"] == "LPG (cylinders)":
    msg = "Use pressure cooker more often, keep burners clean, and ensure vessels match flame size."
elif biggest["Category"] == "Car":
    msg = "Combine trips, prefer carpooling, maintain tyre pressure, and avoid harsh acceleration."
elif biggest["Category"] == "Bike / Scooter":
    msg = "Regular servicing, correct tyre pressure, and smoother riding reduce fuel use."
elif biggest["Category"] == "Bus":
    msg = "Public transport is already efficient; try to shift car/bike trips to bus when practical."
elif biggest["Category"] == "Train":
    msg = "Train is one of the lowest-carbon modes; prefer train over short flights when possible."
elif biggest["Category"] == "Flights":
    msg = "Combine trips, choose economy class, and prefer train/bus for short distances."
elif biggest["Category"] == "Food (diet)":
    msg = "Shift some meals toward vegetarian/plant-forward options and reduce food waste."

st.write(f"**Biggest category:** {biggest['Category']} — {biggest['kg CO2e']:.2f} kg CO₂e. {msg}")

# ---------- Export ----------
@st.cache_data
def to_csv(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(index=False).encode("utf-8")

csv = to_csv(df)
st.download_button(
    label="Download breakdown as CSV",
    data=csv,
    file_name="green_steps_footprint_breakdown.csv",
    mime="text/csv",
)

st.caption(
    "Note: This is a quick-estimate tool. Factors are approximate and for education/awareness. Edit factors.json for your region."
)