"""
Tablero de monitoreo macroeconómico — Problema 6: "Las variables no se mueven solas"
IECNA Consultora · Ministerio de Economía

Ejecutar con:  streamlit run app.py
Los datos están en datos/indicadores.csv y datos/relaciones.csv (se pueden editar con Excel).
"""

import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Monitor macroeconómico · IECNA", page_icon="📊", layout="wide")

BASE = Path(__file__).parent
# Lenguaje visual fijo: lo nominal siempre en tono pálido, lo real siempre en tinta oscura.
C = dict(nominal="#A9BCD0", real="#1F3A5F", previo="#C9CED6", sube="#2E7D5B", baja="#B23A48", alerta="#C98A1B", gris="#8A94A6")
EJES = {"Ingresos y precios": "#7A5195", "Sector externo": "#2A9D8F", "Fiscal": "#C98A1B",
        "Monetario y financiero": "#3D6FB6", "Transversal": "#B23A48"}

st.markdown("""
<style>
.kpi {border-left: 6px solid var(--c); padding: .55rem .9rem; border-radius: 3px;
      background: rgba(127,127,127,.07); min-height: 128px; margin-bottom: .6rem}
.kpi .t {font-size: .82rem; opacity: .8}
.kpi .v {font-size: 1.55rem; font-weight: 700; line-height: 1.25}
.kpi .d {font-size: .85rem; margin-top: .1rem}
.kpi .f {font-size: .72rem; opacity: .6; margin-top: .25rem}
.lead {font-size: 1.05rem; max-width: 78ch; opacity: .9}
</style>""", unsafe_allow_html=True)


# ------------------------------------------------------------------ helpers
def fmt(v, dec=1, signo=False):
    """Formato argentino: 1.234,5"""
    if v is None or pd.isna(v):
        return "–"
    s = f"{v:+,.{dec}f}" if signo else f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def var(a, b):
    return (b / a - 1) * 100


@st.cache_data
def leer(origen) -> pd.DataFrame:
    df = pd.read_csv(origen, dtype={"brief": str})
    return df.fillna({"categoria": "", "medida": "", "nota": ""})


def kpi(col, titulo, valor, detalle, estado, fuente):
    color = {"bien": C["sube"], "mal": C["baja"], "alerta": C["alerta"]}.get(estado, C["gris"])
    col.markdown(f'<div class="kpi" style="--c:{color}"><div class="t">{titulo}</div>'
                 f'<div class="v">{valor}</div><div class="d">{detalle}</div>'
                 f'<div class="f">{fuente}</div></div>', unsafe_allow_html=True)


def estilo(fig, alto=360, leyenda=True):
    fig.update_layout(height=alto, margin=dict(t=50, b=10, l=10, r=10), showlegend=leyenda,
                      legend=dict(orientation="h", y=-0.15, title=None),
                      xaxis_title=None, yaxis_title=None, separators=",.")
    return fig


def mostrar(col, fig):
    col.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ------------------------------------------------------------------- datos
with st.sidebar:
    st.header("Datos")
    subido = st.file_uploader("Reemplazar indicadores.csv (opcional)", type="csv",
                              help="Usá el mismo formato de columnas que el archivo original.")
    st.caption("Por defecto se usan los datos de los Briefs 01 a 05 del equipo.")

def ruta(nombre):
    """Busca el CSV en la carpeta datos/ o, si no está, junto a app.py."""
    en_datos = BASE / "datos" / nombre
    return en_datos if en_datos.exists() else BASE / nombre


df = leer(subido if subido else ruta("indicadores.csv"))
rel = leer(ruta("relaciones.csv"))


def s(ind, cat=None, medida=None, eje=None):
    q = df[df["indicador"] == ind]
    if cat is not None:
        q = q[q["categoria"] == cat]
    if medida is not None:
        q = q[q["medida"] == medida]
    if eje is not None:
        q = q[q["eje"] == eje]
    return q


def v(ind, periodo, cat=None, medida=None):
    q = s(ind, cat, medida)
    q = q[q["periodo"] == periodo]
    return float(q["valor"].iloc[0]) if len(q) else float("nan")


