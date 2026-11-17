import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Rutina personal", page_icon="🏋️", layout="wide")

# Configura APP_PASSWORD y DATABASE_URL en variables de entorno o en Streamlit secrets.
def setting(name, default=None):
    try:
        value = st.secrets.get(name)
        if value is not None:
            return value
    except Exception:
        pass
    return os.getenv(name, default)

APP_PASSWORD = setting("APP_PASSWORD")
DATABASE_URL = setting("DATABASE_URL", f"sqlite:///{Path(__file__).with_name('routine.db')}")

if not APP_PASSWORD:
    st.error("La aplicación está protegida. Configura APP_PASSWORD en las variables de entorno o como secreto antes de usarla.")
    st.code('APP_PASSWORD = "elige-una-clave-segura"\nDATABASE_URL = "postgresql+psycopg://usuario:clave@servidor:5432/base"', language="toml")
    st.stop()

@st.cache_resource
def get_engine(url):
    return create_engine(url, pool_pre_ping=True)

engine = get_engine(DATABASE_URL)

with engine.begin() as conn:
    conn.execute(text("CREATE TABLE IF NOT EXISTS routine_state (id INTEGER PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)"))

DEFAULT_STATE = {
    "date": date.today().isoformat(), "done": {}, "symptoms": {}, "weekly": {},
    "journal": [], "mode": "standard", "streak": 0, "mobility_length": "short",
}


def load_state():
    with engine.begin() as conn:
        row = conn.execute(text("SELECT payload FROM routine_state WHERE id = 1")).fetchone()
    if not row:
        return json.loads(json.dumps(DEFAULT_STATE))
    try:
        loaded = json.loads(row[0])
        state = {**DEFAULT_STATE, **loaded}
        if state["date"] != date.today().isoformat():
            state["date"] = date.today().isoformat()
            state["done"] = {}
            state["symptoms"] = {}
        return state
    except (TypeError, ValueError):
        return json.loads(json.dumps(DEFAULT_STATE))


def save_state(state):
    payload = json.dumps(state, ensure_ascii=False)
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT id FROM routine_state WHERE id = 1")).fetchone()
        if exists:
            conn.execute(text("UPDATE routine_state SET payload = :payload, updated_at = :updated WHERE id = 1"), {"payload": payload, "updated": now})
        else:
            conn.execute(text("INSERT INTO routine_state (id, payload, updated_at) VALUES (1, :payload, :updated)"), {"payload": payload, "updated": now})


def ex(id, title, category, dose, instructions, alternative, kind="general", reps=""):
    return {
        "id": id,
        "title": title,
        "category": category,
        "dose": dose,
        "instructions": instructions,
        "alternative": alternative,
        "kind": kind,
        "reps": reps,
    }

HOME = [
    ex("home-walk", "Pausa activa: caminar o cambiar de postura", "Pausa", "1–2 min", "Levántate y camina un poco, o cambia de postura. No es necesario mantener una postura perfecta.", "Si no puedes caminar, ponte de pie y vuelve a sentarte despacio."),
    ex("home-shoulder", "Soltar hombros y movilidad cómoda", "Hombros · rango pequeño", "5–8 repeticiones", "Sentada o de pie, lleva suavemente los codos un poco hacia atrás y vuelve. Mantén cuello y mandíbula relajados.", "Solo respira con calma y deja caer los hombros. No eleves los brazos por encima de la cabeza."),
    ex("home-twist", "Rotación torácica pequeña", "Espalda alta · control", "3–5 por lado", "Gira suavemente el tronco unos grados con la mirada al frente. Regresa al centro entre repeticiones.", "Omite el giro y camina un minuto o cambia de postura."),
    ex("home-neck", "Giro cervical corto (opcional)", "Cuello · solo si resulta cómodo", "2–3 por lado", "Mira ligeramente a un lado y vuelve al centro; no hagas círculos ni fuerces el final del rango.", "Omítelo por completo; no es necesario mover el cuello para completar la pausa."),
]
MOBILITY = [
    ex("mob-thoracic", "Apertura torácica apoyada en silla", "Columna torácica · suave", "4–6 repeticiones", "Sentada, apoya la espalda alta en el respaldo y permite un pequeño movimiento de apertura del pecho. Cabeza neutra, sin arquear la espalda baja.", "Haz una respiración cómoda con los pies apoyados."),
    ex("mob-twist", "Rotación torácica sentada", "Movilidad complementaria", "4–6 por lado", "Cruza los brazos suavemente sobre el pecho y gira un poco el tronco. La cabeza acompaña solo si no molesta.", "Reduce el giro o sáltalo."),
    ex("mob-band", "Remo muy ligero con banda", "Activación opcional · banda", "1–2 × 8–12", "Ancla la banda de forma segura a la altura del torso. Tira los codos hacia atrás sin encoger hombros ni adelantar el cuello.", "Sin banda: junta suavemente los omóplatos o simplemente omítelo."),
    ex("mob-hip", "Balanceo cómodo de cadera sentado", "Cadera · sin estirar fuerte", "30 segundos", "Sentada, alterna pequeños cambios de peso sobre los isquiones sin girar o forzar la espalda.", "Ponte de pie y da unos pasos."),
]


