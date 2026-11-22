#!/usr/bin/env python3
"""Genera MisTareas.aia, el proyecto de MIT App Inventor de la lista de tareas.

Uso:  python3 generar_aia.py

Crea la carpeta proyecto/ (los archivos sueltos, faciles de leer) y el archivo
MisTareas.aia, que es esa misma carpeta comprimida en .zip. El .aia se importa en
App Inventor con: Projects -> Import project (.aia) from my computer.
"""
import json
import os
import zipfile
from xml.sax.saxutils import escape

AQUI = os.path.dirname(os.path.abspath(__file__))
USUARIO = "ai_estudiante"
PROYECTO = "MisTareas"
PAQUETE = f"appinventor/{USUARIO}/{PROYECTO}"

# Versiones de un App Inventor de 2024. App Inventor actualiza solo los
# proyectos viejos al abrirlos, pero rechaza los que dicen ser mas nuevos que
# el servidor, asi que es mas seguro declarar versiones un poco antiguas.
YA_VERSION = "230"
BLOCKS_LANGUAGE_VERSION = "37"
V = {
    "Form": "31", "Label": "5", "HorizontalArrangement": "4", "TextBox": "14",
    "Button": "7", "ListView": "8", "TinyDB": "3", "Notifier": "6",
}

# Colores (formato de App Inventor: &HAARRGGBB)
AZUL = "&HFF3F51B5"
AZUL_CLARO = "&HFFE8EAF6"
ROJO = "&HFFE53935"
BLANCO = "&HFFFFFFFF"
GRIS = "&HFF555555"
NEGRO = "&HFF212121"

# ---------------------------------------------------------------------------
# 1. Pantalla (Designer)
# ---------------------------------------------------------------------------
_uuid = [1000]


def comp(tipo, nombre, hijos=None, **props):
    _uuid[0] += 1
    c = {"$Name": nombre, "$Type": tipo, "$Version": V[tipo], "Uuid": str(_uuid[0])}
    c.update({k: str(v) for k, v in props.items()})
    if hijos:
        c["$Components"] = hijos
    return c


pantalla = {
    "authURL": ["ai2.appinventor.mit.edu"],
    "YaVersion": YA_VERSION,
    "Source": "Form",
    "Properties": {
        "$Name": "Screen1", "$Type": "Form", "$Version": V["Form"], "Uuid": "0",
        "AppName": PROYECTO,
        "Title": "Mis Tareas",
        "AlignHorizontal": "3",          # centrado
        "BackgroundColor": AZUL_CLARO,
        "Sizing": "Responsive",
        "Theme": "AppTheme.Light.DarkActionBar",
        "PrimaryColor": AZUL,
        "PrimaryColorDark": "&HFF303F9F",
        "AccentColor": "&HFFFF4081",
        "$Components": [
            comp("Label", "EtiquetaTitulo", Text="Mis Tareas", FontSize="26",
                 FontBold="True", TextColor=AZUL, Width="-2", TextAlignment="1"),
            comp("HorizontalArrangement", "FilaAgregar", Width="-2",
                 AlignVertical="2", hijos=[
                     comp("TextBox", "CajaTarea", Width="-2", FontSize="16",
                          Hint="Escribe una tarea nueva..."),
                     comp("Button", "BotonAgregar", Text="Agregar", FontSize="16",
                          FontBold="True", BackgroundColor=AZUL, TextColor=BLANCO,
                          Shape="1"),
                 ]),
            comp("Label", "EtiquetaContador", Text="", FontSize="15",
                 TextColor=GRIS, Width="-2", TextAlignment="1"),
            comp("ListView", "ListaTareas", Width="-2", Height="-2",
                 BackgroundColor=BLANCO, TextColor=NEGRO),
            comp("Button", "BotonBorrarTodo", Text="Borrar todo", FontSize="14",
                 BackgroundColor=ROJO, TextColor=BLANCO, Shape="1"),
            # Componentes invisibles (aparecen debajo del telefono en el Designer)
            comp("TinyDB", "TinyDB1", Namespace="TinyDB1"),
            comp("Notifier", "NotificadorTarea"),
            comp("Notifier", "NotificadorTodo"),
        ],
    },
}
scm = "#|\n$JSON\n" + json.dumps(pantalla, ensure_ascii=False, separators=(",", ":")) + "\n|#"