# --------------------------------------------------------------- encabezado
st.title("Monitor macroeconómico")
st.markdown('<p class="lead">Las variables no se mueven solas. Este tablero reúne los indicadores '
            'centrales de los Briefs 01 a 05 y muestra cómo una misma inflación cambia la lectura '
            'de salarios, cuentas fiscales, competitividad y tasas.</p>', unsafe_allow_html=True)

tabs = st.tabs(["Resumen", "Ingresos y precios", "Sector externo", "Fiscal",
                "Monetario y financiero", "🔗 Relaciones", "Datos y notas"])

# ================================================================= RESUMEN
with tabs[0]:
    infl = v("Inflación interanual", "Ene-ago 2026")
    sr = s("Salario medio", medida="real").set_index("periodo")["valor"]
    tcrm, tcrm_h = v("ITCRM", "Ago 2026"), v("ITCRM", "Promedio histórico")
    deuda25, deuda26 = v("Deuda bruta total", "Ago 2025"), v("Deuda bruta total", "Ago 2026")
    tasa_real = v("Tasa de interés real (BADLAR)", "2026")

    st.subheader("Precios e ingresos")
    c = st.columns(4)
    kpi(c[0], "Inflación interanual", f"{fmt(infl)}%", "Hilo conductor de los cuatro briefs", "alerta", "Brief 04 · ene-ago 2026")
    kpi(c[1], "Salario real medio, interanual", f"{fmt(var(sr['2025-T1'], sr['2026-T1']), signo=True)}%",
        f"Último trimestre: {fmt(var(sr['2025-T4'], sr['2026-T1']), signo=True)}%", "alerta", "Brief 01-02 · 2025-T1 a 2026-T1")
    kpi(c[2], "Brecha salarial de género (media)", f"{fmt(v('Brecha salarial de género','2026-T1','Media'))}%",
        f"{fmt(v('Brecha salarial de género','2026-T1','Media') - v('Brecha salarial de género','2025-T1','Media'), signo=True)} pp en un año",
        "mal", "Brief 01-02 · 2026-T1")
    kpi(c[3], "Cobertura de la CBT", f"{fmt(v('Cobertura de la CBT (salario medio / CBT)','2026-T1'), 2)} canastas",
        "Pico de 2,62 en 2025-T4", "alerta", "Brief 01-02 · salario medio / CBT")

    st.subheader("Sector externo y monetario")
    c = st.columns(4)
    kpi(c[0], "Saldo comercial", f"USD {fmt(v('Saldo comercial','Ago 2026'), 0)} MM",
        f"1S 2026: USD {fmt(v('Saldo comercial','1S 2026'), 0)} MM", "bien", "Brief 03 · agosto 2026")
    kpi(c[1], "Tipo de cambio real multilateral", fmt(tcrm),
        f"{fmt(var(tcrm_h, tcrm), signo=True)}% vs promedio histórico", "mal", "Briefs 03 y 05 · agosto 2026")
    kpi(c[2], "Reservas brutas / netas", f"USD {fmt(v('Reservas internacionales brutas','Ago 2026'), 0)} MM",
        f"Netas ≈ USD {fmt(v('Reservas internacionales netas','Ago 2026'), 0)} MM", "alerta", "Brief 03 · agosto 2026")
    kpi(c[3], "Tasa de interés real (BADLAR)", f"{fmt(tasa_real)}%",
        "Nominal 22% TNA vs inflación 33%", "alerta", "Cálculo cruzado Briefs 04 y 05")

    st.subheader("Fiscal y crédito")
    c = st.columns(4)
    kpi(c[0], "Resultado primario (ene-ago)",
        f"{fmt(var(v('Resultado primario','Ene-ago 2025',medida='real'), v('Resultado primario','Ene-ago 2026',medida='real')), signo=True)}% real",
        f"{fmt(var(v('Resultado primario','Ene-ago 2025',medida='nominal'), v('Resultado primario','Ene-ago 2026',medida='nominal')), signo=True)}% nominal · sigue en superávit",
        "alerta", "Brief 04")
    kpi(c[1], "Deuda bruta Adm. Central", f"USD {fmt(deuda26 / 1000, 1)} mil MM",
        f"{fmt(var(deuda25, deuda26), signo=True)}% interanual", "mal", "Brief 04 · agosto 2026")
    kpi(c[2], "Crédito en dólares al sector privado", f"{fmt(v('Crédito en dólares al sector privado (var. interanual)','2026'), 0, True)}%",
        f"Stock USD {fmt(v('Crédito en dólares al sector privado (stock)','2026'), 0)} MM", "bien", "Brief 05")
    kpi(c[3], "Crédito en pesos / PIB", f"{fmt(v('Crédito en pesos al sector privado / PIB','2026'))}%",
        f"{fmt(v('Crédito en pesos al sector privado (var. interanual)','2026'), signo=True)}% real interanual", "mal", "Brief 05")

    st.caption("Colores: verde = evolución favorable, ámbar = señal mixta o a vigilar, rojo = deterioro.")

