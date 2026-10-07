# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   MÓDULO CATÁLOGOS  —  Extra Dark Premium  v1.0                            ║
║   Catálogo de Materiales · Trabajadores · Proveedores · Clientes           ║
║   Paleta y patrones idénticos a modulo_fichas_tecnicas.py                  ║
║                                                                            ║
║   ARQUITECTURA DE MIGRACIÓN LIMPIA:                                        ║
║   ─────────────────────────────────────────────────────────────────────── ║
║   • DB propia: catalogos_db.sqlite  (NO toca fichas_tecnicas_db.sqlite)   ║
║   • fichas_tecnicas.py NO se modifica en esta fase                         ║
║   • Conexión con FichasMixin: solo LECTURA de nombres para autocomplete    ║
║   • Escritura bidireccional: Fase 2 (cuando catálogo esté estable)         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json, os, datetime, sqlite3, threading

import customtkinter as ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Escalado adaptativo — idéntico a fichas técnicas ────────────────────────
def _calcular_escala():
    try:
        import tkinter as _tk
        _r = _tk.Tk(); _r.withdraw()
        _sw = _r.winfo_screenwidth()
        _sh = _r.winfo_screenheight()
        _r.destroy()
    except Exception:
        return 1.0, 1.0, 11
    if _sw <= 1280 or _sh <= 800:    return 1.25, 1.10, 20
    elif _sw <= 1600 or _sh <= 1024: return 1.30, 1.15, 22
    elif _sw <= 1920 or _sh <= 1080: return 1.40, 1.20, 24
    else:                             return 1.55, 1.30, 28

_WIDGET_SCALE, _WINDOW_SCALE, _BASE_FONT_SIZE = _calcular_escala()
try:
    ctk.set_widget_scaling(_WIDGET_SCALE)
    ctk.set_window_scaling(_WINDOW_SCALE)
except Exception:
    pass

_FS  = _BASE_FONT_SIZE
_FT  = "Segoe UI"
_FTM = "Consolas"

# ── Paleta Extra Dark Premium — idéntica a fichas_tecnicas ──────────────────
_BG      = "#050505"
_BG2     = "#0a0a0a"
_BG3     = "#141414"
_CARD    = "#0f1318"
_CARD2   = "#141414"
_BORDER  = "#2a2a2a"
_BDR     = "#2a2a2a"
_TXT     = "#f2f2f2"
_TXT2    = "#a0a0a0"
_MUT     = "#666666"
_RED     = "#ef4444"
_RED_BG  = "#1a0a0a"
_AMB     = "#f59e0b"
_AMB_BG  = "#1a1000"
_GRN     = "#22c55e"
_GRN_BG  = "#0a1a0a"
_CYAN    = "#38bdf8"
_PURP    = "#a78bfa"
_TEAL    = "#2dd4bf"
_GOLD    = "#d4a017"
_ROSE    = "#f43f5e"
_ROSE_BG = "#1a0a0f"
_INDIGO  = "#6366f1"
_IND_BG  = "#0a0a1a"

# ── Colores por catálogo — cada uno con su identidad visual ─────────────────
CAT_CONFIG = {
    "materiales": {
        "label":   "MATERIALES",
        "acento":  _TEAL,
        "acento2": "#1a3a3a",
        "icono":   "◈",
        "desc":    "Insumos, pieles, suelas, hilos y consumibles",
    },
    "trabajadores": {
        "label":   "TRABAJADORES",
        "acento":  _PURP,
        "acento2": "#1a0a3a",
        "icono":   "◉",
        "desc":    "Personal de planta, costureras, cortadores y operativos",
    },
    "proveedores": {
        "label":   "PROVEEDORES",
        "acento":  _AMB,
        "acento2": "#1a1000",
        "icono":   "◆",
        "desc":    "Empresas y personas que surten materiales al negocio",
    },
    "clientes": {
        "label":   "CLIENTES",
        "acento":  _ROSE,
        "acento2": "#1a0a10",
        "icono":   "◎",
        "desc":    "Tiendas, distribuidores y compradores directos",
    },
}

# ── Campos por catálogo (nombre_interno, etiqueta, tipo, opciones) ───────────
# tipo: "text" | "combo" | "num" | "area"
CAMPOS = {
    "materiales": [
        ("nombre",          "NOMBRE DEL MATERIAL",   "text",  None),
        ("tipo_material",   "TIPO",                  "combo", ["DIRECTO", "INDIRECTO"]),
        ("es_principal",    "MATERIAL PRINCIPAL",    "combo", ["NO", "SÍ"]),
        ("unidad_default",  "UNIDAD POR DEFECTO",    "combo", ["dm", "m", "cm", "par", "pza",
                                                                "kg", "g", "ml", "lt", "mts",
                                                                "rollo", "caja", "par/dna"]),
        ("departamento",    "DEPARTAMENTO",          "combo", ["CORTE", "PESPUNTE", "MONTADO",
                                                                "ADORNO", "EMBARQUE", "GENERAL"]),
        ("visible_monitor", "VER EN MONITOR",        "combo", ["SÍ", "NO"]),
        ("proveedor_ref",   "PROVEEDOR REFERENCIA",  "text",  None),
        ("costo_ref",       "COSTO REFERENCIA",      "num",   None),
        ("notas",           "NOTAS",                 "area",  None),
    ],
    "trabajadores": [
        ("nombre",              "NOMBRE COMPLETO",        "text",  None),
        ("puesto",              "PUESTO",                 "combo", ["CORTADOR", "COSTURERA", "MONTADOR",
                                                                     "ADORNADOR", "EMBARCADOR",
                                                                     "SUPERVISOR", "ADMINISTRATIVO",
                                                                     "OTRO"]),
        ("departamento",        "DEPARTAMENTO",           "combo", ["CORTE", "PESPUNTE", "MONTADO",
                                                                     "ADORNO", "EMBARQUE", "GENERAL",
                                                                     "ADMINISTRATIVO"]),
        ("tipo_pago",           "TIPO DE PAGO",           "combo", ["POR PAR", "SEMANAL FIJO",
                                                                     "DESTAJO", "OTRO"]),
        ("sueldo_semanal",      "SUELDO SEMANAL ($)",     "num",   None),
        ("cuota_minima_pares",  "CUOTA MIN. PARES/SEMANA","num",   None),
        ("telefono",            "TELEFONO",               "text",  None),
        ("curp",                "CURP",                   "text",  None),
        ("fecha_ingreso",       "FECHA DE INGRESO",       "text",  None),
        ("estatus",             "ESTATUS",                "combo", ["ACTIVO", "INACTIVO", "BAJA"]),
        ("notas",               "NOTAS",                  "area",  None),
    ],
    "proveedores": [
        ("nombre",          "NOMBRE / RAZÓN SOCIAL", "text",  None),
        ("contacto",        "NOMBRE DE CONTACTO",    "text",  None),
        ("telefono",        "TELÉFONO",              "text",  None),
        ("email",           "EMAIL",                 "text",  None),
        ("direccion",       "DIRECCIÓN",             "area",  None),
        ("rfc",             "RFC",                   "text",  None),
        ("dias_credito",    "DÍAS DE CRÉDITO",       "num",   None),
        ("materiales_surte","MATERIALES QUE SURTE",  "area",  None),
        ("estatus",         "ESTATUS",               "combo", ["ACTIVO", "INACTIVO",
                                                                "BLOQUEADO"]),
        ("notas",           "NOTAS",                 "area",  None),
    ],
    "clientes": [
        ("nombre",          "NOMBRE / RAZÓN SOCIAL", "text",  None),
        ("contacto",        "NOMBRE DE CONTACTO",    "text",  None),
        ("telefono",        "TELÉFONO",              "text",  None),
        ("email",           "EMAIL",                 "text",  None),
        ("direccion",       "DIRECCIÓN",             "area",  None),
        ("rfc",             "RFC",                   "text",  None),
        ("tipo_cliente",    "TIPO DE CLIENTE",       "combo", ["TIENDA", "DISTRIBUIDOR",
                                                                "DIRECTO", "EXPORTACIÓN",
                                                                "OTRO"]),
        ("dias_credito",    "DÍAS DE CRÉDITO",       "num",   None),
        ("limite_credito",  "LÍMITE DE CRÉDITO",     "num",   None),
        ("estatus",         "ESTATUS",               "combo", ["ACTIVO", "INACTIVO",
                                                                "BLOQUEADO"]),
        ("notas",           "NOTAS",                 "area",  None),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# CAPA DE DATOS — SQLite
# Una tabla por catálogo, campos en JSON para máxima flexibilidad futura.
# ════════════════════════════════════════════════════════════════════════════
import os as _os_cat
CAT_DB_PATH = _os_cat.path.join(
    _os_cat.path.dirname(_os_cat.path.abspath(__file__)),
    "catalogos_db.sqlite"
)

def cat_init_db():
    """
    Inicializa la DB de catálogos.
    Una tabla genérica por catálogo: id, datos_json, fecha_alta, fecha_mod.
    Esto permite agregar campos sin ALTER TABLE.
    """
    con = sqlite3.connect(CAT_DB_PATH)
    cur = con.cursor()
    for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {tabla} (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre     TEXT NOT NULL,
                datos_json TEXT NOT NULL,
                estatus    TEXT DEFAULT 'ACTIVO',
                fecha_alta TEXT NOT NULL,
                fecha_mod  TEXT NOT NULL
            )
        """)
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{tabla}_nombre
            ON {tabla}(nombre)
        """)
    # ── Tabla relación Proveedor ↔ Material ───────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS proveedor_materiales (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_nombre TEXT NOT NULL,
            material_nombre  TEXT NOT NULL,
            prioridad        INTEGER DEFAULT 1,
            precio_ref       REAL    DEFAULT 0.0,
            unidad           TEXT    DEFAULT '',
            notas            TEXT    DEFAULT '',
            fecha_alta       TEXT    NOT NULL,
            fecha_mod        TEXT    NOT NULL,
            UNIQUE(proveedor_nombre, material_nombre)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pm_proveedor ON proveedor_materiales(proveedor_nombre)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pm_material  ON proveedor_materiales(material_nombre)")
    con.commit()
    con.close()

def cat_guardar(tabla: str, datos: dict, registro_id: int = None):
    """
    INSERT o UPDATE según si viene registro_id.
    Retorna (True, id) o (False, mensaje_error).
    """
    nombre = datos.get("nombre", "").strip().upper()
    if not nombre:
        return False, "El campo NOMBRE es obligatorio."
    estatus = datos.get("estatus", "ACTIVO").upper()
    hoy = datetime.date.today().isoformat()
    # ── Forzar mayúsculas en todos los campos de texto ──────────────────────
    datos_upper = {}
    for k, v in datos.items():
        if isinstance(v, str):
            datos_upper[k] = v.strip().upper()
        else:
            datos_upper[k] = v
    datos = datos_upper
    datos_json = json.dumps(datos, ensure_ascii=False)

    con = sqlite3.connect(CAT_DB_PATH)
    cur = con.cursor()
    try:
        if registro_id:
            cur.execute(f"""
                UPDATE {tabla}
                SET nombre=?, datos_json=?, estatus=?, fecha_mod=?
                WHERE id=?
            """, (nombre, datos_json, estatus, hoy, registro_id))
            con.commit()
            return True, registro_id
        else:
            # Verificar duplicado de nombre
            cur.execute(f"SELECT id FROM {tabla} WHERE nombre=?", (nombre,))
            dup = cur.fetchone()
            if dup:
                return False, f"Ya existe un registro con el nombre:\n{nombre}"
            cur.execute(f"""
                INSERT INTO {tabla} (nombre, datos_json, estatus, fecha_alta, fecha_mod)
                VALUES (?,?,?,?,?)
            """, (nombre, datos_json, estatus, hoy, hoy))
            con.commit()
            return True, cur.lastrowid
    except Exception as e:
        return False, str(e)
    finally:
        con.close()

def cat_eliminar(tabla: str, registro_id: int):
    con = sqlite3.connect(CAT_DB_PATH)
    con.execute(f"DELETE FROM {tabla} WHERE id=?", (registro_id,))
    con.commit()
    con.close()

def cat_buscar(tabla: str, texto: str = "", estatus: str = "TODOS"):
    """Busca por nombre o cualquier campo en datos_json."""
    con = sqlite3.connect(CAT_DB_PATH)
    cur = con.cursor()
    txt = texto.strip().upper()
    if not txt:
        # Performance optimization: bypass costly LIKE operations on datos_json when search string is empty
        if estatus == "TODOS":
            cur.execute(f"""
                SELECT id, nombre, datos_json, estatus, fecha_alta, fecha_mod
                FROM {tabla}
                ORDER BY nombre ASC
            """)
        else:
            cur.execute(f"""
                SELECT id, nombre, datos_json, estatus, fecha_alta, fecha_mod
                FROM {tabla}
                WHERE estatus=?
                ORDER BY nombre ASC
            """, (estatus.upper(),))
    else:
        like = f"%{txt}%"
        if estatus == "TODOS":
            cur.execute(f"""
                SELECT id, nombre, datos_json, estatus, fecha_alta, fecha_mod
                FROM {tabla}
                WHERE nombre LIKE ? OR datos_json LIKE ?
                ORDER BY nombre ASC
            """, (like, like))
        else:
            cur.execute(f"""
                SELECT id, nombre, datos_json, estatus, fecha_alta, fecha_mod
                FROM {tabla}
                WHERE (nombre LIKE ? OR datos_json LIKE ?)
                AND estatus=?
                ORDER BY nombre ASC
            """, (like, like, estatus.upper()))
    rows = cur.fetchall()
    con.close()
    return rows

def cat_get_by_id(tabla: str, registro_id: int):
    con = sqlite3.connect(CAT_DB_PATH)
    cur = con.cursor()
    cur.execute(f"""
        SELECT id, nombre, datos_json, estatus, fecha_alta, fecha_mod
        FROM {tabla} WHERE id=?
    """, (registro_id,))
    row = cur.fetchone()
    con.close()
    return row

def cat_stats(tabla: str):
    """Retorna dict con conteo por estatus."""
    con = sqlite3.connect(CAT_DB_PATH)
    cur = con.cursor()
    cur.execute(f"SELECT estatus, COUNT(*) FROM {tabla} GROUP BY estatus")
    rows = cur.fetchall()
    con.close()
    return {r[0]: r[1] for r in rows}

# ════════════════════════════════════════════════════════════════════════════
# CAPA BD — Relación Proveedor ↔ Material
# ════════════════════════════════════════════════════════════════════════════

def pm_listar(proveedor_nombre: str) -> list:
    """Retorna lista de dicts con todos los materiales de un proveedor, ordenados por prioridad."""
    try:
        con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
        cur.execute("""
            SELECT id, material_nombre, prioridad, precio_ref, unidad, notas
            FROM   proveedor_materiales
            WHERE  proveedor_nombre=?
            ORDER  BY prioridad ASC, material_nombre ASC
        """, (proveedor_nombre.strip().upper(),))
        rows = cur.fetchall(); con.close()
        return [{"id": r[0], "material": r[1], "prioridad": r[2],
                 "precio_ref": r[3], "unidad": r[4], "notas": r[5]} for r in rows]
    except Exception:
        return []

def pm_guardar(proveedor_nombre: str, material_nombre: str,
               prioridad: int = 1, precio_ref: float = 0.0,
               unidad: str = "", notas: str = "",
               registro_id: int = None) -> tuple:
    """INSERT o UPDATE de una relación proveedor-material. Retorna (True, id) o (False, msg)."""
    hoy = datetime.date.today().isoformat()
    pnm = proveedor_nombre.strip().upper()
    mnm = material_nombre.strip().upper()
    if not pnm or not mnm:
        return False, "Proveedor y material son obligatorios."
    try:
        con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
        if registro_id:
            cur.execute("""
                UPDATE proveedor_materiales
                SET material_nombre=?, prioridad=?, precio_ref=?,
                    unidad=?, notas=?, fecha_mod=?
                WHERE id=?
            """, (mnm, prioridad, precio_ref, unidad.upper(), notas.upper(), hoy, registro_id))
            con.commit(); con.close()
            return True, registro_id
        else:
            cur.execute("""
                INSERT INTO proveedor_materiales
                    (proveedor_nombre, material_nombre, prioridad, precio_ref, unidad, notas, fecha_alta, fecha_mod)
                VALUES (?,?,?,?,?,?,?,?)
            """, (pnm, mnm, prioridad, precio_ref, unidad.upper(), notas.upper(), hoy, hoy))
            new_id = cur.lastrowid
            con.commit(); con.close()
            return True, new_id
    except sqlite3.IntegrityError:
        try: con.close()
        except Exception: pass
        return False, f"El material '{mnm}' ya está asignado a este proveedor."
    except Exception as e:
        return False, str(e)

def pm_eliminar(registro_id: int):
    """Elimina una relación por id."""
    try:
        con = sqlite3.connect(CAT_DB_PATH)
        con.execute("DELETE FROM proveedor_materiales WHERE id=?", (registro_id,))
        con.commit(); con.close()
        return True
    except Exception:
        return False

def pm_conteo(proveedor_nombre: str) -> int:
    """Número de materiales asignados a un proveedor."""
    try:
        con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM proveedor_materiales WHERE proveedor_nombre=?",
                    (proveedor_nombre.strip().upper(),))
        n = cur.fetchone()[0]; con.close()
        return n
    except Exception:
        return 0