# ---------------------------------------------------------------------------
# 2. Bloques (Blocks)
#    Pequenas funciones que escriben el XML de cada tipo de bloque.
# ---------------------------------------------------------------------------
_bid = [0]


def bid():
    _bid[0] += 1
    return f"b{_bid[0]:03d}"


def block(tipo, contenido="", mutation=None, pos=None):
    xy = f' x="{pos[0]}" y="{pos[1]}"' if pos else ""
    mut = ""
    if mutation is not None:
        attrs = "".join(f' {k}="{escape(str(v))}"' for k, v in mutation.items()
                        if not k.startswith("_"))
        mut = f"<mutation{attrs}>{mutation.get('_inner', '')}</mutation>"
    return f'<block type="{tipo}" id="{bid()}"{xy}>{mut}{contenido}</block>'


def field(nombre, valor):
    return f'<field name="{nombre}">{escape(str(valor))}</field>'


def value(nombre, b):
    return f'<value name="{nombre}">{b}</value>'


def statement(nombre, *bloques):
    return f'<statement name="{nombre}">{encadenar(*bloques)}</statement>' if bloques else ""


def encadenar(*bloques):
    """Pone los bloques uno debajo del otro (cada uno es el 'next' del anterior)."""
    xml = ""
    for b in reversed(bloques):
        if xml:
            b = b[: -len("</block>")] + f"<next>{xml}</next></block>"
        xml = b
    return xml


# --- texto, numeros, logica
def texto(t):
    return block("text", field("TEXT", t))


def unir(*partes):
    return block("text_join", "".join(value(f"ADD{i}", p) for i, p in enumerate(partes)),
                 {"items": len(partes)})


def texto_vacio(t):
    return block("text_isEmpty", value("VALUE", t))


def recortar(t):
    return block("text_trim", value("TEXT", t))


def texto_igual(a, b):
    return block("text_compare", field("OP", "EQUAL") + value("TEXT1", a) + value("TEXT2", b))


def falso():
    return block("logic_boolean", field("BOOL", "FALSE"))


def si(*ramas, sino=None):
    """ramas = [(condicion, [bloques]), ...]  -> si / sino si / sino"""
    contenido = ""
    for i, (cond, cuerpo) in enumerate(ramas):
        contenido += value(f"IF{i}", cond) + statement(f"DO{i}", *cuerpo)
    mut = {}
    if len(ramas) > 1:
        mut["elseif"] = len(ramas) - 1
    if sino:
        mut["else"] = 1
        contenido += statement("ELSE", *sino)
    return block("controls_if", contenido, mut)


# --- listas
def lista_vacia():
    return block("lists_create_with", "", {"items": 0})


def agregar_a_lista(lista, elemento):
    return block("lists_add_items", value("LIST", lista) + value("ITEM0", elemento), {"items": 1})


def quitar_de_lista(lista, indice):
    return block("lists_remove_item", value("LIST", lista) + value("INDEX", indice))


def largo_lista(lista):
    return block("lists_length", value("LIST", lista))


def lista_esta_vacia(lista):
    return block("lists_is_empty", value("LIST", lista))


def esta_en_lista(elemento, lista):
    return block("lists_is_in", value("ITEM", elemento) + value("LIST", lista))


# --- variables y procedimientos
def global_var(nombre, valor, pos):
    return block("global_declaration", field("NAME", nombre) + value("VALUE", valor), pos=pos)


def obtener(nombre_global):
    return block("lexical_variable_get", field("VAR", f"global {nombre_global}"))


def obtener_local(nombre):
    return block("lexical_variable_get", field("VAR", nombre))