# ======================================================= INGRESOS Y PRECIOS
with tabs[1]:
    st.markdown("**Pregunta del Brief 01-02:** los ingresos aumentan, pero ¿la población está mejor?")
    T = ["2025-T1", "2025-T2", "2025-T3", "2025-T4", "2026-T1"]
    idx = pd.DataFrame({
        "Salario medio nominal": s("Salario medio", medida="nominal").set_index("periodo")["valor"],
        "IPC": s("IPC trimestral").set_index("periodo")["valor"],
        "Salario medio real": s("Salario medio", medida="real").set_index("periodo")["valor"],
    }).loc[T]
    idx = idx / idx.iloc[0] * 100
    fig = go.Figure()
    for col, color, dash in [("Salario medio nominal", C["nominal"], None), ("IPC", C["alerta"], "dot"),
                             ("Salario medio real", C["real"], None)]:
        fig.add_trace(go.Scatter(x=T, y=idx[col], name=col, mode="lines+markers+text",
                                 line=dict(color=color, width=3, dash=dash),
                                 text=[""] * 4 + [fmt(idx[col].iloc[-1])], textposition="middle right"))
    fig.update_layout(title="Ilusión monetaria: base 2025-T1 = 100", yaxis_range=[95, 145])
    c1, c2 = st.columns([3, 2])
    mostrar(c1, estilo(fig, 400))

    sec = s("Variación real del salario por sector").sort_values("valor")
    fig = px.bar(sec, x="valor", y="categoria", orientation="h", text=sec["valor"].map(lambda x: fmt(x, 1, True) + "%"),
                 color=sec["valor"] > 0, color_discrete_map={True: C["sube"], False: C["baja"]},
                 title="Salario real por sector, 2025-T1 a 2026-T1")
    mostrar(c2, estilo(fig, 400, leyenda=False))

    c1, c2, c3 = st.columns(3)
    br = s("Brecha salarial de género")
    fig = px.bar(br, x="periodo", y="valor", color="categoria", barmode="group", text=br["valor"].map(lambda x: fmt(x) + "%"),
                 color_discrete_map={"Media": C["real"], "Mediana": C["gris"]}, title="Brecha salarial de género (%)")
    mostrar(c1, estilo(fig, 320))

    cob = pd.concat([s("Cobertura de la CBT (salario medio / CBT)").assign(serie="Salario medio"),
                     s("Cobertura de la CBT (salario mediano / CBT)").assign(serie="Salario mediano")])
    fig = px.line(cob, x="periodo", y="valor", color="serie", markers=True, title="Canastas básicas que cubre un salario",
                  color_discrete_map={"Salario medio": C["real"], "Salario mediano": C["gris"]})
    mostrar(c2, estilo(fig, 320))

    med = s("Salario mediano", medida="real").set_index("periodo")["valor"].loc[T]
    prom = s("Salario medio", medida="real").set_index("periodo")["valor"].loc[T]
    dif = pd.DataFrame({"Media": prom.pct_change() * 100, "Mediana": med.pct_change() * 100}).iloc[1:].reset_index()
    dif = dif.melt(id_vars="periodo", var_name="medida", value_name="var")
    fig = px.bar(dif, x="periodo", y="var", color="medida", barmode="group", title="Salario real: media vs mediana (var. %)",
                 color_discrete_map={"Media": C["real"], "Mediana": C["gris"]})
    mostrar(c3, estilo(fig, 320))
    st.caption("Cuando la media y la mediana se mueven en sentidos opuestos, la mejora se concentra en una parte de la distribución (Brief 01-02).")