def core(id, title, instructions, alternative, reps):
    return ex(id, title, "Core · estabilidad y control", f"3 series × {reps}", instructions, alternative, "Core", reps)


def lift(id, title, category, dose, instructions, alternative, reps="8–12"):
    return ex(id, title, category, dose, instructions, alternative, "Fuerza", reps)

GYM = {
    "A": {"name": "Piernas, glúteos y tracción", "core": [
        core("a-deadbug", "Dead bug", "Tumbada, mueve lentamente una pierna y vuelve; usa un recorrido que te permita respirar y mantener el tronco cómodo.", "Desliza un talón por el suelo con recorrido corto.", "6–8 por lado"),
        core("a-pallof", "Pallof press en polea", "De pie de lado a una polea a la altura del pecho, extiende las manos al frente y resiste el giro. Brazos sin elevarlos sobre la cabeza.", "Usa banda ligera anclada a la altura del pecho o acorta el recorrido.", "8–10 por lado"),
    ], "lifts": [
        lift("a-hip", "Hip thrust en máquina o puente cargado", "Glúteos · principal", "3 × 8–12", "Apoya la espalda de forma estable. Eleva la pelvis contrayendo glúteos; detente en un rango cómodo, sin arquear la espalda.", "Puente de glúteos sin carga o con banda ligera."),
        lift("a-press", "Prensa de piernas", "Tren inferior", "3 × 8–12", "Coloca los pies en una posición cómoda. Baja solo hasta donde pelvis y espalda estén cómodas; empuja con control.", "Sentadilla a caja o menor rango."),
        lift("a-row", "Remo sentado con apoyo", "Espalda · tracción", "3 × 8–12", "Tira de los agarres hacia el torso, hombros relajados y cuello neutro. No encogas los hombros.", "Remo con banda anclada delante."),
        lift("a-chest", "Press de pecho horizontal en máquina (opcional)", "Pecho · opcional", "3 × 8–12", "Empuje horizontal a una altura cómoda, sin llevar los brazos por encima de las orejas. Prueba carga ligera y rango tolerable; no es obligatorio.", "Omitir y consultar a un profesional para elegir una variante cómoda. No sustituir por empuje vertical."),
        lift("a-biceps", "Curl de bíceps", "Brazos · bíceps", "3 × 10–12", "Flexiona los codos cerca del torso; mantén cuello y hombros relajados y evita balancear el cuerpo.", "Mancuernas más ligeras o banda suave.", "10–12"),
        lift("a-triceps", "Extensión de tríceps en polea hacia abajo", "Brazos · tríceps", "3 × 10–12", "Codos cerca del torso. Empuja el agarre hacia abajo sin llevar las manos detrás del cuerpo ni mover el tronco.", "Banda anclada de forma segura por arriba, empujando hacia abajo; menos carga o rango.", "10–12"),
    ]},
    "B": {"name": "Isquiotibiales, glúteos y espalda", "core": [
        core("b-bird-dog", "Bird dog", "En cuatro apoyos, desliza una pierna atrás; si resulta cómodo, añade el brazo contrario. Mantén el tronco estable y sin arquear.", "Mueve solo una pierna o un brazo; omite si incomoda.", "6–8 por lado"),
        core("b-side-plank", "Plancha lateral con rodillas apoyadas", "Apoya antebrazo y rodillas y eleva ligeramente la pelvis manteniendo respiración fluida.", "Haz una inclinación lateral mínima de pie o sáltala.", "15–20 segundos por lado"),
    ], "lifts": [
        lift("b-curl", "Curl femoral sentado", "Piernas · isquiotibiales", "3 × 10–15", "Ajusta la máquina y flexiona las rodillas de forma controlada, sin apretar mandíbula ni aguantar la respiración.", "Reduce carga o recorrido.", "10–15"),
        lift("b-rdl", "Peso muerto rumano con mancuernas (opcional)", "Glúteos e isquiotibiales", "3 × 8–10", "Solo si ya conoces la técnica y resulta cómodo: lleva la cadera atrás con mancuernas cerca de las piernas; detente antes de perder control.", "Curl femoral en máquina o reduce rango/carga; también puedes omitirlo.", "8–10"),
        lift("b-pulldown", "Jalón al pecho", "Espalda · tracción hacia abajo", "3 × 8–12", "Tira la barra al frente hacia la parte alta del pecho, nunca detrás de la nuca. Mantén hombros cómodos y rango que no empeore síntomas.", "Remo sentado o con banda si la posición inicial o el jalón molestan."),
        lift("b-hipab", "Abducción de cadera en máquina", "Glúteos · lateral", "3 × 12–15", "Abre las piernas en un rango cómodo y vuelve despacio sin balancearte. Esto fortalece, pero no reduce grasa localizada.", "Pasos laterales con banda por encima de las rodillas.", "12–15"),
        lift("b-biceps", "Curl de bíceps", "Brazos · bíceps", "3 × 10–12", "Flexiona con los codos junto al torso y sin elevar hombros. Ajusta asiento o carga si el cuello se tensa.", "Mancuernas o banda ligera en rango corto.", "10–12"),
        lift("b-triceps", "Extensión de tríceps en polea hacia abajo", "Brazos · tríceps", "3 × 10–12", "Codos cerca del cuerpo y empuja el agarre hacia abajo con control; evita extender los brazos sobre la cabeza.", "Banda ligera anclada arriba y empujando hacia abajo; reduce carga o rango.", "10–12"),
    ]},
    "C": {"name": "Piernas, glúteos, espalda y brazos", "core": [
        core("c-bridge-march", "Marcha de puente (o dead bug)", "Desde un puente cómodo, alterna levantar un pie unos centímetros solo si la pelvis se mantiene estable.", "Puente bilateral sin marchar o dead bug sencillo.", "6–8 por lado"),
        core("c-pallof", "Pallof press en polea", "Resiste el giro de la banda o polea a la altura del pecho. Mantén los codos en rango cómodo.", "Reduce tensión o hazlo sentado con banda.", "8–10 por lado"),
    ], "lifts": [
        lift("c-squat", "Sentadilla a caja o prensa", "Piernas · cuádriceps y glúteos", "3 × 8–12", "Si eliges sentadilla, toca una caja estable y vuelve arriba; en prensa, ajusta profundidad a un rango cómodo.", "Elige la opción más estable o reduce recorrido/carga."),
        lift("c-kick", "Extensión de cadera en polea", "Glúteos · énfasis", "3 × 10–12 por lado", "Sujétate a un apoyo, mueve la pierna desde la cadera sin arquear la espalda ni girar la pelvis.", "Extensión de cadera con banda o puente."),
        lift("c-legext", "Extensión de rodilla en máquina", "Tren inferior · cuádriceps", "3 × 10–15", "Extiende y flexiona la rodilla con carga controlada, sin golpear el tope.", "Reduce carga o recorrido.", "10–15"),
        lift("c-row", "Remo sentado o con apoyo", "Espalda · tracción", "3 × 8–12", "Tracciona hacia el torso con cuello neutro y sin elevar hombros.", "Banda ligera anclada de forma segura."),
        lift("c-chest", "Press de pecho horizontal en máquina (opcional)", "Pecho · opcional", "3 × 8–12", "Empuje horizontal; no sobre la cabeza. Usa un rango cómodo y omítelo si aumenta el tinnitus o alguna molestia.", "Omitir y solicitar alternativa profesionalmente; no hacer empuje vertical."),
        lift("c-arms", "Curl de bíceps + tríceps polea abajo", "Brazos · bíceps y tríceps", "3 × 10–12 cada uno", "Haz ambos movimientos como ejercicios separados, tres series cada uno: curl junto al torso y tríceps empujando hacia abajo.", "Banda ligera o elimina el movimiento que provoque síntomas.", "10–12"),
    ]},
}

