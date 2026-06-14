class Theme:
    """Paleta y tokens de diseño de la aplicación.

    Se conservan los nombres históricos (PRIMARY, CARD_BG_N1...) por
    retrocompatibilidad y se añaden tokens semánticos (SURFACE, BORDER,
    TEXT_MUTED, ACCENT...) para usar la MISMA paleta verde bosque de forma
    coherente y profesional. Evita colores sueltos fuera de paleta en las
    páginas: usa estos tokens.
    """

    # =========================================================
    # Marca (paleta original verde bosque)
    # =========================================================
    DARKEST = "#051F20"          # Verde casi negro (sidebar / texto fuerte)
    DARK = "#0B2B26"
    PRIMARY = "#235347"          # Forest Green — acción principal
    PRIMARY_HOVER = "#163832"
    BRAND = "#235347"
    TRANSPARENT = "transparent"

    SECONDARY = "#8EB69B"        # Sage Green
    SECONDARY_HOVER = "#235347"

    ACCENT = "#8EB69B"           # Resaltados / selección
    ACCENT_SOFT = "#B7CCBE"

    # =========================================================
    # Superficies — tuplas (claro, oscuro) para soportar modo oscuro.
    # CustomTkinter selecciona el elemento según el modo de apariencia.
    # =========================================================
    BACKGROUND = ("#DAF1DE", "#0A1F1C")   # Fondo de la app
    SURFACE = ("#FFFFFF", "#10302A")      # Tarjetas principales
    SURFACE_2 = ("#F2F8F3", "#15392F")    # Tarjetas/inputs secundarios
    BORDER = ("#C5D9CD", "#2B4A40")       # Bordes sutiles
    SIDEBAR_BG = ("#051F20", "#04161A")   # Barra lateral (verde oscuro)

    # =========================================================
    # Texto — tuplas (claro, oscuro)
    # =========================================================
    TEXT_MAIN = ("#051F20", "#E4F2E8")
    TEXT_MUTED = ("#5A726A", "#9DB4A8")   # Gris verdoso (no gris neutro)
    TEXT_WHITE = "#FFFFFF"
    TEXT_ON_DARK = "#DAF1DE"

    # =========================================================
    # Escala de tarjetas del dashboard (tinte por categoría)
    # =========================================================
    CARD_BG_N1 = "#8EB69B"
    CARD_BG_N2 = "#99BDA5"
    CARD_BG_N3 = "#A4C4AF"
    CARD_BG_N4 = "#AFCBB9"
    CARD_BG_N5 = "#BAD2C3"
    CARD_BG_N6 = "#C5D9CD"
    CARD_BG_N7 = "#D0E0D7"
    CARD_BG_N8 = "#DAF1DE"

    # =========================================================
    # Colores semánticos (derivados de la MISMA paleta)
    # =========================================================
    SUCCESS = "#235347"          # Verde de marca (¡no el teal #2CC985!)
    SUCCESS_HOVER = "#163832"

    WARNING = "#B58B00"          # Ámbar discreto, solo para avisos
    WARNING_HOVER = "#946F00"

    DANGER = "#8B2E2E"           # Rojo apagado coherente con el tono
    DANGER_HOVER = "#A33A3A"

    # =========================================================
    # Tipografía
    # =========================================================
    FONT_FAMILY = "Segoe UI"
    TITLE_SIZE = 24
    HEADER_SIZE = 20
    BODY_SIZE = 14

    # Escala de tamaños tipográficos
    SIZE = {"xs": 11, "sm": 13, "md": 14, "lg": 18, "xl": 24, "display": 28}

    # =========================================================
    # Espaciado y radios (consistencia visual)
    # =========================================================
    RADIUS = {"sm": 8, "md": 12, "lg": 16, "pill": 999}
    PAD = {"xs": 4, "sm": 8, "md": 12, "lg": 20, "xl": 32}