# ============================================================ SECTOR EXTERNO
with tabs[2]:
    st.markdown("**Pregunta del Brief 03:** ¿alcanza con mirar el intercambio comercial para evaluar la situación externa?")
    c1, c2 = st.columns(2)
    comp = df[(df["indicador"].isin(["Exportaciones", "Importaciones", "Saldo comercial"])) &
              (df["periodo"].isin(["1S 2025", "1S 2026"]))]
    fig = px.bar(comp, x="indicador", y="valor", color="periodo", barmode="group", text=comp["valor"].map(lambda x: fmt(x, 0)),
                 color_discrete_map={"1S 2025": C["previo"], "1S 2026": C["real"]}, category_orders={"periodo": ["1S 2025", "1S 2026"]},
                 title="Comercio exterior, 1S 2025 vs 1S 2026 (MM USD)")
    mostrar(c1, estilo(fig, 380))

    flujo = pd.DataFrame({"concepto": ["Saldo comercial (ago)", "Compras del BCRA (ago)", "Reservas netas (ago)"],
                          "valor": [v("Saldo comercial", "Ago 2026"), v("Compras de divisas del BCRA", "Ago 2026"),
                                    v("Reservas internacionales netas", "Ago 2026")]})
    fig = px.bar(flujo, x="concepto", y="valor", text=flujo["valor"].map(lambda x: fmt(x, 0)),
                 color_discrete_sequence=[C["real"]], title="Del superávit a las reservas (MM USD)")
    mostrar(c2, estilo(fig, 380, leyenda=False))

    c1, c2 = st.columns(2)
    bl = s("Saldo comercial por bloque").sort_values("valor")
    fig = px.bar(bl, x="valor", y="categoria", orientation="h", text=bl["valor"].map(lambda x: fmt(x, 0)),
                 color=bl["valor"] > 0, color_discrete_map={True: C["sube"], False: C["baja"]},
                 title="Saldo comercial por bloque, 1S 2026 (MM USD)")
    mostrar(c1, estilo(fig, 400, leyenda=False))

    pr = s("Exportaciones por producto").merge(s("Var. interanual de exportaciones por producto")[["categoria", "valor"]],
                                               on="categoria", suffixes=("", "_var")).sort_values("valor")
    fig = px.bar(pr, x="valor", y="categoria", orientation="h",
                 text=pr.apply(lambda r: f"{fmt(r['valor'], 0)}  ({fmt(r['valor_var'], 1, True)}%)", axis=1),
                 color_discrete_sequence=[C["real"]], title="Principales productos, 1S 2026 (MM USD y var. %)")
    mostrar(c2, estilo(fig, 400, leyenda=False))

    c1, c2 = st.columns(2)
    fig = go.Figure(go.Indicator(mode="gauge+number+delta", value=tcrm,
                                 delta=dict(reference=tcrm_h, relative=True, valueformat=".1%"),
                                 gauge=dict(axis=dict(range=[50, 180]), bar=dict(color=C["real"]),
                                            threshold=dict(line=dict(color=C["baja"], width=4), value=tcrm_h))))
    fig.update_layout(title="ITCRM agosto 2026 vs promedio histórico (113,2)")
    mostrar(c1, estilo(fig, 380, leyenda=False))
    total = v("Var. interanual de exportaciones por región", "1S 2026", "Total país")
    c2.markdown("**Competitividad y regiones**")
    c2.markdown(f"- ITCRM más bajo = peso más apreciado = menor competitividad-precio.\n"
                f"- El complejo petrolero (USD 8.116 MM) ya casi iguala al sojero (USD 9.082 MM).\n"
                f"- Las exportaciones crecieron {fmt(total)}% en el país, impulsadas por NOA (+68,2%) y Patagonia (+51,7%). "
                f"La región Pampeana (+15,2%), Cuyo (+14,1%) y el NEA (+14,6%) quedaron por debajo del promedio.")

