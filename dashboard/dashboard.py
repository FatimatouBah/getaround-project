import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="GetAround - Delay Analysis", page_icon="🚗", layout="wide")

# ----------------------------------------------------------------
# Chargement et preparation des donnees
# ----------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("get_around_delay_analysis.xlsx")

    chained = df[df["previous_ended_rental_id"].notnull()].copy()
    prev_delays = df[["rental_id", "delay_at_checkout_in_minutes"]].rename(
        columns={"rental_id": "previous_ended_rental_id", "delay_at_checkout_in_minutes": "previous_delay"}
    )
    chained = chained.merge(prev_delays, on="previous_ended_rental_id", how="left")
    chained_known = chained.dropna(subset=["previous_delay"]).copy()
    chained_known["impact_minutes"] = chained_known["previous_delay"] - chained_known["time_delta_with_previous_rental_in_minutes"]
    chained_known["actually_late_for_checkin"] = chained_known["impact_minutes"] > 0

    return df, chained, chained_known


df, chained, chained_known = load_data()
TOTAL_RENTALS = len(df)

# ----------------------------------------------------------------
# Sidebar - parametres interactifs
# ----------------------------------------------------------------
st.sidebar.title("⚙️ Parametres de la feature")
scope = st.sidebar.radio("Perimetre (scope)", ["Toutes les voitures", "Connect uniquement"])
threshold = st.sidebar.slider("Delai minimum entre 2 locations (minutes)", 0, 720, 60, step=15)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Cette app simule l'effet d'un **delai minimum obligatoire** entre deux locations "
    "sur le meme vehicule, pour eviter qu'un conducteur arrive alors que la voiture "
    "n'a pas encore ete rendue."
)

subset = chained_known if scope == "Toutes les voitures" else chained_known[chained_known["checkin_type"] == "connect"]
total_problematic = subset["actually_late_for_checkin"].sum()

# ----------------------------------------------------------------
# Titre
# ----------------------------------------------------------------
st.title("🚗 GetAround — Analyse des retards & simulation du delai minimum")
st.markdown(
    "Aide a la decision pour le Product Manager : quel **seuil** et quel **perimetre** "
    "choisir pour le delai minimum entre deux locations ?"
)

# ----------------------------------------------------------------
# KPIs generaux
# ----------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Locations totales", f"{TOTAL_RENTALS:,}")
col2.metric("Locations enchainees", f"{len(chained):,}", f"{len(chained)/TOTAL_RENTALS*100:.1f}% du total")
col3.metric("Cas ou le prochain conducteur est reellement impacte", f"{chained_known['actually_late_for_checkin'].sum():,}",
            f"{chained_known['actually_late_for_checkin'].mean()*100:.1f}% des locations enchainees")
col4.metric("Retard median (quand impact)", f"{chained_known.loc[chained_known['actually_late_for_checkin'], 'impact_minutes'].median():.0f} min")

st.markdown("---")

# ----------------------------------------------------------------
# Impact du seuil choisi
# ----------------------------------------------------------------
affected = subset[subset["time_delta_with_previous_rental_in_minutes"] < threshold]
n_affected = len(affected)
pct_affected = n_affected / TOTAL_RENTALS * 100
n_solved = affected["actually_late_for_checkin"].sum()
pct_solved = n_solved / total_problematic * 100 if total_problematic > 0 else 0

st.header(f"📊 Avec un seuil de {threshold} minutes ({scope})")
c1, c2, c3 = st.columns(3)
c1.metric("Locations affectees par la feature", f"{n_affected:,}", f"{pct_affected:.2f}% du total des locations")
c2.metric("Cas problematiques resolus", f"{n_solved:,}", f"{pct_solved:.1f}% des cas problematiques")
c3.metric("Revenu potentiellement impacte", f"~{pct_affected:.2f}%",
          help="Approximation : on suppose que le prix moyen d'une location n'est pas correle au fait d'etre affecte par le seuil, donc la part de revenu impactee est proche de la part de locations affectees.")

st.markdown(
    f"Sur les **{int(total_problematic)}** cas ou le conducteur suivant a reellement ete impacte "
    f"({scope.lower()}), ce seuil en resout **{int(n_solved)}** ({pct_solved:.1f}%), "
    f"au prix de **{n_affected}** locations qui seraient bloquees/masquees dans les resultats de recherche "
    f"({pct_affected:.2f}% de l'ensemble des locations)."
)

st.markdown("---")

# ----------------------------------------------------------------
# Courbes trade-off : seuil vs. % affecte / % resolu, pour les 2 scopes
# ----------------------------------------------------------------
st.header("📈 Compromis seuil / impact, pour les deux perimetres")

thresholds_range = list(range(0, 721, 15))
rows = []
for scope_name, sub in [("Toutes les voitures", chained_known), ("Connect uniquement", chained_known[chained_known["checkin_type"] == "connect"])]:
    total_prob = sub["actually_late_for_checkin"].sum()
    for t in thresholds_range:
        aff = sub[sub["time_delta_with_previous_rental_in_minutes"] < t]
        rows.append({
            "threshold": t,
            "scope": scope_name,
            "pct_rentals_affected": len(aff) / TOTAL_RENTALS * 100,
            "pct_problematic_solved": (aff["actually_late_for_checkin"].sum() / total_prob * 100) if total_prob > 0 else 0,
        })
tradeoff_df = pd.DataFrame(rows)

col_a, col_b = st.columns(2)
with col_a:
    fig1 = px.line(tradeoff_df, x="threshold", y="pct_rentals_affected", color="scope",
                    title="% des locations affectees selon le seuil",
                    labels={"threshold": "Seuil (minutes)", "pct_rentals_affected": "% des locations affectees"})
    fig1.add_vline(x=threshold, line_dash="dash", line_color="red")
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    fig2 = px.line(tradeoff_df, x="threshold", y="pct_problematic_solved", color="scope",
                    title="% des cas problematiques resolus selon le seuil",
                    labels={"threshold": "Seuil (minutes)", "pct_problematic_solved": "% des cas problematiques resolus"})
    fig2.add_vline(x=threshold, line_dash="dash", line_color="red")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------------------
# Distributions
# ----------------------------------------------------------------
st.header("🔍 Distributions sous-jacentes")

col_c, col_d = st.columns(2)
with col_c:
    delay_clipped = df["delay_at_checkout_in_minutes"].clip(-120, 240)
    fig3 = px.histogram(delay_clipped.dropna(), nbins=60,
                         title="Distribution du retard au checkout (minutes, valeurs extremes ecretees)",
                         labels={"value": "Retard au checkout (min)"})
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    fig4 = px.histogram(chained_known, x="time_delta_with_previous_rental_in_minutes", nbins=48,
                         title="Delai reel entre deux locations enchainees (minutes)",
                         labels={"time_delta_with_previous_rental_in_minutes": "Delai entre 2 locations (min)"})
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.header("💡 Recommandation")
st.markdown("""
- Un seuil autour de **60 a 90 minutes**, applique **uniquement aux voitures Connect**, offre le meilleur compromis :
  il resout **70 a 80%** des cas problematiques identifies tout en n'affectant qu'environ **1%** de l'ensemble des locations (et donc du revenu).
- Etendre la regle a **toutes les voitures** resout davantage de cas au meme seuil, mais affecte aussi une part plus importante des locations (donc du revenu), les checkins papier/mobile etant moins previsibles que Connect en termes d'horaires.
- Un seuil au-dela de 240 minutes n'apporte plus que des gains marginaux (rendements decroissants), pour un cout croissant en locations bloquees.
""")