ALL = HOME + MOBILITY + [item for session in GYM.values() for item in session["core"] + session["lifts"]]
STOP_NOTE = "Detén el movimiento si empeoran el dolor o el tinnitus, aparece mareo, entumecimiento u otro síntoma nuevo. No entrenes a través de síntomas que empeoran."

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.title("Rutina personal")
    password = st.text_input("Contraseña", type="password")
    if st.button("Entrar", type="primary"):
        if password and password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    st.caption("El acceso es privado. Tus datos se guardan en la base de datos configurada por quien administra la app.")
    st.stop()

if "routine" not in st.session_state:
    st.session_state.routine = load_state()
state = st.session_state.routine
if state["date"] != date.today().isoformat():
    state["date"] = date.today().isoformat()
    state["done"] = {}
    state["symptoms"] = {}

st.title("Rutina personal")
st.caption("Seguimiento personal. No sustituye una valoración profesional ni es tratamiento del dolor o del tinnitus.")
mode_names = {"standard": "Día estándar", "recovery": "Recuperación suave", "consolidation": "Consolidación"}
mode = st.selectbox("Modo del día", list(mode_names), format_func=lambda value: mode_names[value], index=list(mode_names).index(state.get("mode", "standard")))
state["mode"] = mode
completed_count = sum(bool(state["done"].get(exercise["id"], 0)) for exercise in ALL)
st.progress(completed_count / len(ALL), text=f"{completed_count} de {len(ALL)} ejercicios marcados hoy")