# ==================================================================== FISCAL
with tabs[3]:
    st.markdown("**Pregunta del Brief 04:** ¿“equilibrio fiscal” o “situación fiscal delicada”? Los dos titulares "
                "usan datos oficiales: el primero los lee en pesos corrientes y el segundo descontando la inflación.")
    conceptos = ["Ingresos totales", "Recaudación tributaria", "Gastos primarios", "Resultado primario", "Resultado financiero"]
    filas = []
    for cpt in conceptos:
        for med in ["nominal", "real"]:
            filas.append({"concepto": cpt, "lectura": "Titular A · nominal" if med == "nominal" else "Titular B · real",
                          "var": var(v(cpt, "Ene-ago 2025", medida=med), v(cpt, "Ene-ago 2026", medida=med))})
    fv = pd.DataFrame(filas)
    fig = px.bar(fv, x="concepto", y="var", color="lectura", barmode="group", text=fv["var"].map(lambda x: fmt(x, 1, True) + "%"),
                 color_discrete_map={"Titular A · nominal": C["nominal"], "Titular B · real": C["real"]},
                 title="Variación interanual ene-ago 2026: misma información, dos lecturas")
    mostrar(st, estilo(fig, 420))

    c1, c2, c3 = st.columns(3)
    de = s("Deuda bruta de la Administración Central")
    fig = px.bar(de, x="periodo", y="valor", color="categoria", text=de["valor"].map(lambda x: fmt(x / 1000, 1)),
                 title="Deuda bruta (miles de MM USD)",
                 color_discrete_sequence=[C["real"], C["nominal"], C["alerta"]])
    mostrar(c1, estilo(fig, 380))

    gp = s("Gasto en personal / PIB")
    fig = px.line(gp, x="periodo", y="valor", markers=True, text=gp["valor"].map(lambda x: fmt(x, 2) + "%"),
                  title="Gasto en personal (% del PIB)", color_discrete_sequence=[C["real"]])
    fig.update_traces(textposition="top center")
    mostrar(c2, estilo(fig, 380, leyenda=False))

    dot = s("Dotación de personal")
    fig = px.bar(dot, x="categoria", y="valor", color="periodo", barmode="group", text=dot["valor"].map(lambda x: fmt(x, 0)),
                 color_discrete_map={"Ago 2025": C["previo"], "Ago 2026": C["real"]}, title="Dotación del Estado nacional")
    mostrar(c3, estilo(fig, 380))

    ip = s("Ingreso medio de asalariados públicos")
    ipn = ip[ip["medida"] == "nominal"].set_index("periodo")["valor"]
    ipr = ip[ip["medida"] == "real"].set_index("periodo")["valor"]
    c1, c2 = st.columns(2)
    tab_ip = pd.DataFrame({"nominal": ipn.pct_change() * 100, "real": ipr.pct_change() * 100}).iloc[1:].reset_index().melt(
        id_vars="periodo", var_name="medida", value_name="var")
    fig = px.bar(tab_ip, x="periodo", y="var", color="medida", barmode="group", text=tab_ip["var"].map(lambda x: fmt(x, 1, True) + "%"),
                 color_discrete_map={"nominal": C["nominal"], "real": C["real"]}, title="Ingreso de asalariados públicos (var. ia)")
    mostrar(c1, estilo(fig, 340))
    c2.markdown("**Tamaño del Estado: cómo leerlo**")
    c2.markdown("- Gasto en personal: cae en términos reales (−21,9% en 2024 y −9,8% en 2025) y en peso sobre el PIB.\n"
                "- Dotación: 6,7% menos agentes en la APN y 20,8% menos en la administración centralizada.\n"
                "- Los universos no son iguales: el gasto cubre la Administración Nacional, la dotación excluye "
                "fuerzas de seguridad y el ingreso medio (EPH) incluye provincias y municipios.")