def obtener_param(nombre):
    return block("lexical_variable_get", field("VAR", nombre),
                 {"_inner": f'<eventparam name="{nombre}"></eventparam>'})


def poner(nombre_global, valor):
    return block("lexical_variable_set", field("VAR", f"global {nombre_global}") + value("VALUE", valor))


def local(nombre, valor, *cuerpo):
    return block("local_declaration_statement",
                 field("VAR0", nombre) + value("DECL0", valor) + statement("STACK", *cuerpo),
                 {"_inner": f'<localname name="{nombre}"></localname>'})


def procedimiento(nombre, cuerpo, pos):
    return block("procedures_defnoreturn", field("NAME", nombre) + statement("STACK", *cuerpo),
                 {}, pos=pos)


def llamar(nombre):
    return block("procedures_callnoreturn", field("PROCNAME", nombre), {"name": nombre})


# --- componentes
def evento(tipo, instancia, evento_, cuerpo, pos):
    return block("component_event", field("COMPONENT_SELECTOR", instancia) + statement("DO", *cuerpo),
                 {"component_type": tipo, "is_generic": "false", "instance_name": instancia,
                  "event_name": evento_}, pos=pos)


def metodo(tipo, instancia, metodo_, *args):
    return block("component_method",
                 field("COMPONENT_SELECTOR", instancia)
                 + "".join(value(f"ARG{i}", a) for i, a in enumerate(args)),
                 {"component_type": tipo, "method_name": metodo_, "is_generic": "false",
                  "instance_name": instancia})


def prop_get(tipo, instancia, prop):
    return block("component_set_get", field("COMPONENT_SELECTOR", instancia) + field("PROP", prop),
                 {"component_type": tipo, "set_or_get": "get", "property_name": prop,
                  "is_generic": "false", "instance_name": instancia})


def prop_set(tipo, instancia, prop, valor):
    return block("component_set_get",
                 field("COMPONENT_SELECTOR", instancia) + field("PROP", prop) + value("VALUE", valor),
                 {"component_type": tipo, "set_or_get": "set", "property_name": prop,
                  "is_generic": "false", "instance_name": instancia})


def aviso(mensaje):
    return metodo("Notifier", "NotificadorTarea", "ShowAlert", texto(mensaje))


# --- El programa ------------------------------------------------------------
TAREAS = "tareas"
INDICE = "indiceSeleccionado"