def week_record(exercise_id):
    iso = date.today().isocalendar()
    week = f"{iso.year}-W{iso.week:02d}"
    state["weekly"].setdefault(week, {})
    record = state["weekly"][week].setdefault(exercise_id, {"sets": [{}, {}, {}]})
    while len(record["sets"]) < 3:
        record["sets"].append({})
    return week, record


def exercise_card(exercise, gym_exercise=False):
    exid = exercise["id"]
    with st.container(border=True):
        st.subheader(exercise["title"])
        st.caption(f"{exercise['category']} · {exercise['dose']}")
        st.write(exercise["instructions"])
        st.info(f"Alternativa: {exercise['alternative']}")
        st.warning(f"Precaución: {STOP_NOTE}")
        current = int(state["done"].get(exid, 0) or 0)
        state["done"][exid] = int(st.checkbox("Marcar hecho hoy", value=current > 0, key=f"done-{exid}"))
        sensation = st.selectbox("¿Cómo se sintió?", ["Sin registrar", "Alivió", "Igual", "Empeoró"], index=["", "better", "same", "worse"].index(state["symptoms"].get(exid, "")), key=f"symptom-{exid}")
        state["symptoms"][exid] = {"Sin registrar": "", "Alivió": "better", "Igual": "same", "Empeoró": "worse"}[sensation]
        if gym_exercise:
            week, record = week_record(exid)
            st.caption(f"Registro semanal · {week} — anota repeticiones y kg por serie")
            cols = st.columns([0.6, 1, 1, 0.8])
            for col, label in zip(cols, ["Serie", "Reps", "kg", "Hecha"]):
                col.caption(label)
            for idx in range(3):
                row = record["sets"][idx]
                cols = st.columns([0.6, 1, 1, 0.8])
                cols[0].write(str(idx + 1))
                reps_value = cols[1].number_input(f"Reps serie {idx + 1}", min_value=0, max_value=99, value=int(row.get("reps") or 0), key=f"reps-{exid}-{idx}", label_visibility="collapsed")
                kg_value = cols[2].number_input(f"Kg serie {idx + 1}", min_value=0.0, step=0.5, value=float(row.get("kg") or 0), key=f"kg-{exid}-{idx}", label_visibility="collapsed")
                row["reps"] = reps_value if reps_value else ""
                row["kg"] = kg_value if kg_value else ""
                row["done"] = cols[3].checkbox(f"Serie {idx + 1} hecha", value=bool(row.get("done")), key=f"set-{exid}-{idx}", label_visibility="collapsed")
            st.caption("Deja los kg en 0 si el ejercicio no lleva carga.")


tabs = st.tabs(["Inicio", "Movilidad", "Gimnasio", "Pausas", "Diario", "Datos"])
with tabs[0]:
    st.info("Elige una o dos opciones y cambia de postura o camina 2–3 minutos cada 45–60 minutos si te resulta viable. No hace falta mantener una postura perfecta.")
    for exercise in HOME:
        exercise_card(exercise)