# ===================================================== MONETARIO Y FINANCIERO
with tabs[4]:
    st.markdown("**Pregunta del Brief 05:** ¿las condiciones monetarias y financieras favorecen o restringen la actividad?")
    c1, c2 = st.columns(2)
    tasas = pd.DataFrame({"concepto": ["BADLAR (TNA)", "Inflación interanual", "Tasa real"],
                          "valor": [22.0, infl, tasa_real]})
    fig = px.bar(tasas, x="concepto", y="valor", text=tasas["valor"].map(lambda x: fmt(x, 1) + "%"),
                 color="concepto", color_discrete_map={"BADLAR (TNA)": C["nominal"], "Inflación interanual": C["alerta"], "Tasa real": C["baja"]},
                 title="Costo real del dinero ≈ (1 + tasa) / (1 + inflación) − 1")
    mostrar(c1, estilo(fig, 380, leyenda=False))
    c1.caption("Aproximación ex post con la inflación interanual del Brief 04. Responde al comentario docente: el Brief 05 presentaba la fórmula pero no el cálculo.")

    cr = pd.DataFrame({"crédito": ["En pesos (real)", "En dólares"],
                       "var": [v("Crédito en pesos al sector privado (var. interanual)", "2026"),
                               v("Crédito en dólares al sector privado (var. interanual)", "2026")]})
    fig = px.bar(cr, x="crédito", y="var", text=cr["var"].map(lambda x: fmt(x, 1, True) + "%"),
                 color="crédito", color_discrete_map={"En pesos (real)": C["nominal"], "En dólares": C["real"]},
                 title="Crédito privado: dos velocidades (var. ia)")
    mostrar(c2, estilo(fig, 380, leyenda=False))

    c1, c2 = st.columns(2)
    res = pd.DataFrame({"momento": ["Brutas jun 2026", "Brutas ago 2026", "Netas ago 2026"],
                        "valor": [v("Reservas internacionales brutas", "Jun 2026"), v("Reservas internacionales brutas", "Ago 2026"),
                                  v("Reservas internacionales netas", "Ago 2026")]})
    fig = px.bar(res, x="momento", y="valor", text=res["valor"].map(lambda x: fmt(x, 0)),
                 color_discrete_sequence=[C["real"]], title="Reservas internacionales (MM USD)")
    mostrar(c1, estilo(fig, 360, leyenda=False))
    c1.caption("Junio: punto medio del rango 43.000–47.000 del Brief 05. Compras netas del BCRA en el 1S: ≈ USD 6.300 MM.")

    liq = pd.DataFrame({"agregado": ["Base monetaria real", "M2 privado real"],
                        "var": [v("Base monetaria real (var. interanual)", "2026"), v("M2 privado transaccional real (var. interanual)", "2026")]})
    fig = px.bar(liq, x="agregado", y="var", text=liq["var"].map(lambda x: fmt(x, 0, True) + "%"),
                 color_discrete_sequence=[C["baja"]], title="Liquidez: agregados reales (var. ia)")
    mostrar(c2, estilo(fig, 360, leyenda=False))
    c2.caption(f"Base monetaria ≈ {fmt(v('Base monetaria / PIB', '2026'))}% del PIB. Sirve como indicador de liquidez, el punto que el comentario docente marcó como faltante.")

