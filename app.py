import streamlit as st
import pandas as pd
from pathlib import Path

# ---------- Helpers ----------
def find_col(df, keys):
    for c in df.columns:
        for k in keys:
            if k.lower() in c.lower():
                return c
    raise ValueError(f"Missing column for {keys}. Found: {df.columns.tolist()}")

def parse_list(x):
    return [i.strip().lower() for i in str(x).split(",") if i.strip()]

def skills_ok(p, req): return set(parse_list(req)).issubset(set(parse_list(p)))
def certs_ok(p, req): return set(parse_list(req)).issubset(set(parse_list(p))) if str(req).lower() not in ["nan", "none"] else True
def same_loc(a, b): return str(a).strip().lower() == str(b).strip().lower()
def is_rain_risk(drone_rating, weather): 
    return str(weather).lower() == "rainy" and "ip" not in str(drone_rating).lower()

def cost_calc(rate, start, end):
    try:
        days = (pd.to_datetime(end) - pd.to_datetime(start)).days + 1
        return int(float(rate)) * max(days, 1)
    except:
        return None

# ---------- Load ----------
BASE = Path(__file__).resolve().parent
pilots = pd.read_csv(BASE/"pilot_roster.csv")
drones = pd.read_csv(BASE/"drone_fleet.csv")
missions = pd.read_csv(BASE/"missions.csv")

# ---------- Columns ----------
mid = find_col(missions, ["mission", "project", "id"])
mloc = find_col(missions, ["location", "city"])
mweather = find_col(missions, ["weather"])
mskills = find_col(missions, ["skill"])
mcerts = find_col(missions, ["cert"])
mbudget = find_col(missions, ["budget"])
mstart = find_col(missions, ["start"])
mend = find_col(missions, ["end"])
mprio = find_col(missions, ["priority"])

pname = find_col(pilots, ["name"])
pskills = find_col(pilots, ["skill"])
pcerts = find_col(pilots, ["cert"])
ploc = find_col(pilots, ["location"])
pstatus = find_col(pilots, ["status"])
prate = find_col(pilots, ["daily", "rate", "cost"])

did = find_col(drones, ["drone", "id"])
dweather = find_col(drones, ["weather", "ip"])
dstatus = find_col(drones, ["status"])
dloc = find_col(drones, ["location"])
dmaint = find_col(drones, ["maint", "due"]) if any("maint" in c.lower() for c in drones.columns) else None

# ---------- State ----------
if "audit" not in st.session_state:
    st.session_state.audit = []

# ---------- UI ----------
st.set_page_config(layout="wide")
st.title("Operations Dashboard")

mission_id = st.selectbox("Mission", missions[mid].astype(str))
m = missions[missions[mid].astype(str) == str(mission_id)].iloc[0]

# ---------- Blockers & Risks ----------
blockers, risks = [], []

for _, p in pilots.iterrows():
    if str(p[pstatus]).lower() != "available":
        blockers.append(f"Pilot unavailable: {p[pname]}")
for _, d in drones.iterrows():
    if str(d[dstatus]).lower() != "available":
        blockers.append(f"Drone unavailable: {d[did]}")

if str(m[mweather]).lower() == "rainy":
    risks.append("Rain expected: only IP-rated drones allowed")

st.subheader("Blocking issues")
if blockers:
    for b in blockers: st.error(b)
else:
    st.success("No blocking issues detected")

st.subheader("Risk flags")
for r in risks: st.warning(r)
if not risks: st.info("No risk flags detected")

# ---------- Candidates ----------
candidates = []
for _, p in pilots.iterrows():
    if str(p[pstatus]).lower() != "available": continue
    if not skills_ok(p[pskills], m[mskills]): continue
    if not certs_ok(p[pcerts], m[mcerts]): continue
    if not same_loc(p[ploc], m[mloc]): continue

    for _, d in drones.iterrows():
        if str(d[dstatus]).lower() != "available": continue
        if not same_loc(d[dloc], m[mloc]): continue
        if is_rain_risk(d[dweather], m[mweather]): continue

        cost = cost_calc(p[prate], m[mstart], m[mend])
        if cost is None: continue
        over = float(cost) - float(m[mbudget]) if pd.notna(m[mbudget]) else 0
        risk_note = f"Over budget by ₹{int(over)}" if over > 0 else "Within budget"

        maint_risk = ""
        if dmaint and pd.notna(d[dmaint]):
            due = pd.to_datetime(d[dmaint])
            if due <= pd.Timestamp.now() + pd.Timedelta(days=2):
                maint_risk = "Maintenance due soon"

        candidates.append({
            "pilot": p[pname],
            "drone": d[did],
            "cost": cost,
            "risk": ", ".join([x for x in [risk_note, maint_risk] if x])
        })

st.subheader("Recommended assignment")
if candidates:
    rec = candidates[0]
    st.info(f"Primary: Pilot {rec['pilot']} • Drone {rec['drone']} • Est. cost ₹{rec['cost']}")
    if rec["risk"]: st.warning(f"Notes: {rec['risk']}")

    st.subheader("Alternatives")
    for alt in candidates[1:3]:
        st.write(f"- Pilot {alt['pilot']} • Drone {alt['drone']} • Est. cost ₹{alt['cost']} • Notes: {alt['risk']}")
else:
    st.warning("No suitable assignment found under current constraints.")

# ---------- Impact Preview ----------
st.subheader("Impact preview")
st.write("• Pilot status → Assigned")
st.write("• Drone status → Deployed")

override = st.checkbox("Override for high-priority mission")

# ---------- Proceed ----------
if st.button("Proceed with assignment"):
    if str(m[mprio]).lower() == "high" and override:
        st.warning("Override applied. One lower-priority mission will be delayed.")
        action = "Override assigned"
    elif candidates:
        action = "Assigned"
        st.success("Assignment confirmed.")
    else:
        st.error("Cannot proceed. No suitable resources.")
        action = "Failed"

    if candidates:
        st.session_state.audit.append({
            "time": str(pd.Timestamp.now()),
            "mission": m[mid],
            "pilot": rec["pilot"],
            "drone": rec["drone"],
            "action": action
        })

# ---------- Audit ----------
st.subheader("Assignment history")
if st.session_state.audit:
    st.dataframe(pd.DataFrame(st.session_state.audit), use_container_width=True)
else:
    st.info("No assignments yet.")

# ---------- Ops View ----------
st.subheader("Current data (read-only)")
c1, c2, c3 = st.columns(3)
with c1: st.dataframe(pilots, use_container_width=True)
with c2: st.dataframe(drones, use_container_width=True)
with c3: st.dataframe(missions, use_container_width=True)