with tabs[1]:
    st.info("Escoge según cómo te sientas. Puedes omitir cualquier opción; no hagas manipulaciones bruscas del cuello ni estiramientos intensos.")
    length = st.radio("Duración", ["short", "full"], format_func=lambda value: "Breve · 3–5 min" if value == "short" else "Completa · 8–10 min", horizontal=True, index=0 if state.get("mobility_length") == "short" else 1)
    state["mobility_length"] = length
    for exercise in (MOBILITY[:2] if length == "short" else MOBILITY):
        exercise_card(exercise)
with tabs[2]:
    st.info("Tres sesiones semanales de una hora, con recuperación entre ellas cuando sea posible. Core primero. Los descansos son orientativos: descansa más si lo necesitas.")
    day = st.radio("Sesión", list(GYM), format_func=lambda key: f"Sesión {key} · {GYM[key]['name']}", horizontal=True)
    session = GYM[day]
    st.markdown("**Orden sugerido:** calentamiento suave · movilidad cómoda · core · fuerza · cierre y registro.")
    for exercise in session["core"] + session["lifts"]:
        exercise_card(exercise, gym_exercise=True)
    st.info("Progresión: suma repeticiones dentro del rango; cuando las tres series alcancen el tope con buena técnica, comodidad y 2–3 repeticiones en reserva en sesiones sucesivas, aumenta el menor incremento disponible y vuelve al mínimo del rango. No se puede reducir grasa de forma localizada.")
with tabs[3]:
    st.info("Escoge una pausa breve. Si una opción no te sienta bien, omítela. Alternar posiciones y caminar un poco puede ser práctico.")
    for exercise in HOME[:3]:
        exercise_card(exercise)
with tabs[4]:
    st.info("El diario es personal, no diagnóstico. Escala propia: 1 leve/bajo · 5 intenso/alto.")
    with st.form("journal_form", clear_on_submit=True):
        log_date = st.date_input("Fecha", value=date.today())
        c1, c2, c3 = st.columns(3)
        energy = c1.selectbox("Energía", ["", "1", "2", "3", "4", "5"])
        trap = c2.selectbox("Trapecio", ["", "1", "2", "3", "4", "5"])
        tinnitus = c3.selectbox("Tinnitus", ["", "1", "2", "3", "4", "5"])
        note = st.text_area("Notas opcionales")
        if st.form_submit_button("Guardar registro"):
            state["journal"].append({"date": log_date.isoformat(), "energy": energy, "trap": trap, "tinnitus": tinnitus, "note": note.strip()})
            state["streak"] = int(state.get("streak", 0)) + 1
            save_state(state)
            st.success("Registro guardado.")
    for record in reversed(state["journal"]):
        with st.container(border=True):
            st.markdown(f"**{record.get('date', '')}** · Energía {record.get('energy') or '—'}/5 · Trapecio {record.get('trap') or '—'}/5 · Tinnitus {record.get('tinnitus') or '—'}/5")
            if record.get("note"):
                st.write(record["note"])
    if st.button("Borrar registros del diario"):
        state["journal"] = []
        save_state(state)
        st.rerun()
    st.error("El tinnitus persistente de un solo oído y el dolor crónico merecen valoración profesional. Busca orientación ante pérdida repentina de audición, mareo importante, debilidad, adormecimiento o dolor agudo.")
with tabs[5]:
    st.write("La app guarda los registros en la base de datos configurada. Al desplegarla en la nube, configura una base de datos compartida para que los datos estén disponibles desde distintos dispositivos.")
    st.download_button("Exportar copia JSON", data=json.dumps(state, ensure_ascii=False, indent=2), file_name="rutina-seguimiento-copia.json", mime="application/json")
    uploaded = st.file_uploader("Importar copia JSON", type=["json"])
    if uploaded is not None and st.button("Importar y reemplazar datos"):
        try:
            imported = json.loads(uploaded.getvalue().decode("utf-8"))
            if not isinstance(imported, dict):
                raise ValueError("El archivo no contiene un objeto JSON.")
            state.clear()
            state.update({**DEFAULT_STATE, **imported})
            save_state(state)
            st.success("Copia importada.")
            st.rerun()
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            st.error(f"No se pudo importar el archivo: {error}")
    if st.button("Cerrar sesión"):
        st.session_state.authenticated = False
        st.rerun()

save_state(state)