# ════════════════════════════════════════════════════════════════════════════
# API PÚBLICA — consumida por modulo_compras.py (Fase 2)
# ════════════════════════════════════════════════════════════════════════════

def cat_get_proveedor_de_material(material_nombre: str) -> dict:
    """
    Retorna el proveedor PRINCIPAL (prioridad=1) asignado a este material.
    Retorna {} si no hay relación registrada.
    Uso en compras: asignación automática al cargar programa al carrito.
    """
    try:
        con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
        cur.execute("""
            SELECT proveedor_nombre, prioridad, precio_ref, unidad
            FROM   proveedor_materiales
            WHERE  material_nombre=?
            ORDER  BY prioridad ASC LIMIT 1
        """, (material_nombre.strip().upper(),))
        r = cur.fetchone(); con.close()
        if r:
            return {"proveedor": r[0], "prioridad": r[1],
                    "precio_ref": r[2], "unidad": r[3]}
    except Exception:
        pass
    return {}

def cat_get_todos_proveedores_de_material(material_nombre: str) -> list:
    """
    Retorna TODOS los proveedores de un material ordenados por prioridad.
    Útil para mostrar alternativas (principal + respaldo).
    """
    try:
        con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
        cur.execute("""
            SELECT proveedor_nombre, prioridad, precio_ref, unidad
            FROM   proveedor_materiales
            WHERE  material_nombre=?
            ORDER  BY prioridad ASC
        """, (material_nombre.strip().upper(),))
        rows = cur.fetchall(); con.close()
        return [{"proveedor": r[0], "prioridad": r[1],
                 "precio_ref": r[2], "unidad": r[3]} for r in rows]
    except Exception:
        return []

def cat_get_materiales_por_proveedor(proveedor_nombre: str) -> list:
    """
    Retorna todos los materiales de un proveedor con su prioridad y precio.
    Uso en compras: para saber qué materiales puede surtir cada proveedor.
    """
    return pm_listar(proveedor_nombre)

def cat_get_mapa_material_proveedor() -> dict:
    """
    Retorna dict {material_nombre: proveedor_nombre} con el proveedor
    PRINCIPAL de cada material. Uso en compras para asignación masiva.
    """
    try:
        con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
        cur.execute("""
            SELECT material_nombre, proveedor_nombre
            FROM   proveedor_materiales
            WHERE  prioridad=1
            ORDER  BY material_nombre
        """)
        rows = cur.fetchall(); con.close()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


# ── Lectura de fichas técnicas para poblar materiales existentes ─────────────
def cat_importar_materiales_de_fichas():
    """
    Lee fichas_tecnicas_db.sqlite y extrae nombres únicos de materiales.
    NO modifica nada — solo lectura para sugerir importación.
    Retorna lista de dicts con campos pre-llenados.
    """
    ft_db = "fichas_tecnicas_db.sqlite"
    if not os.path.exists(ft_db):
        return []
    try:
        con = sqlite3.connect(ft_db)
        cur = con.cursor()
        cur.execute("SELECT materiales FROM fichas")
        rows = cur.fetchall()
        con.close()
    except Exception:
        return []

    vistos = {}
    for (mats_json,) in rows:
        try:
            mats = json.loads(mats_json) if mats_json else []
            for m in mats:
                nm = m.get("nombre", "").strip().upper()
                if nm and nm not in vistos:
                    vistos[nm] = {
                        "nombre":          nm,
                        "tipo_material":   m.get("tipo_material", "DIRECTO"),
                        "es_principal":    "SÍ" if m.get("principal", False) else "NO",
                        "unidad_default":  m.get("unidad", "dm"),
                        "departamento":    m.get("departamento", "CORTE"),
                        "visible_monitor": "SÍ" if m.get("visible_monitor", True) else "NO",
                        "proveedor_ref":   "",
                        "costo_ref":       "",
                        "notas":           "IMPORTADO DE FICHAS TÉCNICAS",
                        "estatus":         "ACTIVO",
                    }
        except Exception:
            continue
    return list(vistos.values())


# ════════════════════════════════════════════════════════════════════════════
# TARJETA DE REGISTRO — patrón idéntico a FT_Tarjeta
# ════════════════════════════════════════════════════════════════════════════
class CAT_Tarjeta(ctk.CTkFrame):
    def __init__(self, parent, tabla, fila, acento, on_refresh,
                 on_editar=None, **kw):
        fid, nombre, datos_json, estatus, fecha_alta, fecha_mod = fila
        datos = {}
        try:
            datos = json.loads(datos_json)
        except Exception:
            pass

        # Color de borde según estatus
        if estatus == "ACTIVO":
            bdr_col = acento
        elif estatus == "INACTIVO":
            bdr_col = _MUT
        else:
            bdr_col = _RED

        super().__init__(parent,
                         fg_color=_CARD,
                         border_width=2,
                         border_color=bdr_col,
                         corner_radius=12, **kw)

        self.tabla      = tabla
        self.fila       = fila
        self.acento     = acento
        self.on_refresh = on_refresh
        self.on_editar  = on_editar
        self._construir(datos, estatus, fecha_alta, bdr_col)

    def _construir(self, datos, estatus, fecha_alta, bdr_col):
        fid, nombre, datos_json, *_ = self.fila

        # ── [1] Franja superior 2px ───────────────────────────────────────────
        ctk.CTkFrame(self, fg_color=self.acento, height=2,
                     corner_radius=0).pack(fill="x")

        # ── [2] Nombre + botones ─────────────────────────────────────────────
        f_hdr = ctk.CTkFrame(self, fg_color="transparent")
        f_hdr.pack(fill="x", padx=10, pady=(5, 0))

        ctk.CTkLabel(f_hdr, text=nombre,
                     fg_color="transparent", text_color=self.acento,
                     font=(_FTM, max(9, _FS - 3), "bold"),
                     anchor="w").pack(side="left", fill="x", expand=True)

        f_btns = ctk.CTkFrame(f_hdr, fg_color="transparent")
        f_btns.pack(side="right", padx=(4, 0))

        ctk.CTkButton(f_btns, text="EDT", width=36, height=22,
                      fg_color=_AMB_BG, hover_color="#2a1800",
                      text_color=_AMB,
                      font=(_FTM, max(9, _FS - 4)),
                      border_width=1, border_color=_AMB,
                      corner_radius=4,
                      command=lambda: self.on_editar(self.fila) if self.on_editar else None
                      ).pack(side="left", padx=(0, 2))

        ctk.CTkButton(f_btns, text="✕", width=28, height=22,
                      fg_color=_RED_BG, hover_color="#2a0a0a",
                      text_color=_RED,
                      font=(_FTM, max(9, _FS - 4)),
                      border_width=1, border_color=_RED,
                      corner_radius=4,
                      command=self._eliminar
                      ).pack(side="left")

        # ── [3] Metadata en una línea horizontal ──────────────────────────────
        campos_tabla = CAMPOS.get(self.tabla, [])
        meta_campos  = [c for c in campos_tabla
                        if c[0] not in ("nombre", "notas", "direccion",
                                        "materiales_surte")][:3]
        partes = []
        for campo_key, _, _, _ in meta_campos:
            val = datos.get(campo_key, "")
            if val:
                partes.append(str(val))
        if partes:
            ctk.CTkLabel(self, text="  ·  ".join(partes),
                         fg_color="transparent", text_color=_TXT2,
                         font=(_FT, max(8, _FS - 5)),
                         anchor="w").pack(fill="x", padx=10, pady=(1, 0))

        # ── [4] Pie: badge + fecha ────────────────────────────────────────────
        col_est = {"ACTIVO": _GRN, "INACTIVO": _MUT,
                   "BAJA": _RED, "BLOQUEADO": _RED}.get(estatus, _TXT2)
        bg_est  = {"ACTIVO": _GRN_BG, "INACTIVO": _BG3,
                   "BAJA": _RED_BG, "BLOQUEADO": _RED_BG}.get(estatus, _BG3)

        f_pie = ctk.CTkFrame(self, fg_color="transparent")
        f_pie.pack(fill="x", padx=10, pady=(3, 5))

        ctk.CTkLabel(f_pie, text=f" {estatus} ",
                     fg_color=bg_est, text_color=col_est,
                     font=(_FTM, max(7, _FS - 7), "bold"),
                     corner_radius=3).pack(side="left")

        fecha_corta = fecha_alta[5:] if fecha_alta else ""
        ctk.CTkLabel(f_pie, text=fecha_corta,
                     fg_color="transparent", text_color=_MUT,
                     font=(_FTM, max(7, _FS - 7))).pack(side="right")

    def _eliminar(self):
        fid, nombre, *_ = self.fila
        if messagebox.askyesno("Eliminar",
                               f"¿Eliminar registro:\n{nombre}?",
                               parent=self.winfo_toplevel()):
            cat_eliminar(self.tabla, fid)
            self.on_refresh()


# ════════════════════════════════════════════════════════════════════════════
# PANEL DE FORMULARIO — genérico, se adapta por catálogo
# ════════════════════════════════════════════════════════════════════════════
class CAT_PanelFormulario(ctk.CTkFrame):
    def __init__(self, parent, tabla, acento, on_save,
                 on_proveedor_activo=None, **kw):
        super().__init__(parent, fg_color=_CARD,
                         border_width=1, border_color=_BDR,
                         corner_radius=12, **kw)
        self.tabla                = tabla
        self.acento               = acento
        self.on_save              = on_save
        self.on_proveedor_activo  = on_proveedor_activo  # callback → panel PM
        self._edit_id             = None
        self._vars                = {}
        self._widgets             = {}
        self._construir()

    def _construir(self):
        cfg = CAT_CONFIG[self.tabla]

        # Franja acento
        ctk.CTkFrame(self, fg_color=self.acento, height=3,
                     corner_radius=0).pack(fill="x")

        # Header
        f_hdr = ctk.CTkFrame(self, fg_color=_BG2, corner_radius=0)
        f_hdr.pack(fill="x")
        f_hdr_in = ctk.CTkFrame(f_hdr, fg_color="transparent")
        f_hdr_in.pack(fill="x", padx=14, pady=(10, 8))
        self._lbl_modo = ctk.CTkLabel(
            f_hdr_in,
            text=f"NUEVO  {cfg['label']}",
            fg_color="transparent", text_color=_TXT,
            font=(_FTM, _FS - 2, "bold"))
        self._lbl_modo.pack(side="left")
        ctk.CTkFrame(f_hdr, fg_color=_BDR, height=1,
                     corner_radius=0).pack(fill="x")

        # Pie fijo (declarado antes para pack side=bottom)
        f_pie = ctk.CTkFrame(self, fg_color=_BG2, corner_radius=0)
        f_pie.pack(side="bottom", fill="x")
        ctk.CTkFrame(f_pie, fg_color=_BDR, height=1,
                     corner_radius=0).pack(fill="x")
        f_pie_in = ctk.CTkFrame(f_pie, fg_color="transparent")
        f_pie_in.pack(fill="x", padx=14, pady=10)

        self._btn_guardar = ctk.CTkButton(
            f_pie_in,
            text=f"◈  GUARDAR  {cfg['label']}",
            command=self._guardar,
            fg_color="#1a3a6a", hover_color="#1e4d8a",
            text_color=self.acento,
            font=(_FTM, _FS - 2, "bold"),
            corner_radius=8, height=42,
            border_width=1, border_color=self.acento)
        self._btn_guardar.pack(fill="x", pady=(0, 6))

        ctk.CTkButton(f_pie_in, text="↺  Limpiar formulario",
                      command=self.limpiar,
                      fg_color=_BG3, hover_color=_CARD2,
                      text_color=_TXT2,
                      font=(_FT, _FS - 4, "bold"),
                      corner_radius=8, height=32).pack(fill="x")

        # ── Área scrollable de campos ─────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=_BDR,
            scrollbar_button_hover_color=_MUT)
        self._scroll.pack(fill="both", expand=True, padx=0, pady=0)

        PAD = 14

        for campo_key, campo_label, campo_tipo, opciones in CAMPOS.get(self.tabla, []):
            # Etiqueta
            ctk.CTkLabel(self._scroll, text=campo_label,
                         fg_color="transparent", text_color=_MUT,
                         font=(_FT, max(9, _FS - 3), "bold"),
                         anchor="w").pack(anchor="w", padx=PAD, pady=(8, 2))

            var = tk.StringVar()
            self._vars[campo_key] = var

            if campo_tipo == "text":
                w = ctk.CTkEntry(
                    self._scroll, textvariable=var,
                    fg_color=_BG3, text_color=_TXT,
                    border_color=_BDR, border_width=1,
                    font=(_FT, max(10, _FS - 2)), height=36,
                    corner_radius=6)
                w.pack(fill="x", padx=PAD, pady=(0, 2))
                self._widgets[campo_key] = w
                # Forzar mayúsculas en tiempo real
                def _mayus(name, idx, mode, _v=var):
                    val = _v.get()
                    up  = val.upper()
                    if val != up:
                        _v.set(up)
                var.trace_add("write", _mayus)

            elif campo_tipo == "combo":
                w = ctk.CTkComboBox(
                    self._scroll, variable=var,
                    values=opciones or [],
                    fg_color=_BG3, text_color=_TXT,
                    border_color=_BDR,
                    button_color=_BDR, button_hover_color=_MUT,
                    dropdown_fg_color=_CARD2, dropdown_text_color=_TXT,
                    font=(_FT, _FS - 3), height=36, corner_radius=6)
                w.pack(fill="x", padx=PAD, pady=(0, 2))
                self._widgets[campo_key] = w
                if opciones:
                    var.set(opciones[0])

            elif campo_tipo == "num":
                w = ctk.CTkEntry(
                    self._scroll, textvariable=var,
                    fg_color=_BG3, text_color=_TXT,
                    border_color=_BDR, border_width=1,
                    font=(_FTM, max(10, _FS - 2)), height=36,
                    corner_radius=6)
                w.pack(fill="x", padx=PAD, pady=(0, 2))
                self._widgets[campo_key] = w

            elif campo_tipo == "area":
                w = ctk.CTkTextbox(
                    self._scroll,
                    fg_color=_BG3, text_color=_TXT,
                    border_color=_BDR, border_width=1,
                    font=(_FT, max(9, _FS - 3)),
                    corner_radius=6, height=70)
                w.pack(fill="x", padx=PAD, pady=(0, 2))
                self._widgets[campo_key] = w

        # Espacio final
        ctk.CTkFrame(self._scroll, fg_color="transparent",
                     height=16).pack()

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _get_valor(self, campo_key, campo_tipo):
        if campo_tipo == "area":
            w = self._widgets.get(campo_key)
            raw = w.get("1.0", "end-1c").strip() if w else ""
            return raw.upper()
        return self._vars.get(campo_key, tk.StringVar()).get().strip().upper()

    def _set_valor(self, campo_key, campo_tipo, valor):
        if campo_tipo == "area":
            w = self._widgets.get(campo_key)
            if w:
                w.delete("1.0", "end")
                w.insert("1.0", str(valor))
        else:
            var = self._vars.get(campo_key)
            if var:
                var.set(str(valor))

    def cargar_para_editar(self, fila):
        fid, nombre, datos_json, estatus, fecha_alta, fecha_mod = fila
        datos = {}
        try:
            datos = json.loads(datos_json)
        except Exception:
            pass

        self._edit_id = fid
        cfg = CAT_CONFIG[self.tabla]
        self._lbl_modo.configure(text=f"✏  EDITAR: {nombre[:18]}")
        self._btn_guardar.configure(
            text="ACTUALIZAR REGISTRO",
            fg_color="#1a1000",
            text_color=self.acento,
            border_color=_BDR)

        for campo_key, _, campo_tipo, _ in CAMPOS.get(self.tabla, []):
            val = datos.get(campo_key, "")
            self._set_valor(campo_key, campo_tipo, val)

        # Notificar panel de materiales si es proveedor
        if self.tabla == "proveedores" and self.on_proveedor_activo:
            self.on_proveedor_activo(nombre)

    def limpiar(self):
        self._edit_id = None
        cfg = CAT_CONFIG[self.tabla]
        self._lbl_modo.configure(text=f"NUEVO  {cfg['label']}")
        self._btn_guardar.configure(
            text=f"◈  GUARDAR  {cfg['label']}",
            fg_color="#1a3a6a",
            text_color=self.acento,
            border_color=self.acento)

        for campo_key, _, campo_tipo, opciones in CAMPOS.get(self.tabla, []):
            default = (opciones[0] if opciones else "")
            self._set_valor(campo_key, campo_tipo, default)

    def _guardar(self):
        datos = {}
        for campo_key, campo_label, campo_tipo, _ in CAMPOS.get(self.tabla, []):
            val = self._get_valor(campo_key, campo_tipo)
            datos[campo_key] = val

        # Validación mínima: nombre obligatorio
        if not datos.get("nombre", "").strip():
            messagebox.showwarning("AVISO", "El campo NOMBRE es obligatorio.",
                                   parent=self.winfo_toplevel())
            return

        ok, resultado = cat_guardar(self.tabla, datos, self._edit_id)
        if ok:
            accion = "actualizado" if self._edit_id else "guardado"
            messagebox.showinfo("OK", f"Registro {accion} correctamente.",
                                parent=self.winfo_toplevel())
            # Notificar panel de materiales con el nombre guardado
            if self.tabla == "proveedores" and self.on_proveedor_activo:
                self.on_proveedor_activo(datos.get("nombre", ""))
            self.limpiar()
            if self.on_save:
                self.on_save()
        else:
            messagebox.showerror("Error", resultado,
                                 parent=self.winfo_toplevel())