bloques = [
    # Variables globales
    global_var(TAREAS, lista_vacia(), (20, 20)),
    global_var(INDICE, block("math_number", field("NUM", "0")), (20, 80)),

    # Al abrir la app: cargar lo guardado
    evento("Form", "Screen1", "Initialize", [
        poner(TAREAS, metodo("TinyDB", "TinyDB1", "GetValue", texto("tareas"), lista_vacia())),
        llamar("mostrarTareas"),
    ], (20, 150)),

    # Boton Agregar
    evento("Button", "BotonAgregar", "Click", [
        local("nuevaTarea", recortar(prop_get("TextBox", "CajaTarea", "Text")),
              si((texto_vacio(obtener_local("nuevaTarea")),
                  [aviso("Primero escribe una tarea")]),
                 (esta_en_lista(obtener_local("nuevaTarea"), obtener(TAREAS)),
                  [aviso("Esa tarea ya está en la lista")]),
                 sino=[
                     agregar_a_lista(obtener(TAREAS), obtener_local("nuevaTarea")),
                     prop_set("TextBox", "CajaTarea", "Text", texto("")),
                     llamar("guardarTareas"),
                     llamar("mostrarTareas"),
                 ])),
    ], (20, 290)),

    # Tocar una tarea de la lista
    evento("ListView", "ListaTareas", "AfterPicking", [
        poner(INDICE, prop_get("ListView", "ListaTareas", "SelectionIndex")),
        metodo("Notifier", "NotificadorTarea", "ShowChooseDialog",
               unir(texto("¿Ya terminaste \""), prop_get("ListView", "ListaTareas", "Selection"),
                    texto("\"?")),
               texto("Tarea"), texto("Eliminar"), texto("Cancelar"), falso()),
    ], (20, 620)),

    # Respuesta a "¿Ya terminaste...?"
    evento("Notifier", "NotificadorTarea", "AfterChoosing", [
        si((texto_igual(obtener_param("choice"), texto("Eliminar")), [
            quitar_de_lista(obtener(TAREAS), obtener(INDICE)),
            llamar("guardarTareas"),
            llamar("mostrarTareas"),
        ])),
    ], (20, 800)),

    # Boton Borrar todo
    evento("Button", "BotonBorrarTodo", "Click", [
        si((lista_esta_vacia(obtener(TAREAS)), [aviso("No hay tareas para borrar")]),
           sino=[metodo("Notifier", "NotificadorTodo", "ShowChooseDialog",
                        texto("¿Seguro que quieres borrar TODAS las tareas?"),
                        texto("Borrar todo"), texto("Sí, borrar"), texto("No"), falso())]),
    ], (620, 20)),

    # Respuesta a "¿Seguro que quieres borrar todo?"
    evento("Notifier", "NotificadorTodo", "AfterChoosing", [
        si((texto_igual(obtener_param("choice"), texto("Sí, borrar")), [
            poner(TAREAS, lista_vacia()),
            llamar("guardarTareas"),
            llamar("mostrarTareas"),
        ])),
    ], (620, 200)),

    # Procedimiento: guardar la lista en el telefono
    procedimiento("guardarTareas", [
        metodo("TinyDB", "TinyDB1", "StoreValue", texto("tareas"), obtener(TAREAS)),
    ], (620, 380)),

    # Procedimiento: mostrar la lista y el contador en pantalla
    procedimiento("mostrarTareas", [
        prop_set("ListView", "ListaTareas", "Elements", obtener(TAREAS)),
        si((lista_esta_vacia(obtener(TAREAS)),
            [prop_set("Label", "EtiquetaContador", "Text", texto("¡No tienes tareas pendientes!"))]),
           sino=[prop_set("Label", "EtiquetaContador", "Text",
                          unir(texto("Tareas pendientes: "), largo_lista(obtener(TAREAS))))]),
    ], (620, 470)),
]

bky = ('<xml xmlns="https://developers.google.com/blockly/xml">'
       + "".join(bloques)
       + f'<yacodeblocks ya-version="{YA_VERSION}" language-version="{BLOCKS_LANGUAGE_VERSION}">'
       + "</yacodeblocks></xml>")

propiedades = f"""main=appinventor.{USUARIO}.{PROYECTO}.Screen1
name={PROYECTO}
assets=../assets
source=../src
build=../build
versioncode=1
versionname=1.0
useslocation=False
aname={PROYECTO}
sizing=Responsive
showlistsasjson=True
tutorialurl=
subsetjson=
actionbar=True
theme=AppTheme.Light.DarkActionBar
color.primary=&HFF3F51B5
color.primary.dark=&HFF303F9F
color.accent=&HFFFF4081
defaultfilescope=App
"""

# ---------------------------------------------------------------------------
# 3. Escribir los archivos y el .aia
# ---------------------------------------------------------------------------
archivos = {
    "youngandroidproject/project.properties": propiedades,
    f"src/{PAQUETE}/Screen1.scm": scm,
    f"src/{PAQUETE}/Screen1.bky": bky,
}

for ruta, contenido in archivos.items():
    destino = os.path.join(AQUI, "proyecto", ruta)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(contenido)

with zipfile.ZipFile(os.path.join(AQUI, f"{PROYECTO}.aia"), "w", zipfile.ZIP_DEFLATED) as z:
    for ruta, contenido in archivos.items():
        z.writestr(ruta, contenido)

print(f"Listo: {PROYECTO}.aia ({len(bloques)} grupos de bloques)")