# ================================================================ RELACIONES
with tabs[5]:
    st.subheader("Mapa de relaciones entre variables")
    POS = {"Inflación": (0, 0.3), "Salario real": (-2.4, 1.8), "Actividad interna": (-3.6, 0.2),
           "Resultado fiscal real": (-2.4, -1.4), "Gasto en personal y dotación": (-3.8, -2.7),
           "Crédito en pesos": (-1.2, -2.9), "Tasa de interés real": (0.4, -2.0), "Tipo de cambio real": (1.4, 1.7),
           "Deuda pública en USD": (-0.4, 3.0), "Exportaciones y saldo comercial": (4.0, 0.2), "Crédito en USD": (4.4, 2.4),
           "Compras del BCRA": (4.0, -1.4), "Reservas": (2.2, -2.5)}
    EJE_NODO = {"Inflación": "Transversal", "Salario real": "Ingresos y precios", "Actividad interna": "Ingresos y precios",
                "Resultado fiscal real": "Fiscal", "Gasto en personal y dotación": "Fiscal", "Deuda pública en USD": "Fiscal",
                "Crédito en pesos": "Monetario y financiero", "Tasa de interés real": "Monetario y financiero",
                "Crédito en USD": "Monetario y financiero", "Reservas": "Monetario y financiero",
                "Tipo de cambio real": "Sector externo", "Exportaciones y saldo comercial": "Sector externo",
                "Compras del BCRA": "Sector externo"}

    c1, c2 = st.columns([3, 2])
    elegido = c2.selectbox("Elegí una variable para ver con qué se conecta", list(POS), index=0)
    fig = go.Figure()
    for _, r in rel.iterrows():
        activo = elegido in (r["origen"], r["destino"])
        x0, y0 = POS[r["origen"]]
        x1, y1 = POS[r["destino"]]
        color = (C["sube"] if r["efecto"] == "+" else C["baja"]) if activo else "rgba(138,148,166,.35)"
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=3, arrowsize=1.3, arrowwidth=3 if activo else 1.5,
                           arrowcolor=color, standoff=22, startstandoff=22)
    for nodo, (x, y) in POS.items():
        fig.add_annotation(x=x, y=y - 0.42, text=nodo, showarrow=False, font=dict(size=12, color="#2B2F36"),
                           bgcolor="rgba(255,255,255,.55)", borderpad=1)
        fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers",
                                 marker=dict(size=34 if nodo == elegido else 24, color=EJES[EJE_NODO[nodo]],
                                             line=dict(width=3 if nodo == elegido else 0, color="white")),
                                 hoverinfo="text", hovertext=EJE_NODO[nodo], showlegend=False))
    for eje, color in EJES.items():
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(size=12, color=color), name=eje))
    fig.update_xaxes(visible=False, range=[-5.4, 5.6])
    fig.update_yaxes(visible=False, range=[-3.4, 3.5])
    mostrar(c1, estilo(fig, 560))

    with c2:
        st.caption("Flecha verde (+): se mueven en el mismo sentido. Flecha roja (−): en sentido contrario.")
        for _, r in rel[(rel["origen"] == elegido) | (rel["destino"] == elegido)].iterrows():
            with st.container(border=True):
                st.markdown(f"**{r['origen']} → {r['destino']}** ({r['efecto']})")
                st.markdown(r["mecanismo"])
                st.markdown(f"*Evidencia:* {r['evidencia']}")
                st.caption(f"Brief {r['briefs']}")

# ============================================================ DATOS Y NOTAS
with tabs[6]:
    c1, c2 = st.columns([3, 2])
    with c1:
        ejes = st.multiselect("Filtrar por eje", list(EJES), default=list(EJES))
        vista = df[df["eje"].isin(ejes)]
        st.dataframe(vista, width="stretch", hide_index=True, height=420)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, sheet_name="Indicadores", index=False)
            rel.to_excel(w, sheet_name="Relaciones", index=False)
        st.download_button("Descargar datos en Excel", buf.getvalue(), "monitor_macroeconomico.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        st.markdown("**Notas metodológicas**")
        st.markdown(
            "- Los datos provienen de los Briefs 01 a 05; las fuentes primarias son INDEC, BCRA, Secretaría de Hacienda "
            "y Secretaría de Finanzas.\n"
            "- Cuando un brief informa un rango, se usa el punto medio y se indica en la columna *nota*.\n"
            "- Los valores de agosto 2025 y del 1S 2025 del comercio exterior se calcularon a partir de las variaciones interanuales.\n"
            "- La inflación interanual (≈33,2%) surge de la relación entre las series nominales y reales del Brief 04.\n"
            "- La tasa real es una aproximación ex post: compara la BADLAR con la inflación pasada, no con la esperada.\n"
            "- Los períodos no coinciden entre briefs (trimestres, meses, semestres), así que las relaciones se presentan "
            "como evidencia conjunta y no como correlaciones estadísticas.")