# ════════════════════════════════════════════════════════════════════════════
# PANEL CATÁLOGO — lista de tarjetas con búsqueda y filtros
# ════════════════════════════════════════════════════════════════════════════
class CAT_PanelCatalogo(ctk.CTkFrame):
    def __init__(self, parent, tabla, acento, on_editar, **kw):
        super().__init__(parent, fg_color="transparent",
                         corner_radius=0, **kw)
        self.tabla     = tabla
        self.acento    = acento
        self.on_editar = on_editar
        self._after_id = None
        self._construir()

    def _construir(self):
        # Header catálogo
        f_hdr = ctk.CTkFrame(self, fg_color=_BG2, corner_radius=0)
        f_hdr.pack(fill="x")
        ctk.CTkFrame(f_hdr, fg_color=self.acento, height=3,
                     corner_radius=0).pack(fill="x")
        f_hdr_in = ctk.CTkFrame(f_hdr, fg_color="transparent")
        f_hdr_in.pack(fill="x", padx=14, pady=(10, 8))
        cfg = CAT_CONFIG[self.tabla]
        ctk.CTkLabel(f_hdr_in,
                     text=f"{cfg['icono']}  {cfg['label']}  —  CATÁLOGO",
                     fg_color="transparent", text_color=_TXT,
                     font=(_FTM, _FS - 2, "bold")).pack(side="left")
        ctk.CTkFrame(f_hdr, fg_color=_BDR, height=1,
                     corner_radius=0).pack(fill="x")

        # Búsqueda + filtro estatus
        f_busq = ctk.CTkFrame(self, fg_color=_BG2, corner_radius=0)
        f_busq.pack(fill="x")
        f_busq_in = ctk.CTkFrame(f_busq, fg_color="transparent")
        f_busq_in.pack(fill="x", padx=14, pady=8)

        self._var_busq = tk.StringVar()
        self._var_busq.trace("w", lambda *a: self.refrescar())
        ctk.CTkEntry(f_busq_in, textvariable=self._var_busq,
                     placeholder_text="Buscar…",
                     fg_color=_BG3, text_color=_TXT,
                     border_color=_BDR,
                     font=(_FT, _FS - 3), height=36,
                     corner_radius=8).pack(
            side="left", fill="x", expand=True, padx=(0, 10))

        self._var_estatus = tk.StringVar(value="ACTIVO")
        ctk.CTkSegmentedButton(
            f_busq_in, variable=self._var_estatus,
            values=["TODOS", "ACTIVO", "INACTIVO"],
            font=(_FTM, _FS - 5, "bold"), width=220,
            fg_color=_BG3,
            selected_color=_BG3, selected_hover_color=_CARD2,
            unselected_color=_BG3, unselected_hover_color=_CARD2,
            text_color=_TXT2, corner_radius=8,
            command=lambda v: self.refrescar()
        ).pack(side="left")

        # Contador + botón importar (solo materiales)
        f_meta = ctk.CTkFrame(self, fg_color="transparent")
        f_meta.pack(fill="x", padx=14, pady=(0, 2))

        self._lbl_count = ctk.CTkLabel(
            f_meta, text="",
            fg_color="transparent", text_color=_MUT,
            font=(_FT, _FS - 5))
        self._lbl_count.pack(side="left")

        if self.tabla == "materiales":
            ctk.CTkButton(
                f_meta,
                text="↓  Importar desde Fichas Técnicas",
                command=self._importar_de_fichas,
                fg_color=_BG3, hover_color=_CARD2,
                text_color=_TEAL,
                font=(_FT, _FS - 5, "bold"),
                corner_radius=6, height=26,
                border_width=1, border_color=_TEAL
            ).pack(side="right")

        ctk.CTkFrame(self, fg_color=_BDR, height=1,
                     corner_radius=0).pack(fill="x")

        # Grid de tarjetas — canvas scrollable
        f_outer = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        f_outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(f_outer, bg=_BG, highlightthickness=0)
        vsb = ctk.CTkScrollbar(f_outer, orientation="vertical",
                                command=self._canvas.yview,
                                button_color=_BDR,
                                button_hover_color=_MUT)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._f_grid = ctk.CTkFrame(self._canvas, fg_color=_BG, corner_radius=0)
        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._f_grid, anchor="nw")

        self._f_grid.bind("<Configure>",
                          lambda e: self._canvas.configure(
                              scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(
                              self._canvas_win, width=e.width))
        for ev, d in [("<MouseWheel>", None), ("<Button-4>", -1), ("<Button-5>", 1)]:
            if d is None:
                self._canvas.bind(ev, lambda e: self._canvas.yview_scroll(
                    int(-1 * (e.delta // 120)), "units"))
            else:
                self._canvas.bind(ev, lambda e, _d=d: self._canvas.yview_scroll(
                    _d, "units"))

        self.refrescar()

    def refrescar(self):
        # Cancelar render pendiente
        if self._after_id:
            try:
                self._f_grid.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        for w in self._f_grid.winfo_children():
            w.destroy()

        busq    = self._var_busq.get()
        estatus = self._var_estatus.get()
        filas   = cat_buscar(self.tabla, busq, estatus)
        total   = len(filas)
        self._lbl_count.configure(text=f"{total} registro(s)")

        if not filas:
            ctk.CTkLabel(self._f_grid,
                         text="— Sin registros —",
                         fg_color="transparent", text_color=_MUT,
                         font=(_FT, _FS, "italic")).pack(pady=60)
            return

        ncols = 2
        for c in range(ncols):
            self._f_grid.columnconfigure(c, weight=1, uniform="cat_col")

        PRIMER  = 8
        LOTE    = 6
        DELAY   = 25

        def _render(inicio):
            fin = min(inicio + LOTE, total)
            for idx in range(inicio, fin):
                fila = filas[idx]
                row, col = divmod(idx, ncols)
                try:
                    card = CAT_Tarjeta(
                        self._f_grid,
                        tabla=self.tabla,
                        fila=fila,
                        acento=self.acento,
                        on_refresh=self.refrescar,
                        on_editar=self.on_editar)
                    card.grid(row=row, column=col,
                              padx=8, pady=8, sticky="nsew")
                except Exception:
                    pass
            if fin < total:
                try:
                    self._after_id = self._f_grid.after(
                        DELAY, lambda i=fin: _render(i))
                except Exception:
                    for idx in range(fin, total):
                        fila = filas[idx]
                        row, col = divmod(idx, ncols)
                        try:
                            card = CAT_Tarjeta(
                                self._f_grid, self.tabla, fila,
                                self.acento, self.refrescar, self.on_editar)
                            card.grid(row=row, column=col,
                                      padx=8, pady=8, sticky="nsew")
                        except Exception:
                            pass

        # Primer lote inmediato
        for idx in range(min(PRIMER, total)):
            fila = filas[idx]
            row, col = divmod(idx, ncols)
            try:
                card = CAT_Tarjeta(
                    self._f_grid, self.tabla, fila,
                    self.acento, self.refrescar, self.on_editar)
                card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            except Exception:
                pass

        if total > PRIMER:
            try:
                self._after_id = self._f_grid.after(
                    DELAY, lambda: _render(PRIMER))
            except Exception:
                _render(PRIMER)

    def _importar_de_fichas(self):
        mats = cat_importar_materiales_de_fichas()
        if not mats:
            messagebox.showinfo("Sin datos",
                                "No se encontró fichas_tecnicas_db.sqlite\n"
                                "o no hay materiales registrados.",
                                parent=self.winfo_toplevel())
            return

        # Verificar cuáles ya existen
        existentes = {r[1] for r in cat_buscar("materiales")}
        nuevos     = [m for m in mats if m["nombre"] not in existentes]

        if not nuevos:
            messagebox.showinfo("Sin nuevos",
                                f"Todos los {len(mats)} materiales ya están\n"
                                "en el catálogo.",
                                parent=self.winfo_toplevel())
            return

        resp = messagebox.askyesno(
            "Importar materiales",
            f"Se encontraron {len(nuevos)} material(es) nuevos\n"
            f"en Fichas Técnicas.\n\n"
            f"¿Importarlos al catálogo?",
            parent=self.winfo_toplevel())
        if not resp:
            return

        importados = 0
        for m in nuevos:
            ok, _ = cat_guardar("materiales", m)
            if ok:
                importados += 1

        messagebox.showinfo("Importación completa",
                            f"Se importaron {importados} material(es) correctamente.",
                            parent=self.winfo_toplevel())
        self.refrescar()


# ════════════════════════════════════════════════════════════════════════════
# PANEL RELACIÓN PROVEEDOR ↔ MATERIAL — UI premium Dark
# ════════════════════════════════════════════════════════════════════════════
class CAT_PanelProveedorMateriales(ctk.CTkFrame):
    """
    Panel que se muestra al pie del formulario de proveedores.
    Permite asignar materiales del catálogo al proveedor activo,
    con prioridad (PRINCIPAL / RESPALDO), precio de referencia y unidad.
    """
    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=_BG2,
                         border_width=1, border_color="#1a2a1a",
                         corner_radius=10, **kw)
        self._proveedor_nombre = None
        self._edit_id          = None
        self._filas            = []
        self._construir()

    # ── Construcción UI ───────────────────────────────────────────────────────
    def _construir(self):
        # Franja acento amber
        ctk.CTkFrame(self, fg_color=_AMB, height=2,
                     corner_radius=0).pack(fill="x")

        # ── Cabecera ──────────────────────────────────────────────────────────
        f_hdr = ctk.CTkFrame(self, fg_color="#0d1200", corner_radius=0)
        f_hdr.pack(fill="x")
        f_hi = ctk.CTkFrame(f_hdr, fg_color="transparent")
        f_hi.pack(fill="x", padx=12, pady=(7, 6))
        ctk.CTkLabel(f_hi,
            text="◆  MATERIALES QUE SURTE",
            fg_color="transparent", text_color=_AMB,
            font=(_FTM, 13, "bold")).pack(side="left")
        self._lbl_conteo = ctk.CTkLabel(f_hi,
            text="",
            fg_color="#1a1a00", text_color=_AMB,
            font=(_FTM, 12, "bold"),
            corner_radius=6)
        self._lbl_conteo.pack(side="right")
        ctk.CTkFrame(f_hdr, fg_color="#1a2a00", height=1,
                     corner_radius=0).pack(fill="x")

        # ── Formulario rápido de asignación ───────────────────────────────────
        f_form = ctk.CTkFrame(self, fg_color="#080d00", corner_radius=0)
        f_form.pack(fill="x", padx=0, pady=0)
        f_form_in = ctk.CTkFrame(f_form, fg_color="transparent")
        f_form_in.pack(fill="x", padx=12, pady=8)

        # Label estado proveedor
        self._lbl_prov_activo = ctk.CTkLabel(
            f_form_in,
            text="— Selecciona un proveedor para gestionar sus materiales —",
            fg_color="transparent", text_color=_MUT,
            font=(_FT, 12, "italic"),
            anchor="w")
        self._lbl_prov_activo.pack(fill="x", pady=(0, 6))

        # Fila 1: selector material + unidad
        f_r1 = ctk.CTkFrame(f_form_in, fg_color="transparent")
        f_r1.pack(fill="x", pady=(0, 4))
        f_r1.columnconfigure(0, weight=1)
        f_r1.columnconfigure(1, weight=0)

        # Selector de material (dropdown custom)
        self._var_mat = tk.StringVar(value="")
        self._f_mat_wrap = ctk.CTkFrame(f_r1, fg_color="#0a1000",
                                         border_width=1, border_color="#1e3a00",
                                         corner_radius=6)
        self._f_mat_wrap.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        f_mat_inner = ctk.CTkFrame(self._f_mat_wrap, fg_color="transparent")
        f_mat_inner.pack(fill="x", padx=6, pady=4)
        ctk.CTkLabel(f_mat_inner, text="MATERIAL",
            fg_color="transparent", text_color="#556600",
            font=(_FTM, 11, "bold")).pack(anchor="w")

        self._f_mat_btn = tk.Frame(f_mat_inner, bg="#0a1000",
            highlightthickness=1, highlightbackground="#1e3a00")
        self._f_mat_btn.pack(fill="x", pady=(2, 0))
        self._lbl_mat_sel = tk.Label(self._f_mat_btn,
            text="— seleccionar material —",
            bg="#0a1000", fg="#334400",
            font=("Consolas", 12),
            anchor="w", padx=8, pady=5, cursor="hand2")
        self._lbl_mat_sel.pack(side="left", fill="x", expand=True)
        self._lbl_mat_arr = tk.Label(self._f_mat_btn, text=" ▼ ",
            bg="#0a1000", fg=_AMB,
            font=("Consolas", 12, "bold"),
            cursor="hand2", padx=4)
        self._lbl_mat_arr.pack(side="right")
        self._dd_mat = [None]
        for w in (self._f_mat_btn, self._lbl_mat_sel, self._lbl_mat_arr):
            w.bind("<Button-1>", self._toggle_dd_mat)

        # Unidad (campo pequeño)
        f_und = ctk.CTkFrame(f_r1, fg_color="#0a1000",
                              border_width=1, border_color="#1e3a00",
                              corner_radius=6)
        f_und.grid(row=0, column=1, sticky="ew")
        f_und_in = ctk.CTkFrame(f_und, fg_color="transparent")
        f_und_in.pack(padx=6, pady=4)
        ctk.CTkLabel(f_und_in, text="UNIDAD",
            fg_color="transparent", text_color="#556600",
            font=(_FTM, 11, "bold")).pack(anchor="w")
        self._var_und = tk.StringVar(value="")
        self._ent_und = ctk.CTkEntry(f_und_in, textvariable=self._var_und,
            fg_color="#0d1800", text_color=_TXT,
            border_color="#1e3a00", border_width=1,
            font=(_FTM, 13), height=28,
            corner_radius=4, width=72)
        self._ent_und.pack()

        # Fila 2: prioridad + precio
        f_r2 = ctk.CTkFrame(f_form_in, fg_color="transparent")
        f_r2.pack(fill="x", pady=(0, 6))
        f_r2.columnconfigure(0, weight=1)
        f_r2.columnconfigure(1, weight=1)

        # Prioridad
        f_prio = ctk.CTkFrame(f_r2, fg_color="#0a1000",
                               border_width=1, border_color="#1e3a00",
                               corner_radius=6)
        f_prio.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        f_prio_in = ctk.CTkFrame(f_prio, fg_color="transparent")
        f_prio_in.pack(fill="x", padx=6, pady=4)
        ctk.CTkLabel(f_prio_in, text="PRIORIDAD",
            fg_color="transparent", text_color="#556600",
            font=(_FTM, 11, "bold")).pack(anchor="w")
        self._var_prio = tk.StringVar(value="PRINCIPAL")
        ctk.CTkSegmentedButton(f_prio_in,
            variable=self._var_prio,
            values=["PRINCIPAL", "RESPALDO"],
            fg_color="#0d1800",
            selected_color="#1a3a00", selected_hover_color="#1e4400",
            unselected_color="#0d1800", unselected_hover_color="#111a00",
            text_color=_TXT2, text_color_disabled=_MUT,
            font=(_FTM, 11, "bold"),
            corner_radius=4, height=26
        ).pack(fill="x", pady=(2, 0))

        # Precio referencia
        f_prec = ctk.CTkFrame(f_r2, fg_color="#0a1000",
                               border_width=1, border_color="#1e3a00",
                               corner_radius=6)
        f_prec.grid(row=0, column=1, sticky="ew")
        f_prec_in = ctk.CTkFrame(f_prec, fg_color="transparent")
        f_prec_in.pack(fill="x", padx=6, pady=4)
        ctk.CTkLabel(f_prec_in, text="PRECIO REF  $",
            fg_color="transparent", text_color="#556600",
            font=(_FTM, 11, "bold")).pack(anchor="w")
        self._var_precio = tk.StringVar(value="")
        ctk.CTkEntry(f_prec_in, textvariable=self._var_precio,
            fg_color="#0d1800", text_color=_GRN,
            border_color="#1e3a00", border_width=1,
            font=(_FTM, 13), height=28,
            corner_radius=4).pack(fill="x", pady=(2, 0))

        # Botón agregar / actualizar
        self._btn_agregar = ctk.CTkButton(f_form_in,
            text="＋  AGREGAR MATERIAL",
            command=self._guardar_relacion,
            fg_color="#0d2200", hover_color="#102800",
            text_color=_AMB,
            font=(_FTM, 13, "bold"),
            corner_radius=6, height=34,
            border_width=1, border_color=_AMB)
        self._btn_agregar.pack(fill="x")

        # ── Lista de materiales asignados ─────────────────────────────────────
        ctk.CTkFrame(self, fg_color="#1a2a00", height=1,
                     corner_radius=0).pack(fill="x")

        f_lista_hdr = ctk.CTkFrame(self, fg_color="#080d00", corner_radius=0)
        f_lista_hdr.pack(fill="x")
        f_lh = ctk.CTkFrame(f_lista_hdr, fg_color="transparent")
        f_lh.pack(fill="x", padx=12, pady=4)
        for txt, w in [("MATERIAL", 12), ("UND", 4), ("PRIORIDAD", 7), ("PRECIO REF", 8), ("", 3)]:
            ctk.CTkLabel(f_lh, text=txt,
                fg_color="transparent", text_color="#556600",
                font=(_FTM, 11, "bold"),
                anchor="w", width=w*7).pack(side="left", padx=(0, 4))

        ctk.CTkFrame(self, fg_color="#1a2a00", height=1,
                     corner_radius=0).pack(fill="x")

        # Scroll de renglones
        self._f_lista_outer = ctk.CTkFrame(self, fg_color="transparent",
                                            corner_radius=0)
        self._f_lista_outer.pack(fill="both", expand=True)

        self._cv_lista = tk.Canvas(self._f_lista_outer,
            bg="#060a00", highlightthickness=0, height=180)
        sb_lista = tk.Scrollbar(self._f_lista_outer, orient="vertical",
            command=self._cv_lista.yview,
            width=14, troughcolor="#060a00", bg="#1e3a00",
            activebackground=_AMB, relief="flat", bd=0)
        self._cv_lista.configure(yscrollcommand=sb_lista.set)
        sb_lista.pack(side="right", fill="y")
        self._cv_lista.pack(side="left", fill="both", expand=True)

        self._f_rengs = tk.Frame(self._cv_lista, bg="#060a00")
        self._win_rengs = self._cv_lista.create_window(
            (0, 0), window=self._f_rengs, anchor="nw")
        self._cv_lista.bind("<Configure>",
            lambda e: self._cv_lista.itemconfig(self._win_rengs, width=e.width))
        self._f_rengs.bind("<Configure>",
            lambda e: self._cv_lista.configure(scrollregion=self._cv_lista.bbox("all")))
        # Scroll táctil
        _d = {"y": 0}
        self._cv_lista.bind("<ButtonPress-1>", lambda e: _d.update(y=e.y))
        self._cv_lista.bind("<B1-Motion>",
            lambda e: self._cv_lista.yview_scroll(int((_d["y"]-e.y)/8), "units")
                      or _d.update(y=e.y))
        self._cv_lista.bind("<Button-4>", lambda e: self._cv_lista.yview_scroll(-2, "units"))
        self._cv_lista.bind("<Button-5>", lambda e: self._cv_lista.yview_scroll( 2, "units"))

        # Placeholder vacío
        self._lbl_vacio = tk.Label(self._f_rengs,
            text="Sin materiales asignados",
            bg="#060a00", fg="#334400",
            font=("Segoe UI", 12, "italic"))
        self._lbl_vacio.pack(pady=24)

    # ── Dropdown material ─────────────────────────────────────────────────────
    def _toggle_dd_mat(self, e=None):
        if self._dd_mat[0]:
            try: self._dd_mat[0].destroy()
            except Exception: pass
            self._dd_mat[0] = None
            return
        if not self._proveedor_nombre:
            return

        self._f_mat_btn.update_idletasks()
        rx = self._f_mat_btn.winfo_rootx()
        ry = self._f_mat_btn.winfo_rooty() + self._f_mat_btn.winfo_height()
        rw = self._f_mat_btn.winfo_width()

        root = self.winfo_toplevel()
        dd = tk.Toplevel(root)
        dd.overrideredirect(True)
        dd.attributes("-topmost", True)
        dd.configure(bg="#1e3a00")
        self._dd_mat[0] = dd

        # Buscador
        f_top = tk.Frame(dd, bg="#0a1000")
        f_top.pack(fill="x", padx=1, pady=(1, 0))
        var_q = tk.StringVar()
        e_q = tk.Entry(f_top, textvariable=var_q,
            bg="#0a1000", fg=_TXT, insertbackground=_AMB,
            font=("Consolas", 13),
            relief="flat", bd=6)
        e_q.pack(fill="x")

        # Listbox
        f_lb = tk.Frame(dd, bg="#0a1000")
        f_lb.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        lb = tk.Listbox(f_lb,
            bg="#0a1000", fg=_TXT,
            selectbackground="#1a3a00", selectforeground=_AMB,
            font=("Consolas", 12),
            relief="flat", bd=0,
            highlightthickness=0, activestyle="none",
            height=10)
        sb2 = tk.Scrollbar(f_lb, orient="vertical", command=lb.yview,
            width=18, troughcolor="#0a1000", bg="#1e3a00",
            activebackground=_AMB, relief="flat", bd=0)
        lb.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True)

        # Scroll táctil listbox
        _td = {"y": 0}
        lb.bind("<ButtonPress-1>", lambda ev: _td.update(y=ev.y))
        lb.bind("<B1-Motion>",
            lambda ev: lb.yview_scroll(int((_td["y"]-ev.y)/10), "units")
                       or _td.update(y=ev.y))

        # Poblar
        mats_cat = [r[1] for r in cat_buscar("materiales", "", "ACTIVO")]

        def _poblar(q=""):
            lb.delete(0, "end")
            for m in mats_cat:
                if q.upper() in m.upper():
                    lb.insert("end", "  " + m)

        def _on_q(*_): _poblar(var_q.get())
        var_q.trace("w", _on_q)
        _poblar()

        def _sel(event=None):
            sel = lb.curselection()
            if sel:
                nm = lb.get(sel[0]).strip()
                self._var_mat.set(nm)
                self._lbl_mat_sel.config(text=nm, fg=_TXT)
                # Auto-llenar unidad desde catálogo
                datos = cat_get_material_por_nombre(nm)
                und = datos.get("unidad_default", "")
                self._var_und.set(und)
                dd.destroy(); self._dd_mat[0] = None

        lb.bind("<<ListboxSelect>>", _sel)
        lb.bind("<Double-Button-1>", _sel)
        dd.bind("<FocusOut>", lambda ev: dd.after(200,
            lambda: (dd.destroy() or None) if self._dd_mat[0] else None))
        dd.geometry(f"{max(rw, 260)}x240+{rx}+{ry}")
        e_q.focus_set()

    # ── Guardar relación ──────────────────────────────────────────────────────
    def _guardar_relacion(self):
        if not self._proveedor_nombre:
            messagebox.showwarning("Sin proveedor",
                "Guarda o selecciona un proveedor primero.",
                parent=self.winfo_toplevel()); return
        mat = self._var_mat.get().strip().upper()
        if not mat or mat == "— SELECCIONAR MATERIAL —":
            messagebox.showwarning("Sin material",
                "Selecciona un material del catálogo.",
                parent=self.winfo_toplevel()); return
        prio_txt = self._var_prio.get()
        prio = 1 if prio_txt == "PRINCIPAL" else 2
        try:
            precio = float(self._var_precio.get().replace(",", ".") or 0)
        except ValueError:
            precio = 0.0
        und = self._var_und.get().strip().upper()

        ok, res = pm_guardar(self._proveedor_nombre, mat, prio, precio, und,
                             registro_id=self._edit_id)
        if ok:
            self._edit_id = None
            self._var_mat.set("")
            self._lbl_mat_sel.config(text="— seleccionar material —", fg="#334400")
            self._var_precio.set("")
            self._var_und.set("")
            self._var_prio.set("PRINCIPAL")
            self._btn_agregar.configure(text="＋  AGREGAR MATERIAL")
            self.refrescar_lista()
        else:
            messagebox.showerror("Error", res, parent=self.winfo_toplevel())

    def _editar_fila(self, fila: dict):
        """Pre-carga el formulario para editar una relación existente."""
        self._edit_id = fila["id"]
        self._var_mat.set(fila["material"])
        self._lbl_mat_sel.config(text=fila["material"], fg=_TXT)
        self._var_und.set(fila["unidad"])
        self._var_precio.set(str(fila["precio_ref"]) if fila["precio_ref"] else "")
        self._var_prio.set("PRINCIPAL" if fila["prioridad"] == 1 else "RESPALDO")
        self._btn_agregar.configure(text="✎  ACTUALIZAR MATERIAL")

    # ── API pública ───────────────────────────────────────────────────────────
    def cargar_proveedor(self, nombre: str):
        """Llamado cuando se selecciona/guarda un proveedor. Recarga la lista."""
        self._proveedor_nombre = nombre.strip().upper() if nombre else None
        self._edit_id = None
        self._var_mat.set("")
        self._lbl_mat_sel.config(text="— seleccionar material —", fg="#334400")
        self._var_precio.set("")
        self._var_und.set("")
        self._var_prio.set("PRINCIPAL")
        self._btn_agregar.configure(text="＋  AGREGAR MATERIAL")
        if self._proveedor_nombre:
            self._lbl_prov_activo.configure(
                text=f"  ◆  {self._proveedor_nombre}",
                text_color=_AMB)
        else:
            self._lbl_prov_activo.configure(
                text="— Selecciona un proveedor para gestionar sus materiales —",
                text_color=_MUT)
        self.refrescar_lista()

    def refrescar_lista(self):
        """Redibuja la lista de materiales del proveedor activo."""
        for w in self._f_rengs.winfo_children():
            w.destroy()
        if not self._proveedor_nombre:
            tk.Label(self._f_rengs,
                text="Sin materiales asignados",
                bg="#060a00", fg="#334400",
                font=("Segoe UI", 12, "italic")).pack(pady=24)
            self._lbl_conteo.configure(text="")
            return

        self._filas = pm_listar(self._proveedor_nombre)
        n = len(self._filas)
        self._lbl_conteo.configure(
            text=f"  {n} material{'es' if n != 1 else ''}  ")

        if not self._filas:
            tk.Label(self._f_rengs,
                text="Sin materiales asignados aún",
                bg="#060a00", fg="#334400",
                font=("Segoe UI", 12, "italic")).pack(pady=24)
            return

        PRIO_COL = {1: _GRN, 2: _CYAN}
        PRIO_TXT = {1: "● PRINCIPAL", 2: "○ RESPALDO"}

        for i, fila in enumerate(self._filas):
            bg_r = "#060a00" if i % 2 == 0 else "#080d00"
            fr = tk.Frame(self._f_rengs, bg=bg_r)
            fr.pack(fill="x")

            # Franja de color por prioridad (izquierda)
            pc = PRIO_COL.get(fila["prioridad"], _MUT)
            tk.Frame(fr, bg=pc, width=3).pack(side="left", fill="y")

            # Contenido
            f_cont = tk.Frame(fr, bg=bg_r)
            f_cont.pack(side="left", fill="x", expand=True, padx=6, pady=5)

            # Línea 1: nombre material + precio
            f_l1 = tk.Frame(f_cont, bg=bg_r)
            f_l1.pack(fill="x")
            tk.Label(f_l1, text=fila["material"],
                bg=bg_r, fg=_TXT,
                font=("Consolas", 12, "bold"),
                anchor="w").pack(side="left")
            if fila["precio_ref"] and fila["precio_ref"] > 0:
                tk.Label(f_l1, text=f"  ${fila['precio_ref']:,.2f}",
                    bg=bg_r, fg=_GRN,
                    font=("Consolas", 12),
                    anchor="e").pack(side="right")

            # Línea 2: prioridad + unidad
            f_l2 = tk.Frame(f_cont, bg=bg_r)
            f_l2.pack(fill="x")
            tk.Label(f_l2,
                text=PRIO_TXT.get(fila["prioridad"], f"Prio {fila['prioridad']}"),
                bg=bg_r, fg=pc,
                font=("Consolas", 11),
                anchor="w").pack(side="left")
            if fila["unidad"]:
                tk.Label(f_l2, text=f"  {fila['unidad']}",
                    bg=bg_r, fg=_TXT2,
                    font=("Consolas", 11)).pack(side="left")

            # Botones EDT / ✕
            f_btns = tk.Frame(fr, bg=bg_r)
            f_btns.pack(side="right", padx=4)

            _f = fila  # captura para lambda
            btn_e = tk.Label(f_btns, text=" EDT ",
                bg=bg_r, fg=_AMB,
                font=("Consolas", 11, "bold"),
                cursor="hand2",
                relief="flat",
                highlightthickness=1, highlightbackground="#1a1a00")
            btn_e.pack(side="left", padx=(0, 3), pady=4)
            btn_e.bind("<Button-1>", lambda e, f=_f: self._editar_fila(f))
            btn_e.bind("<Enter>",    lambda e, b=btn_e: b.config(bg="#1a1a00"))
            btn_e.bind("<Leave>",    lambda e, b=btn_e, bg=bg_r: b.config(bg=bg))

            btn_x = tk.Label(f_btns, text=" ✕ ",
                bg=bg_r, fg=_RED,
                font=("Consolas", 11, "bold"),
                cursor="hand2",
                highlightthickness=1, highlightbackground="#1a0000")
            btn_x.pack(side="left", pady=4)
            btn_x.bind("<Button-1>", lambda e, fid=fila["id"]: self._eliminar(fid))
            btn_x.bind("<Enter>",    lambda e, b=btn_x: b.config(bg="#1a0000"))
            btn_x.bind("<Leave>",    lambda e, b=btn_x, bg=bg_r: b.config(bg=bg))

            # Separador
            tk.Frame(self._f_rengs, bg="#0d1a00", height=1).pack(fill="x")

    def _eliminar(self, registro_id: int):
        if messagebox.askyesno("Quitar material",
            "¿Quitar este material del proveedor?",
            parent=self.winfo_toplevel()):
            pm_eliminar(registro_id)
            self.refrescar_lista()


# ════════════════════════════════════════════════════════════════════════════
# VISTA COMPLETA DE UN CATÁLOGO — formulario izq + lista der
# ════════════════════════════════════════════════════════════════════════════
class CAT_Vista(ctk.CTkFrame):
    def __init__(self, parent, tabla, **kw):
        super().__init__(parent, fg_color="transparent",
                         corner_radius=0, **kw)
        self.tabla  = tabla
        self.acento = CAT_CONFIG[tabla]["acento"]
        self._construir()

    def _construir(self):
        if self.tabla == "proveedores":
            self._construir_proveedores()
        else:
            self._construir_estandar()

    def _construir_estandar(self):
        # Panel izquierdo — formulario (35%)
        self._piz = CAT_PanelFormulario(
            self, self.tabla, self.acento,
            on_save=self._on_guardado)
        self._piz.place(relx=0, rely=0, relwidth=0.36, relheight=1.0)

        # Panel derecho — catálogo (65%)
        self._pder = CAT_PanelCatalogo(
            self, self.tabla, self.acento,
            on_editar=self._cargar_edicion)
        self._pder.place(relx=0.365, rely=0, relwidth=0.635, relheight=1.0)

    def _construir_proveedores(self):
        # ── Columna izquierda: formulario (40%) ───────────────────────────────
        f_col_izq = tk.Frame(self, bg=_BG)
        f_col_izq.place(relx=0, rely=0, relwidth=0.40, relheight=1.0)

        # Panel de materiales (ocupa 45% inferior de la columna izq)
        self._pm_panel = CAT_PanelProveedorMateriales(f_col_izq)
        self._pm_panel.place(relx=0, rely=0.52, relwidth=1.0, relheight=0.48)

        # Formulario ocupa el 52% superior
        self._piz = CAT_PanelFormulario(
            f_col_izq, self.tabla, self.acento,
            on_save=self._on_guardado,
            on_proveedor_activo=self._pm_panel.cargar_proveedor)
        self._piz.place(relx=0, rely=0, relwidth=1.0, relheight=0.52)

        # ── Columna derecha: catálogo (60%) ───────────────────────────────────
        self._pder = CAT_PanelCatalogo(
            self, self.tabla, self.acento,
            on_editar=self._cargar_edicion)
        self._pder.place(relx=0.405, rely=0, relwidth=0.595, relheight=1.0)

    def _on_guardado(self):
        self._pder.refrescar()
        if self.tabla == "proveedores" and hasattr(self, "_pm_panel"):
            self._pm_panel.refrescar_lista()

    def _cargar_edicion(self, fila):
        self._piz.cargar_para_editar(fila)

    def refrescar(self):
        self._pder.refrescar()


# ════════════════════════════════════════════════════════════════════════════
# MÓDULO CATÁLOGOS COMPLETO — 4 sub-tabs con selector visual
# ════════════════════════════════════════════════════════════════════════════
class CatalogosMixin:
    """
    Mixin para inyectar en SistemaCorteApp via herencia múltiple.
    Requiere self.tabs[N] disponible como tab destino.
    Usar: self.crear_catalogos() en __init__ del sistema principal.
    """

    def crear_catalogos(self, tab_idx: int = None):
        """
        tab_idx: índice en self.tabs donde se montará el módulo.
        Si no se pasa, busca self.tabs_catalogos.
        """
        if tab_idx is not None:
            tab = self.tabs[tab_idx]
        elif hasattr(self, "tabs_catalogos"):
            tab = self.tabs_catalogos
        else:
            raise ValueError("Especifica tab_idx o define self.tabs_catalogos")

        tab.configure(bg=_BG)
        self._construir_catalogos(tab)

    def _construir_catalogos(self, tab):
        # ── Cabecera premium ─────────────────────────────────────────────────
        hdr = ctk.CTkFrame(tab, fg_color=_BG2, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkFrame(hdr, fg_color=_INDIGO, height=3,
                     corner_radius=0).pack(fill="x")
        f_hdr2 = ctk.CTkFrame(hdr, fg_color="transparent")
        f_hdr2.pack(fill="x", padx=16, pady=(10, 10))
        ctk.CTkLabel(f_hdr2,
                     text="◈  CATÁLOGOS — BASE DE DATOS MAESTRA",
                     fg_color="transparent", text_color=_INDIGO,
                     font=(_FTM, _FS - 1, "bold")).pack(side="left")

        # ── Badge Firebase — mismo patrón que fichas técnicas ────────────────
        self._frm_fb_cat = ctk.CTkFrame(f_hdr2,
                                         fg_color="#200a0a",
                                         border_width=2,
                                         border_color=_RED,
                                         corner_radius=12)
        self._frm_fb_cat.pack(side="right", padx=(0, 10))
        self._lbl_fb_cat_dot = ctk.CTkLabel(
            self._frm_fb_cat, text="●",
            fg_color="transparent", text_color="#475569",
            font=(_FT, 16))
        self._lbl_fb_cat_dot.pack(side="left", padx=(10, 4), pady=6)
        self._lbl_fb_cat_txt = ctk.CTkLabel(
            self._frm_fb_cat, text="Firebase…",
            fg_color="transparent", text_color="#475569",
            font=(_FT, max(8, _FS - 3), "bold"))
        self._lbl_fb_cat_txt.pack(side="left", padx=(0, 10), pady=6)
        for _w in (self._frm_fb_cat, self._lbl_fb_cat_dot, self._lbl_fb_cat_txt):
            _w.configure(cursor="hand2")
        tab.after(2000, self._fb_actualizar_indicador_cat)

        ctk.CTkFrame(hdr, fg_color=_BDR, height=1,
                     corner_radius=0).pack(fill="x")

        # ── Selector de sub-catálogo (botones con acento por catálogo) ────────
        f_sel = ctk.CTkFrame(tab, fg_color=_BG3, corner_radius=0)
        f_sel.pack(fill="x")
        f_sel_in = ctk.CTkFrame(f_sel, fg_color="transparent")
        f_sel_in.pack(padx=10, pady=6, anchor="w")

        self._cat_activo    = tk.StringVar(value="materiales")
        self._cat_vistas    = {}
        self._cat_btns      = {}
        self._cat_body      = ctk.CTkFrame(tab, fg_color="transparent",
                                            corner_radius=0)
        self._cat_body.pack(fill="both", expand=True)

        orden = ["materiales", "trabajadores", "proveedores", "clientes",
                 "ingenieria_costos"]
        for key in orden:
            if key == "ingenieria_costos":
                btn = ctk.CTkButton(
                    f_sel_in,
                    text="\U0001f512  ING. COSTOS",
                    command=lambda k=key: self._cat_seleccionar(k),
                    fg_color=_IC_GOLD_BG, hover_color="#2a2000",
                    text_color=_IC_GOLD,
                    font=(_FTM, _FS - 4, "bold"),
                    corner_radius=8, height=34,
                    border_width=2, border_color=_IC_GOLD,
                    width=160)
                btn.pack(side="left", padx=(0, 8))
                self._cat_btns[key] = btn
                vista = IC_Contenedor(self._cat_body)
                vista.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
                self._cat_vistas[key] = vista
            else:
                cfg = CAT_CONFIG[key]
                btn = ctk.CTkButton(
                    f_sel_in,
                    text=f"{cfg['icono']}  {cfg['label']}",
                    command=lambda k=key: self._cat_seleccionar(k),
                    fg_color=_BG2, hover_color=_CARD2,
                    text_color=_TXT2,
                    font=(_FTM, _FS - 4, "bold"),
                    corner_radius=8, height=34,
                    border_width=2, border_color=_BDR,
                    width=160)
                btn.pack(side="left", padx=(0, 8))
                self._cat_btns[key] = btn
                vista = CAT_Vista(self._cat_body, key)
                vista.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
                self._cat_vistas[key] = vista

        # Activar el primero
        self._cat_seleccionar("materiales")

    def _cat_seleccionar(self, key):
        self._cat_activo.set(key)

        # Actualizar estilo de botones
        for k, btn in self._cat_btns.items():
            if k == "ingenieria_costos":
                if k == key:
                    btn.configure(fg_color="#2a2000",
                                  text_color=_IC_GOLD,
                                  border_color=_IC_GOLD)
                else:
                    btn.configure(fg_color=_IC_GOLD_BG,
                                  text_color=_IC_GOLD,
                                  border_color=_IC_GOLD)
            else:
                c = CAT_CONFIG[k]
                if k == key:
                    btn.configure(
                        fg_color=c["acento2"],
                        text_color=c["acento"],
                        border_color=c["acento"])
                else:
                    btn.configure(
                        fg_color=_BG2,
                        text_color=_TXT2,
                        border_color=_BDR)

        # Mostrar vista activa — ocultar el resto
        for k, vista in self._cat_vistas.items():
            if k == key:
                vista.lift()
            else:
                vista.lower()

    # ── Badge Firebase — mismo patrón que FichasMixin ────────────────────────
    def _fb_estado(self):
        try:
            import sys as _sys
            _p = (_sys.modules.get("__main__") or
                  _sys.modules.get("SISTEMA_CALZADO_V67_firebase") or
                  _sys.modules.get("SISTEMA_CALZADO_V68"))
            if _p is None:
                return {"firebase_conectado": False, "pendientes_sync": 0}
            fn = getattr(_p, "_db_estado", None)
            if fn:
                return fn()
            return {
                "firebase_conectado": getattr(_p, "_fb_disponible", False),
                "pendientes_sync":    getattr(_p, "_db_cola_count",
                                              lambda: 0)(),
            }
        except Exception:
            return {"firebase_conectado": False, "pendientes_sync": 0}

    def _fb_actualizar_indicador_cat(self):
        try:
            if not hasattr(self, "_frm_fb_cat"):
                return
            self._frm_fb_cat.winfo_exists()
        except Exception:
            return

        estado    = self._fb_estado()
        conectado = estado.get("firebase_conectado", False)
        cola      = estado.get("pendientes_sync", 0)

        if conectado and cola == 0:
            dot_col = _GRN;  txt = "Firebase ✓"; cola_txt = "Sincronizado"
            bg_frame = "#0a1f0a"; bdr_col = _GRN
        elif conectado and cola > 0:
            dot_col = _AMB;  txt = "Firebase ↑"; cola_txt = f"{cola} pendiente(s)"
            bg_frame = "#1a1200"; bdr_col = _AMB
        else:
            dot_col = _RED;  txt = "Sin Firebase"; cola_txt = "Modo offline"
            bg_frame = "#200a0a"; bdr_col = _RED

        try:
            self._frm_fb_cat.configure(fg_color=bg_frame, border_color=bdr_col)
            self._lbl_fb_cat_dot.configure(text_color=dot_col, fg_color=bg_frame)
            self._lbl_fb_cat_txt.configure(text=txt, fg_color=bg_frame,
                                            text_color=dot_col)
        except Exception:
            return

        try:
            # Re-checar cada 5 s — usa el primer tab disponible como anchor
            ref_tab = (self.tabs[2] if hasattr(self, "tabs") and len(self.tabs) > 2
                       else None)
            if ref_tab:
                ref_tab.after(5000, self._fb_actualizar_indicador_cat)
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════════════════
# CatalogosFrame — widget standalone para prueba independiente
# ════════════════════════════════════════════════════════════════════════════
class CatalogosFrame(CatalogosMixin, ctk.CTkFrame):
    """Widget standalone. Uso: CatalogosFrame(parent).pack(fill='both', expand=True)"""

    def __init__(self, parent, app_ref=None):
        ctk.CTkFrame.__init__(self, parent, fg_color=_BG, corner_radius=0)
        self.app_ref = app_ref
        # Stub mínimo para que CatalogosMixin encuentre self.tabs
        self.tabs = [None, None, self, None, None]

        cat_init_db()
        # Ejecutar _construir_catalogos directamente sobre self
        self._construir_catalogos(self)

    def _fb_actualizar_indicador_cat(self):
        # En modo standalone no hay firebase — mostrar offline sin re-polling
        try:
            self._frm_fb_cat.configure(fg_color="#200a0a", border_color=_RED)
            self._lbl_fb_cat_dot.configure(text_color=_RED, fg_color="#200a0a")
            self._lbl_fb_cat_txt.configure(text="Sin Firebase",
                                            fg_color="#200a0a", text_color=_RED)
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════════════════
# API PÚBLICA — funciones para consumo desde fichas_tecnicas y sistema principal
# ════════════════════════════════════════════════════════════════════════════

def cat_get_nombres_materiales(solo_activos: bool = True) -> list:
    """
    Retorna lista de nombres de materiales del catálogo.
    Uso en Fichas Técnicas para autocomplete.
    """
    estatus = "ACTIVO" if solo_activos else "TODOS"
    filas = cat_buscar("materiales", "", estatus)
    return [f[1] for f in filas]


def cat_get_material_por_nombre(nombre: str) -> dict:
    """
    Retorna dict con datos del material (tipo, unidad, depto, visible_monitor).
    Retorna {} si no existe.
    Uso: al seleccionar material en Fichas Técnicas → pre-llenar campos.
    """
    nm = nombre.strip().upper()
    if not nm:
        return {}
    con = sqlite3.connect(CAT_DB_PATH)
    cur = con.cursor()
    # Performance optimization: Direct SELECT using index on 'nombre' column to bypass cat_buscar full table scan
    cur.execute("SELECT datos_json FROM materiales WHERE nombre = ?", (nm,))
    row = cur.fetchone()
    con.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except Exception:
            return {}
    return {}


def cat_get_nombres_trabajadores(solo_activos: bool = True) -> list:
    estatus = "ACTIVO" if solo_activos else "TODOS"
    return [f[1] for f in cat_buscar("trabajadores", "", estatus)]


def cat_listar_trabajadores(solo_activos: bool = True) -> list:
    """
    API publica para modulo_nomina_ui.
    Retorna lista de dicts con todos los campos relevantes de cada trabajador.
    """
    estatus = "ACTIVO" if solo_activos else "TODOS"
    rows = cat_buscar("trabajadores", "", estatus)
    resultado = []
    for row in rows:
        datos = {}
        try:
            datos = json.loads(row[2])
        except Exception:
            pass
        resultado.append({
            "id":                row[0],
            "nombre":            row[1],
            "departamento":      datos.get("departamento", ""),
            "puesto":            datos.get("puesto", ""),
            "tipo_pago":         datos.get("tipo_pago", "POR PAR"),
            "sueldo_semanal":    float(datos.get("sueldo_semanal", 0) or 0),
            "cuota_minima_pares": int(float(datos.get("cuota_minima_pares", 0) or 0)),
            "estatus":           row[3],
        })
    return resultado


def cat_alta_rapida_trabajador(nombre: str, departamento: str,
                                tipo_pago: str = "POR PAR") -> tuple:
    """
    Alta rapida de trabajador desde nomina sin abrir el modulo de catalogos.
    Retorna (True, id) o (False, mensaje).
    """
    nombre = nombre.strip().upper()
    if not nombre:
        return False, "El nombre es obligatorio."
    datos = {
        "nombre":             nombre,
        "departamento":       departamento.strip().upper(),
        "tipo_pago":          tipo_pago.strip().upper(),
        "puesto":             "OTRO",
        "sueldo_semanal":     0,
        "cuota_minima_pares": 0,
        "estatus":            "ACTIVO",
        "notas":              "Alta rapida desde nomina",
    }
    return cat_guardar("trabajadores", datos)


def cat_get_nombres_proveedores(solo_activos: bool = True) -> list:
    estatus = "ACTIVO" if solo_activos else "TODOS"
    return [f[1] for f in cat_buscar("proveedores", "", estatus)]


def cat_get_nombres_clientes(solo_activos: bool = True) -> list:
    estatus = "ACTIVO" if solo_activos else "TODOS"
    return [f[1] for f in cat_buscar("clientes", "", estatus)]


def cat_precarga_material(nombre: str) -> dict:
    """
    Dado un nombre de material, retorna dict listo para precargar
    en el formulario de Fichas Técnicas:
        tipo_ft    → "DIR" o "IND"  (formato que usa ft_var_tipo SegmentedButton)
        unidad     → "dm", "mts", etc.
        departamento → "CORTE", etc.
        monitor    → True / False
        principal  → True / False
    Retorna {} si el material no existe en el catálogo.
    """
    datos = cat_get_material_por_nombre(nombre)
    if not datos:
        return {}
    tipo_raw = datos.get("tipo_material", "DIRECTO").upper()
    tipo_ft  = "DIR" if "DIRECTO" in tipo_raw else "IND"
    return {
        "tipo_ft":      tipo_ft,
        "unidad":       datos.get("unidad_default", "dm"),
        "departamento": datos.get("departamento", "CORTE"),
        "monitor":      datos.get("visible_monitor", "SÍ") == "SÍ",
        "principal":    datos.get("es_principal", "NO") == "SÍ",
    }


# ════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA — prueba standalone
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    cat_init_db()
    root = ctk.CTk()
    root.title("Catálogos — Premium v1.0")
    root.geometry("1280x800")
    root.configure(fg_color=_BG)

    frame = CatalogosFrame(root)
    frame.pack(fill="both", expand=True)

    root.mainloop()


# ════════════════════════════════════════════════════════════════════════════
# INGENIERÍA DE COSTOS — Base de datos
# ════════════════════════════════════════════════════════════════════════════
import hashlib as _hashlib

_IC_PASSWORD_DEFAULT = "1234"   # contraseña inicial — el usuario la cambia

def _ic_hash(pwd: str) -> str:
    return _hashlib.sha256(pwd.encode()).hexdigest()

def ic_init_db():
    """Crea tablas de Ingeniería de Costos en catalogos_db.sqlite."""
    con = sqlite3.connect(CAT_DB_PATH)
    cur = con.cursor()

    # Tabla de configuración (contraseña hasheada)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ic_config (
            clave  TEXT PRIMARY KEY,
            valor  TEXT NOT NULL
        )
    """)
    # Insertar contraseña por defecto si no existe
    cur.execute("""
        INSERT OR IGNORE INTO ic_config (clave, valor)
        VALUES ('password_hash', ?)
    """, (_ic_hash(_IC_PASSWORD_DEFAULT),))

    # Tabla de estilos con precio de par completo por departamento
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ic_estilos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            estilo        TEXT NOT NULL,
            departamento  TEXT NOT NULL,
            precio_par    REAL NOT NULL DEFAULT 0.0,
            notas         TEXT DEFAULT '',
            fecha_alta    TEXT NOT NULL,
            fecha_mod     TEXT NOT NULL,
            UNIQUE(estilo, departamento)
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ic_estilo
        ON ic_estilos(estilo)
    """)

    # Tabla de fracciones por estilo+departamento
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ic_fracciones (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ic_estilo_id  INTEGER NOT NULL REFERENCES ic_estilos(id) ON DELETE CASCADE,
            nombre        TEXT NOT NULL,
            precio        REAL NOT NULL DEFAULT 0.0,
            orden         INTEGER DEFAULT 0,
            fecha_alta    TEXT NOT NULL,
            fecha_mod     TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ic_frac_estilo
        ON ic_fracciones(ic_estilo_id)
    """)

    con.commit()
    con.close()


# ── CRUD Ingeniería de Costos ─────────────────────────────────────────────

def ic_verificar_password(pwd: str) -> bool:
    con = sqlite3.connect(CAT_DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT valor FROM ic_config WHERE clave='password_hash'")
    row = cur.fetchone()
    con.close()
    if not row:
        return False
    return row[0] == _ic_hash(pwd)

def ic_cambiar_password(pwd_actual: str, pwd_nueva: str) -> tuple:
    if not ic_verificar_password(pwd_actual):
        return False, "Contraseña actual incorrecta."
    if len(pwd_nueva) < 4:
        return False, "La contraseña nueva debe tener al menos 4 caracteres."
    con = sqlite3.connect(CAT_DB_PATH)
    con.execute("UPDATE ic_config SET valor=? WHERE clave='password_hash'",
                (_ic_hash(pwd_nueva),))
    con.commit(); con.close()
    return True, "Contraseña actualizada."

def ic_guardar_estilo(estilo: str, departamento: str,
                      precio_par: float, notas: str = "",
                      registro_id: int = None) -> tuple:
    hoy = datetime.date.today().isoformat()
    estilo = estilo.strip().upper()
    departamento = departamento.strip().upper()
    if not estilo or not departamento:
        return False, "Estilo y departamento son obligatorios."
    try:
        con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
        if registro_id:
            cur.execute("""
                UPDATE ic_estilos
                SET estilo=?, departamento=?, precio_par=?, notas=?, fecha_mod=?
                WHERE id=?
            """, (estilo, departamento, precio_par, notas.upper(), hoy, registro_id))
            con.commit(); con.close()
            return True, registro_id
        else:
            cur.execute("""
                INSERT INTO ic_estilos
                    (estilo, departamento, precio_par, notas, fecha_alta, fecha_mod)
                VALUES (?,?,?,?,?,?)
            """, (estilo, departamento, precio_par, notas.upper(), hoy, hoy))
            new_id = cur.lastrowid
            con.commit(); con.close()
            return True, new_id
    except sqlite3.IntegrityError:
        try: con.close()
        except Exception: pass
        return False, f"Ya existe el estilo {estilo} en {departamento}."
    except Exception as e:
        return False, str(e)

def ic_eliminar_estilo(registro_id: int):
    con = sqlite3.connect(CAT_DB_PATH)
    con.execute("DELETE FROM ic_estilos WHERE id=?", (registro_id,))
    con.commit(); con.close()

def ic_listar_estilos(buscar: str = "", departamento: str = "TODOS") -> list:
    con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
    like = f"%{buscar.upper()}%"
    if departamento == "TODOS":
        cur.execute("""
            SELECT id, estilo, departamento, precio_par, notas, fecha_alta
            FROM ic_estilos
            WHERE estilo LIKE ? OR notas LIKE ?
            ORDER BY departamento, estilo
        """, (like, like))
    else:
        cur.execute("""
            SELECT id, estilo, departamento, precio_par, notas, fecha_alta
            FROM ic_estilos
            WHERE departamento=? AND (estilo LIKE ? OR notas LIKE ?)
            ORDER BY estilo
        """, (departamento.upper(), like, like))
    rows = cur.fetchall(); con.close()
    return [{"id": r[0], "estilo": r[1], "departamento": r[2],
             "precio_par": r[3], "notas": r[4], "fecha_alta": r[5]}
            for r in rows]

def ic_guardar_fraccion(ic_estilo_id: int, nombre: str,
                        precio: float, orden: int = 0,
                        registro_id: int = None) -> tuple:
    hoy = datetime.date.today().isoformat()
    nombre = nombre.strip().upper()
    if not nombre:
        return False, "El nombre de la fracción es obligatorio."
    try:
        con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
        if registro_id:
            cur.execute("""
                UPDATE ic_fracciones
                SET nombre=?, precio=?, orden=?, fecha_mod=?
                WHERE id=?
            """, (nombre, precio, orden, hoy, registro_id))
        else:
            cur.execute("""
                INSERT INTO ic_fracciones
                    (ic_estilo_id, nombre, precio, orden, fecha_alta, fecha_mod)
                VALUES (?,?,?,?,?,?)
            """, (ic_estilo_id, nombre, precio, orden, hoy, hoy))
        con.commit(); con.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)

def ic_eliminar_fraccion(registro_id: int):
    con = sqlite3.connect(CAT_DB_PATH)
    con.execute("DELETE FROM ic_fracciones WHERE id=?", (registro_id,))
    con.commit(); con.close()

def ic_listar_fracciones(ic_estilo_id: int) -> list:
    con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
    cur.execute("""
        SELECT id, nombre, precio, orden
        FROM ic_fracciones
        WHERE ic_estilo_id=?
        ORDER BY orden, id
    """, (ic_estilo_id,))
    rows = cur.fetchall(); con.close()
    return [{"id": r[0], "nombre": r[1], "precio": r[2], "orden": r[3]}
            for r in rows]

def ic_get_tarifa(estilo: str, departamento: str) -> dict:
    """
    API pública para el módulo de nómina.
    Retorna {"precio_par": X, "fracciones": [...], "modo": "PAR"|"FRACCIONADO"}
    """
    con = sqlite3.connect(CAT_DB_PATH); cur = con.cursor()
    cur.execute("""
        SELECT id, precio_par FROM ic_estilos
        WHERE estilo=? AND departamento=?
    """, (estilo.strip().upper(), departamento.strip().upper()))
    row = cur.fetchone(); con.close()
    if not row:
        return {"precio_par": 0.0, "fracciones": [], "modo": "SIN_TARIFA"}
    est_id, precio_par = row
    fracciones = ic_listar_fracciones(est_id)
    modo = "FRACCIONADO" if fracciones else "PAR"
    return {"precio_par": precio_par, "fracciones": fracciones, "modo": modo}


# ════════════════════════════════════════════════════════════════════════════
# IC_ModalPassword — modal de acceso protegido
# ════════════════════════════════════════════════════════════════════════════
class IC_ModalPassword(ctk.CTkToplevel):
    """
    Modal que bloquea el acceso a Ingeniería de Costos.
    on_success(callback) se ejecuta si la contraseña es correcta.
    """
    _GOLD   = "#d4a017"
    _GOLD_BG = "#1a1200"

    def __init__(self, parent, on_success, **kw):
        super().__init__(parent, **kw)
        self._on_success = on_success
        # overrideredirect causa crash en Android/Pydroid — no se usa
        self.configure(fg_color="#0f0d00")
        self.resizable(False, False)
        self.lift()
        self.grab_set()

        # Centrar
        try:
            root = parent.winfo_toplevel()
            root.update_idletasks()
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
        except Exception:
            sw, sh = 1080, 2340
        w = min(480, int(sw * 0.88))
        h = 300
        x = (sw - w) // 2
        y = max(10, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._construir()
        self.after(150, lambda: self._ent_pwd.focus_set())

    def _construir(self):
        GOLD = "#d4a017"
        # Borde dorado exterior
        outer = ctk.CTkFrame(self, fg_color=GOLD, corner_radius=14)
        outer.pack(fill="both", expand=True, padx=0, pady=0)
        inner = ctk.CTkFrame(outer, fg_color="#0f0c00", corner_radius=12)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        # Header
        hdr = ctk.CTkFrame(inner, fg_color="#1a1400", corner_radius=0, height=48)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkFrame(hdr, fg_color=GOLD, height=2,
                     corner_radius=0).pack(fill="x", side="top")
        ctk.CTkLabel(hdr,
                     text="  [#]  INGENIERÍA DE COSTOS — ACCESO RESTRINGIDO",
                     fg_color="transparent", text_color=GOLD,
                     font=(_FTM, max(9, _FS - 2), "bold"),
                     anchor="w").pack(side="left", padx=14, pady=10)

        def _cerrar():
            try: self.grab_release()
            except Exception: pass
            try: self.destroy()
            except Exception: pass

        ctk.CTkButton(hdr, text="✕", width=40, height=32,
                      fg_color="#1a0808", text_color=_RED,
                      font=(_FTM, _FS - 2, "bold"),
                      hover_color="#2d0a0a", corner_radius=6,
                      command=_cerrar).pack(side="right", padx=8, pady=6)

        # Cuerpo
        body = ctk.CTkFrame(inner, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(body,
                     text="Ingresa la contraseña de supervisor:",
                     fg_color="transparent", text_color=_TXT2,
                     font=(_FT, _FS - 1)).pack(anchor="w", pady=(0, 6))

        f_ent = ctk.CTkFrame(body, fg_color=_BG3,
                             border_width=2, border_color=GOLD,
                             corner_radius=10)
        f_ent.pack(fill="x")
        self._var_pwd = tk.StringVar()
        self._ent_pwd = ctk.CTkEntry(
            f_ent, textvariable=self._var_pwd,
            show="●", fg_color=_BG3, text_color=GOLD,
            border_width=0, corner_radius=8,
            font=(_FTM, _FS + 4, "bold"), justify="center",
            height=40)
        self._ent_pwd.pack(fill="x", padx=6, pady=6)
        self._ent_pwd.bind("<Return>", lambda e: self._validar())

        self._lbl_err = ctk.CTkLabel(body, text="",
                                      fg_color="transparent",
                                      text_color=_RED,
                                      font=(_FT, _FS - 2, "italic"))
        self._lbl_err.pack(pady=(4, 0))

        ctk.CTkButton(body,
                      text="  INGRESAR  →",
                      fg_color="#1a1400", text_color=GOLD,
                      font=(_FTM, _FS, "bold"),
                      corner_radius=10, height=40,
                      border_width=1, border_color=GOLD,
                      hover_color="#2a2000",
                      command=self._validar).pack(fill="x", pady=(12, 0))

        ctk.CTkLabel(body,
                     text="Contraseña inicial: 1234",
                     fg_color="transparent", text_color=_MUT,
                     font=(_FT, max(7, _FS - 4), "italic")).pack(pady=(6, 0))

    def _validar(self):
        pwd = self._var_pwd.get()
        if ic_verificar_password(pwd):
            try: self.grab_release()
            except Exception: pass
            try: self.destroy()
            except Exception: pass
            self._on_success()
        else:
            self._lbl_err.configure(text="⚠  Contraseña incorrecta.")
            self._var_pwd.set("")
            self._ent_pwd.focus_set()


# ════════════════════════════════════════════════════════════════════════════
# IC_Vista — vista principal de Ingeniería de Costos
# ════════════════════════════════════════════════════════════════════════════
_IC_GOLD     = "#d4a017"
_IC_GOLD_BG  = "#1a1200"
_IC_DEPTOS   = ["CORTE", "PESPUNTE", "MONTADO", "ADORNO", "EMBARQUE"]
_IC_DEP_COL  = {
    "CORTE":    "#38bdf8",
    "PESPUNTE": "#a78bfa",
    "MONTADO":  "#fb923c",
    "ADORNO":   "#f472b6",
    "EMBARQUE": "#22c55e",
}
_IC_TIMEOUT_MS = 15 * 60 * 1000   # 15 minutos

class IC_Vista(ctk.CTkFrame):
    """
    Vista completa de Ingeniería de Costos.
    Se construye solo tras autenticación correcta.
    Se auto-bloquea tras _IC_TIMEOUT_MS de inactividad.
    """

    def __init__(self, parent, on_bloquear, **kw):
        super().__init__(parent, fg_color="transparent",
                         corner_radius=0, **kw)
        self._on_bloquear   = on_bloquear
        self._estilo_sel_id = None   # id en ic_estilos del registro seleccionado
        self._timer_id      = None
        self._editando_id   = None   # para saber si estamos en modo edición

        self._var_busq  = tk.StringVar()
        self._var_dep   = tk.StringVar(value="TODOS")
        self._var_estilo   = tk.StringVar()
        self._var_dep_form = tk.StringVar(value="PESPUNTE")
        self._var_precio_par = tk.StringVar(value="0.00")

        ic_init_db()
        self._construir()
        self._reiniciar_timer()
        self.bind("<Button-1>", lambda e: self._reiniciar_timer(), add="+")
        self.bind("<Key>",      lambda e: self._reiniciar_timer(), add="+")

    # ── Timer de inactividad ──────────────────────────────────────────────
    def _reiniciar_timer(self):
        if self._timer_id:
            try: self.after_cancel(self._timer_id)
            except Exception: pass
        self._timer_id = self.after(_IC_TIMEOUT_MS, self._auto_bloquear)

    def _auto_bloquear(self):
        self._on_bloquear()

    # ── LAYOUT principal — tres columnas con place() ──────────────────────
    def _construir(self):
        # Cabecera
        hdr = ctk.CTkFrame(self, fg_color=_BG2, corner_radius=0, height=44)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkFrame(hdr, fg_color=_IC_GOLD, height=3,
                     corner_radius=0).pack(fill="x")
        f_hdr = ctk.CTkFrame(hdr, fg_color="transparent")
        f_hdr.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(f_hdr,
                     text="  [#]  INGENIERÍA DE COSTOS — TARIFAS POR ESTILO",
                     fg_color="transparent", text_color=_IC_GOLD,
                     font=(_FTM, _FS, "bold")).pack(side="left")

        # Botón bloquear
        ctk.CTkButton(f_hdr, text="[#]  Bloquear",
                      fg_color=_IC_GOLD_BG, text_color=_IC_GOLD,
                      font=(_FT, _FS - 2, "bold"),
                      corner_radius=8, height=28, width=110,
                      border_width=1, border_color=_IC_GOLD,
                      hover_color="#2a2000",
                      command=self._on_bloquear).pack(side="right", padx=(0, 4))

        # Botón cambiar contraseña
        ctk.CTkButton(f_hdr, text="[K]  Clave",
                      fg_color=_BG3, text_color=_TXT2,
                      font=(_FT, _FS - 2),
                      corner_radius=8, height=28, width=90,
                      hover_color="#252525",
                      command=self._cambiar_password
                      ).pack(side="right", padx=(0, 6))

        ctk.CTkFrame(self, fg_color=_BDR, height=1,
                     corner_radius=0).pack(fill="x")

        # Cuerpo — dos columnas con place()
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=8, pady=6)
        self._body.after(60, self._reposicionar)

        self._construir_col_izq()
        self._construir_col_der()
        self._refrescar_lista()

    def _reposicionar(self):
        try:
            try:
                self._body.update_idletasks()
            except Exception:
                pass
            w = self._body.winfo_width()
            h = self._body.winfo_height()
            if w < 50 or h < 50:
                self._body.after(120, self._reposicionar); return
            self._frm_izq.place(relx=0.0,   rely=0.0,
                                 relwidth=0.38, relheight=1.0)
            self._frm_der.place(relx=0.385, rely=0.0,
                                 relwidth=0.615, relheight=1.0)
        except Exception:
            self._body.after(200, self._reposicionar)

    # ── COLUMNA IZQUIERDA — formulario de estilo + fracciones ────────────
    def _construir_col_izq(self):
        f = ctk.CTkScrollableFrame(self._body, fg_color=_CARD,
                                    border_width=1, border_color=_BDR,
                                    corner_radius=12)
        self._frm_izq = f

        ctk.CTkFrame(f, fg_color=_IC_GOLD, height=2,
                     corner_radius=0).pack(fill="x")
        ctk.CTkLabel(f, text="  ⚡  CAPTURA DE TARIFA",
                     fg_color="transparent", text_color=_IC_GOLD,
                     font=(_FTM, _FS, "bold")).pack(
                     anchor="w", padx=14, pady=(8, 6))

        # Estilo
        ctk.CTkLabel(f, text="ID / NOMBRE DE ESTILO",
                     fg_color="transparent", text_color=_TXT2,
                     font=(_FT, _FS - 2, "bold")).pack(
                     anchor="w", padx=14, pady=(0, 2))
        f_est = ctk.CTkFrame(f, fg_color=_BG3,
                             border_width=2, border_color=_IC_GOLD,
                             corner_radius=10)
        f_est.pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkEntry(f_est, textvariable=self._var_estilo,
                     fg_color=_BG3, text_color=_IC_GOLD,
                     border_width=0, corner_radius=8,
                     font=(_FTM, _FS + 6, "bold"), justify="center",
                     height=38).pack(fill="x", padx=4, pady=4)

        # Departamento
        ctk.CTkLabel(f, text="DEPARTAMENTO",
                     fg_color="transparent", text_color=_TXT2,
                     font=(_FT, _FS - 2, "bold")).pack(
                     anchor="w", padx=14, pady=(0, 2))

        f_deps = ctk.CTkFrame(f, fg_color="transparent")
        f_deps.pack(fill="x", padx=14, pady=(0, 8))
        self._btns_dep = {}
        for dep in _IC_DEPTOS:
            col = _IC_DEP_COL[dep]
            btn = ctk.CTkButton(
                f_deps, text=dep[:3],
                fg_color=_BG3, text_color=col,
                font=(_FT, _FS - 3, "bold"),
                corner_radius=8, height=30,
                border_width=1, border_color=_BDR,
                hover_color=_CARD2,
                command=lambda d=dep: self._sel_dep(d))
            btn.pack(side="left", padx=(0, 4))
            self._btns_dep[dep] = btn
        self._sel_dep("PESPUNTE")

        # Precio par completo
        ctk.CTkLabel(f, text="PRECIO PAR COMPLETO ($)",
                     fg_color="transparent", text_color=_TXT2,
                     font=(_FT, _FS - 2, "bold")).pack(
                     anchor="w", padx=14, pady=(0, 2))
        f_pp = ctk.CTkFrame(f, fg_color=_BG3,
                            border_width=2, border_color=_IC_GOLD,
                            corner_radius=10)
        f_pp.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkEntry(f_pp, textvariable=self._var_precio_par,
                     fg_color=_BG3, text_color=_IC_GOLD,
                     border_width=0, corner_radius=8,
                     font=(_FTM, _FS + 8, "bold"), justify="center",
                     height=42).pack(fill="x", padx=4, pady=4)

        # Botón guardar estilo
        self._btn_guardar_estilo = ctk.CTkButton(
            f, text="✓  GUARDAR ESTILO",
            fg_color=_IC_GOLD_BG, text_color=_IC_GOLD,
            font=(_FTM, _FS - 1, "bold"),
            corner_radius=10, height=38,
            border_width=1, border_color=_IC_GOLD,
            hover_color="#2a2000",
            command=self._guardar_estilo)
        self._btn_guardar_estilo.pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkButton(f, text="✕  LIMPIAR",
                      fg_color=_BG3, text_color=_MUT,
                      font=(_FT, _FS - 2),
                      corner_radius=8, height=28,
                      border_width=1, border_color=_BDR,
                      hover_color="#1a1a1a",
                      command=self._limpiar_form
                      ).pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkFrame(f, fg_color=_BDR, height=1,
                     corner_radius=0).pack(fill="x", padx=14, pady=(0, 8))

        # ── Sección de fracciones ─────────────────────────────────────────
        ctk.CTkFrame(f, fg_color=_PURP, height=2,
                     corner_radius=0).pack(fill="x", padx=14)
        ctk.CTkLabel(f, text="  ◈  FRACCIONES DEL PAR",
                     fg_color="transparent", text_color=_PURP,
                     font=(_FTM, _FS - 1, "bold")).pack(
                     anchor="w", padx=14, pady=(6, 2))

        # Indicador de balance
        self._lbl_balance = ctk.CTkLabel(
            f, text="Selecciona un estilo para fraccionar",
            fg_color=_BG3, text_color=_MUT,
            font=(_FTM, _FS - 1, "bold"),
            corner_radius=8)
        self._lbl_balance.pack(fill="x", padx=14, pady=(0, 6))

        # Lista de fracciones existentes
        self._frame_frac = ctk.CTkFrame(f, fg_color=_BG3,
                                         border_width=1, border_color=_BDR,
                                         corner_radius=8)
        self._frame_frac.pack(fill="x", padx=14, pady=(0, 6))
        self._lbl_no_frac = ctk.CTkLabel(
            self._frame_frac,
            text="  Sin fracciones — se paga\n  por par completo",
            fg_color="transparent", text_color=_MUT,
            font=(_FT, _FS - 2, "italic"), justify="left")
        self._lbl_no_frac.pack(pady=10)

        # Formulario nueva fracción
        ctk.CTkLabel(f, text="AGREGAR FRACCIÓN",
                     fg_color="transparent", text_color=_TXT2,
                     font=(_FT, _FS - 3, "bold")).pack(
                     anchor="w", padx=14, pady=(4, 2))
        self._var_frac_nombre = tk.StringVar()
        self._var_frac_precio = tk.StringVar(value="0.00")

        ctk.CTkEntry(f, textvariable=self._var_frac_nombre,
                     fg_color=_BG3, text_color=_PURP,
                     border_width=1, border_color=_PURP,
                     placeholder_text="Nombre de la operación…",
                     corner_radius=8, font=(_FT, _FS - 1),
                     height=30).pack(fill="x", padx=14, pady=(0, 4))

        f_fp = ctk.CTkFrame(f, fg_color="transparent")
        f_fp.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(f_fp, text="$",
                     fg_color="transparent", text_color=_PURP,
                     font=(_FTM, _FS, "bold")).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(f_fp, textvariable=self._var_frac_precio,
                     fg_color=_BG3, text_color=_PURP,
                     border_width=1, border_color=_PURP,
                     corner_radius=8, font=(_FTM, _FS, "bold"),
                     justify="center", height=30,
                     width=120).pack(side="left")

        ctk.CTkButton(f, text="＋  AGREGAR FRACCIÓN",
                      fg_color="#1a0a3a", text_color=_PURP,
                      font=(_FTM, _FS - 1, "bold"),
                      corner_radius=10, height=34,
                      border_width=1, border_color=_PURP,
                      hover_color="#2a1050",
                      command=self._agregar_fraccion
                      ).pack(fill="x", padx=14, pady=(0, 10))

    # ── COLUMNA DERECHA — lista de estilos registrados ────────────────────
    def _construir_col_der(self):
        f = ctk.CTkFrame(self._body, fg_color=_CARD,
                         border_width=1, border_color=_BDR,
                         corner_radius=12)
        self._frm_der = f

        ctk.CTkFrame(f, fg_color=_IC_GOLD, height=2,
                     corner_radius=0).pack(fill="x")

        # Cabecera + búsqueda
        f_hdr = ctk.CTkFrame(f, fg_color="transparent")
        f_hdr.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(f_hdr, text="  ESTILOS REGISTRADOS",
                     fg_color="transparent", text_color=_IC_GOLD,
                     font=(_FTM, _FS, "bold")).pack(side="left")

        f_busq = ctk.CTkFrame(f_hdr, fg_color=_BG3,
                              border_width=1, border_color=_IC_GOLD,
                              corner_radius=8)
        f_busq.pack(side="right")
        ctk.CTkLabel(f_busq, text="⌕",
                     fg_color="transparent", text_color=_IC_GOLD,
                     font=(_FTM, _FS)).pack(side="left", padx=(8, 2))
        self._var_busq.trace("w", lambda *_: self._refrescar_lista())
        ctk.CTkEntry(f_busq, textvariable=self._var_busq,
                     fg_color=_BG3, text_color=_IC_GOLD,
                     border_width=0, corner_radius=6,
                     font=(_FT, _FS - 1), width=160,
                     height=26).pack(side="left", ipady=3, padx=(0, 8), pady=4)

        # Filtros departamento
        f_filtros = ctk.CTkFrame(f, fg_color="transparent")
        f_filtros.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(f_filtros, text="Filtrar:",
                     fg_color="transparent", text_color=_MUT,
                     font=(_FT, _FS - 3)).pack(side="left", padx=(0, 6))
        self._var_dep_filtro = tk.StringVar(value="TODOS")
        for dep in ["TODOS"] + _IC_DEPTOS:
            col = _IC_DEP_COL.get(dep, _TXT2)
            ctk.CTkRadioButton(
                f_filtros,
                text=dep[:3] if dep != "TODOS" else "ALL",
                variable=self._var_dep_filtro, value=dep,
                text_color=col, fg_color=col, hover_color=col,
                radiobutton_width=12, radiobutton_height=12,
                font=(_FT, _FS - 3, "bold"),
                command=self._refrescar_lista
            ).pack(side="left", padx=3)

        # Cabecera tabla
        hdr_tbl = tk.Frame(f, bg=_BG2)
        hdr_tbl.pack(fill="x", padx=12)
        _COLS    = ("ESTILO", "DEPTO", "PAR $", "FRACCIONES", "MODO", "")
        _WEIGHTS = (12,        8,       8,        8,            10,     5)
        for ci, wt in enumerate(_WEIGHTS):
            hdr_tbl.columnconfigure(ci, weight=wt)
        for ci, (txt, wt) in enumerate(zip(_COLS, _WEIGHTS)):
            tk.Label(hdr_tbl, text=txt, bg=_BG2,
                     fg=_IC_GOLD if txt else _MUT,
                     font=(_FTM, max(7, int(_FS * 0.32)), "bold"),
                     anchor="center", width=1
                     ).grid(row=0, column=ci, sticky="ew", padx=2, pady=5)

        # Canvas scrollable
        f_co = tk.Frame(f, bg=_BG3)
        f_co.pack(fill="both", expand=True, padx=12)

        self._canvas = tk.Canvas(f_co, bg=_BG3,
                                  highlightthickness=0, bd=0)
        _sb = ctk.CTkScrollbar(f_co, orientation="vertical",
                                fg_color=_BG3, button_color=_BDR,
                                button_hover_color=_BORDER,
                                command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=_sb.set)
        _sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._frame_lista = tk.Frame(self._canvas, bg=_BG3)
        self._canvas_win  = self._canvas.create_window(
            (0, 0), window=self._frame_lista, anchor="nw")

        self._frame_lista.bind("<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(
                self._canvas_win, width=e.width))
        self._canvas.bind("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(
                -1 * (e.delta // 120), "units"))

        # Pie
        f_pie = ctk.CTkFrame(f, fg_color="transparent")
        f_pie.pack(fill="x", padx=12, pady=(2, 6))
        self._lbl_total_reg = ctk.CTkLabel(
            f_pie, text="—",
            fg_color="transparent", text_color=_MUT,
            font=(_FT, _FS - 3))
        self._lbl_total_reg.pack(side="left")
        ctk.CTkLabel(f_pie,
                     text="clic = seleccionar · doble-clic = editar",
                     fg_color="transparent", text_color=_MUT,
                     font=(_FT, _FS - 4, "italic")).pack(side="right")

    # ── Helpers selector departamento (formulario) ────────────────────────
    def _sel_dep(self, dep):
        self._var_dep_form.set(dep)
        for d, btn in self._btns_dep.items():
            col = _IC_DEP_COL[d]
            if d == dep:
                btn.configure(fg_color=_IC_GOLD_BG,
                               text_color=col,
                               border_color=col)
            else:
                btn.configure(fg_color=_BG3,
                               text_color=col,
                               border_color=_BDR)

    # ── Refrescar lista derecha ───────────────────────────────────────────
    def _refrescar_lista(self):
        f = self._frame_lista
        for w in f.winfo_children(): w.destroy()

        dep_fil = self._var_dep_filtro.get() if hasattr(self, "_var_dep_filtro") else "TODOS"
        busq    = self._var_busq.get().strip()
        filas   = ic_listar_estilos(buscar=busq, departamento=dep_fil)

        _TBL_FS = max(7, int(_FS * 0.32))
        _WEIGHTS = (12, 8, 8, 8, 10, 5)

        for row in filas:
            fracs    = ic_listar_fracciones(row["id"])
            n_frac   = len(fracs)
            suma_frac = sum(fr["precio"] for fr in fracs)
            modo     = "FRACCIONADO" if fracs else "PAR COMPLETO"

            # Semáforo balance
            if fracs:
                diff = round(row["precio_par"] - suma_frac, 4)
                if diff == 0:
                    bal_col = _GRN; bal_txt = "✓ CUADRA"
                elif diff > 0:
                    bal_col = _AMB; bal_txt = f"FALTA ${diff:.2f}"
                else:
                    bal_col = _RED; bal_txt = f"EXCEDE ${abs(diff):.2f}"
            else:
                bal_col = _IC_GOLD; bal_txt = "PAR"

            dep_col = _IC_DEP_COL.get(row["departamento"], _TXT2)
            bg_fila = "#0f0d00"

            f_fila = tk.Frame(f, bg=bg_fila)
            f_fila.pack(fill="x", padx=2, pady=1)
            for ci, wt in enumerate(_WEIGHTS):
                f_fila.columnconfigure(ci, weight=wt)

            for ci, (txt, fg, fnt) in enumerate([
                (row["estilo"],                    _IC_GOLD, (_FTM, _TBL_FS, "bold")),
                (row["departamento"][:3],           dep_col,  (_FTM, _TBL_FS, "bold")),
                (f"${row['precio_par']:.2f}",      _TXT2,    (_FTM, _TBL_FS)),
                (str(n_frac) if n_frac else "—",   _PURP,    (_FT,  _TBL_FS)),
                (bal_txt,                           bal_col,  (_FTM, _TBL_FS, "bold")),
            ]):
                tk.Label(f_fila, text=txt, bg=bg_fila, fg=fg,
                         font=fnt, anchor="center", width=1
                         ).grid(row=0, column=ci,
                                sticky="ew", padx=2, pady=5)

            # Botón editar
            btn_e = tk.Label(f_fila, text="EDT", bg="#1a1400",
                              fg=_IC_GOLD,
                              font=(_FTM, _TBL_FS, "bold"),
                              cursor="hand2", padx=4)
            btn_e.grid(row=0, column=5, sticky="ew", padx=2)
            btn_e.bind("<Button-1>",
                       lambda e, r=row: self._cargar_edicion(r))

            # Hover
            bg_h = "#1a1800"
            f_fila.bind("<Enter>",
                lambda e, fr=f_fila: fr.config(bg=bg_h))
            f_fila.bind("<Leave>",
                lambda e, fr=f_fila: fr.config(bg=bg_fila))
            f_fila.bind("<Button-1>",
                        lambda e, r=row: self._seleccionar_estilo(r))
            f_fila.bind("<Double-Button-1>",
                        lambda e, r=row: self._cargar_edicion(r))

        self._lbl_total_reg.configure(
            text=f"{len(filas)} estilo(s) registrado(s)")
        if not filas:
            tk.Label(f, text="— Sin registros —",
                     bg=_BG3, fg=_MUT,
                     font=(_FT, max(8, _FS - 2), "italic"),
                     pady=20).pack()

    # ── Seleccionar estilo (para fraccionar) ──────────────────────────────
    def _seleccionar_estilo(self, row):
        self._estilo_sel_id = row["id"]
        self._var_estilo.set(row["estilo"])
        self._sel_dep(row["departamento"])
        self._var_precio_par.set(f"{row['precio_par']:.2f}")
        self._editando_id = row["id"]
        self._btn_guardar_estilo.configure(text="✓  ACTUALIZAR ESTILO")
        self._refrescar_fracciones()

    def _cargar_edicion(self, row):
        self._seleccionar_estilo(row)

    # ── Guardar estilo ────────────────────────────────────────────────────
    def _guardar_estilo(self):
        estilo = self._var_estilo.get().strip().upper()
        dep    = self._var_dep_form.get()
        try:
            precio = float(self._var_precio_par.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("AVISO", "El precio debe ser un número.",
                                   parent=self.winfo_toplevel()); return
        if not estilo:
            messagebox.showwarning("AVISO", "Ingresa el ID o nombre del estilo.",
                                   parent=self.winfo_toplevel()); return
        ok, resultado = ic_guardar_estilo(
            estilo, dep, precio,
            registro_id=self._editando_id)
        if ok:
            self._estilo_sel_id = resultado
            self._editando_id   = resultado
            self._btn_guardar_estilo.configure(text="✓  ACTUALIZAR ESTILO")
            self._refrescar_lista()
            self._refrescar_fracciones()
        else:
            messagebox.showerror("ERROR", resultado,
                                 parent=self.winfo_toplevel())

    def _limpiar_form(self):
        self._var_estilo.set("")
        self._var_precio_par.set("0.00")
        self._var_frac_nombre.set("")
        self._var_frac_precio.set("0.00")
        self._estilo_sel_id = None
        self._editando_id   = None
        self._btn_guardar_estilo.configure(text="✓  GUARDAR ESTILO")
        self._sel_dep("PESPUNTE")
        self._lbl_balance.configure(
            text="Selecciona un estilo para fraccionar",
            text_color=_MUT, fg_color=_BG3)
        for w in self._frame_frac.winfo_children(): w.destroy()
        self._lbl_no_frac = ctk.CTkLabel(
            self._frame_frac,
            text="  Sin fracciones — se paga\n  por par completo",
            fg_color="transparent", text_color=_MUT,
            font=(_FT, _FS - 2, "italic"), justify="left")
        self._lbl_no_frac.pack(pady=10)

    # ── Fracciones ────────────────────────────────────────────────────────
    def _agregar_fraccion(self):
        if not self._estilo_sel_id:
            messagebox.showwarning(
                "AVISO",
                "Primero guarda o selecciona un estilo\n"
                "antes de agregar fracciones.",
                parent=self.winfo_toplevel()); return
        nombre = self._var_frac_nombre.get().strip().upper()
        try:
            precio = float(self._var_frac_precio.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("AVISO", "El precio debe ser un número.",
                                   parent=self.winfo_toplevel()); return
        if not nombre:
            messagebox.showwarning("AVISO", "Ingresa el nombre de la fracción.",
                                   parent=self.winfo_toplevel()); return

        fracs_act = ic_listar_fracciones(self._estilo_sel_id)
        ok, _ = ic_guardar_fraccion(
            self._estilo_sel_id, nombre, precio,
            orden=len(fracs_act) + 1)
        if ok:
            self._var_frac_nombre.set("")
            self._var_frac_precio.set("0.00")
            self._refrescar_fracciones()
            self._refrescar_lista()

    def _refrescar_fracciones(self):
        f = self._frame_frac
        for w in f.winfo_children(): w.destroy()

        if not self._estilo_sel_id:
            ctk.CTkLabel(f,
                         text="  Sin fracciones — se paga\n  por par completo",
                         fg_color="transparent", text_color=_MUT,
                         font=(_FT, _FS - 2, "italic"),
                         justify="left").pack(pady=10)
            self._lbl_balance.configure(
                text="Selecciona un estilo para fraccionar",
                text_color=_MUT, fg_color=_BG3)
            return

        fracs = ic_listar_fracciones(self._estilo_sel_id)
        try:
            precio_par = float(self._var_precio_par.get().replace(",", "."))
        except Exception:
            precio_par = 0.0

        suma = sum(fr["precio"] for fr in fracs)
        diff = round(precio_par - suma, 4)

        # Actualizar indicador de balance
        if not fracs:
            self._lbl_balance.configure(
                text="✓  Sin fracciones — PAR COMPLETO",
                text_color=_IC_GOLD, fg_color=_IC_GOLD_BG)
        elif diff == 0:
            self._lbl_balance.configure(
                text=f"✓  CUADRA EXACTO  (${suma:.2f} / ${precio_par:.2f})",
                text_color=_GRN, fg_color=_GRN_BG)
        elif diff > 0:
            self._lbl_balance.configure(
                text=f"⚠  FALTA  ${diff:.2f}  (asignado ${suma:.2f} de ${precio_par:.2f})",
                text_color=_AMB, fg_color=_AMB_BG)
        else:
            self._lbl_balance.configure(
                text=f"✕  EXCEDE  ${abs(diff):.2f}  (${suma:.2f} > ${precio_par:.2f})",
                text_color=_RED, fg_color=_RED_BG)

        if not fracs:
            ctk.CTkLabel(f,
                         text="  Sin fracciones — se paga\n  por par completo",
                         fg_color="transparent", text_color=_MUT,
                         font=(_FT, _FS - 2, "italic"),
                         justify="left").pack(pady=10)
            return

        for fr in fracs:
            f_row = ctk.CTkFrame(f, fg_color=_BG3, corner_radius=6)
            f_row.pack(fill="x", padx=4, pady=2)
            ctk.CTkLabel(f_row, text=fr["nombre"],
                         fg_color="transparent", text_color=_PURP,
                         font=(_FTM, max(8, _FS - 3), "bold"),
                         anchor="w").pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(f_row, text=f"${fr['precio']:.2f}",
                         fg_color="transparent", text_color=_TXT2,
                         font=(_FTM, max(8, _FS - 3), "bold")
                         ).pack(side="right", padx=(0, 6))
            ctk.CTkButton(f_row, text="✕", width=26, height=22,
                          fg_color=_RED_BG, text_color=_RED,
                          font=(_FTM, max(7, _FS - 4), "bold"),
                          corner_radius=4, hover_color="#2d0a0a",
                          border_width=1, border_color=_RED,
                          command=lambda fid=fr["id"]: self._eliminar_fraccion(fid)
                          ).pack(side="right", padx=4)

    def _eliminar_fraccion(self, frac_id):
        ic_eliminar_fraccion(frac_id)
        self._refrescar_fracciones()
        self._refrescar_lista()

    # ── Cambiar contraseña ────────────────────────────────────────────────
    def _cambiar_password(self):
        GOLD = _IC_GOLD
        modal = ctk.CTkToplevel(self.winfo_toplevel())
        modal.title("Cambiar Contraseña")
        modal.geometry("380x280")
        modal.resizable(False, False)
        modal.grab_set()
        modal.configure(fg_color=_BG2)

        ctk.CTkFrame(modal, fg_color=GOLD, height=3,
                     corner_radius=0).pack(fill="x")
        ctk.CTkLabel(modal, text="  [K]  CAMBIAR CONTRASEÑA",
                     fg_color="transparent", text_color=GOLD,
                     font=(_FTM, _FS, "bold")).pack(
                     anchor="w", padx=16, pady=(10, 6))

        v_act  = tk.StringVar()
        v_new  = tk.StringVar()
        v_conf = tk.StringVar()

        for lbl, var in [("Contraseña actual:", v_act),
                          ("Nueva contraseña:",  v_new),
                          ("Confirmar nueva:",   v_conf)]:
            ctk.CTkLabel(modal, text=lbl, fg_color="transparent",
                         text_color=_TXT2, font=(_FT, _FS - 2)
                         ).pack(anchor="w", padx=16, pady=(0, 2))
            ctk.CTkEntry(modal, textvariable=var, show="●",
                         fg_color=_BG3, text_color=GOLD,
                         border_color=_BDR, border_width=1,
                         corner_radius=8, font=(_FTM, _FS - 1),
                         height=28).pack(fill="x", padx=16, pady=(0, 4))

        lbl_err = ctk.CTkLabel(modal, text="",
                               fg_color="transparent",
                               text_color=_RED, font=(_FT, _FS - 2))
        lbl_err.pack(anchor="w", padx=16)

        def guardar():
            if v_new.get() != v_conf.get():
                lbl_err.configure(text="Las contraseñas nuevas no coinciden.")
                return
            ok, msg = ic_cambiar_password(v_act.get(), v_new.get())
            if ok:
                modal.destroy()
                messagebox.showinfo("✓ LISTO", msg,
                                    parent=self.winfo_toplevel())
            else:
                lbl_err.configure(text=msg)

        ctk.CTkButton(modal, text="GUARDAR NUEVA CONTRASEÑA",
                      fg_color=_IC_GOLD_BG, text_color=GOLD,
                      font=(_FTM, _FS - 1, "bold"),
                      corner_radius=10, height=36,
                      border_width=1, border_color=GOLD,
                      hover_color="#2a2000",
                      command=guardar).pack(fill="x", padx=16, pady=(8, 0))


# ════════════════════════════════════════════════════════════════════════════
# IC_PanelBloqueo — pantalla de candado que se muestra cuando está bloqueado
# ════════════════════════════════════════════════════════════════════════════
class IC_PanelBloqueo(ctk.CTkFrame):
    """Pantalla que reemplaza la vista cuando el módulo está bloqueado."""

    def __init__(self, parent, on_desbloquear, **kw):
        super().__init__(parent, fg_color=_BG, corner_radius=0, **kw)
        self._on_desbloquear = on_desbloquear
        self._construir()

    def _construir(self):
        GOLD = _IC_GOLD
        # Centrar verticalmente con pack
        f_outer = ctk.CTkFrame(self, fg_color="transparent")
        f_outer.pack(fill="both", expand=True)

        f_centro = ctk.CTkFrame(f_outer, fg_color=_CARD,
                                 border_width=2, border_color=GOLD,
                                 corner_radius=18)
        f_centro.pack(expand=True, padx=60, pady=60)

        ctk.CTkFrame(f_centro, fg_color=GOLD, height=3,
                     corner_radius=0).pack(fill="x")

        ctk.CTkLabel(f_centro, text="[#]",
                     fg_color="transparent", text_color=GOLD,
                     font=(_FT, 52)).pack(pady=(30, 6))

        ctk.CTkLabel(f_centro,
                     text="INGENIERÍA DE COSTOS",
                     fg_color="transparent", text_color=GOLD,
                     font=(_FTM, _FS + 4, "bold")).pack()

        ctk.CTkLabel(f_centro,
                     text="Área restringida — acceso con contraseña de supervisor",
                     fg_color="transparent", text_color=_MUT,
                     font=(_FT, _FS - 1, "italic")).pack(pady=(4, 20))

        ctk.CTkButton(f_centro,
                      text="  [O]  INGRESAR  →",
                      fg_color=_IC_GOLD_BG, text_color=GOLD,
                      font=(_FTM, _FS, "bold"),
                      corner_radius=12, height=48, width=240,
                      border_width=2, border_color=GOLD,
                      hover_color="#2a2000",
                      command=self._on_desbloquear).pack(pady=(0, 30))

        ctk.CTkLabel(f_centro, text="Sesión se bloquea automáticamente\ntras 15 min de inactividad",
                     fg_color="transparent", text_color=_MUT,
                     font=(_FT, max(7, _FS - 4), "italic"),
                     justify="center").pack(pady=(0, 16))


# ════════════════════════════════════════════════════════════════════════════
# IC_Contenedor — orquesta bloqueo ↔ vista, se inyecta en CatalogosMixin
# ════════════════════════════════════════════════════════════════════════════
class IC_Contenedor(ctk.CTkFrame):
    """
    Frame que alterna entre IC_PanelBloqueo e IC_Vista.
    Uso: IC_Contenedor(parent).pack(fill='both', expand=True)
    """

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color="transparent",
                         corner_radius=0, **kw)
        ic_init_db()
        self._vista_activa = None
        self._mostrar_bloqueo()

    def _mostrar_bloqueo(self):
        for w in self.winfo_children(): w.destroy()
        self._vista_activa = None
        panel = IC_PanelBloqueo(self, on_desbloquear=self._pedir_password)
        panel.pack(fill="both", expand=True)

    def _pedir_password(self):
        IC_ModalPassword(self, on_success=self._mostrar_vista)

    def _mostrar_vista(self):
        for w in self.winfo_children(): w.destroy()
        self._vista_activa = IC_Vista(self, on_bloquear=self._mostrar_bloqueo)
        self._vista_activa.pack(fill="both", expand=True)
