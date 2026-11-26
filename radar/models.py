"""Identificação do modelo a partir do título do anúncio.

Regra de ouro: o console principal só é reconhecido quando há evidência clara de
PS5 Slim + 1 TB + leitor de disco. Qualquer dúvida vira "modelo_a_confirmar",
que nunca gera alerta.
"""
import re
import unicodedata

from .config import KNOWN_DISC_CATALOG_IDS


def norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t.lower()).strip()


REJECT = re.compile(
    r"\b(usad[oa]|seminov[oa]|recondicionad[oa]|vitrine|mostruario|open ?box|"
    r"import(ado|ada)|sem garantia|defeito|para pecas|capa|skin|adesivo|suporte|"
    r"base|carregador|dock|estacao|cooler|case|bolsa|tampa|faceplate|grip|pelicula|"
    r"volante|headset|fone|camera|pulse|portal|bateria|gatilho|analogico|thumb)\b"
)
DISC = re.compile(r"\b(leitor|disk|disco|disc|midia fisica|fisica|blu-?ray)\b")
DIGITAL = re.compile(r"\b(digital|sem leitor)\b")
ONE_TB = re.compile(r"\b1 ?tb\b")
CONSOLE_HINT = re.compile(r"\b(console|playstation ?5|ps ?5)\b")
SLIM = re.compile(r"\bslim\b")
PRO = re.compile(r"\b(ps ?5|playstation ?5) pro\b")
SLIM_DISC_CODES = re.compile(r"\bcfi-?2(0|1)1[45]\b")
SPECIAL_DS = re.compile(
    r"\b(chroma|edicao limitada|limited|wolverine|gta|techno|remix|rhythm|30th|aniversario|"
    r"astro ?bot|fortnite|god of war|spider|death stranding|prism)\b")
BUNDLE = re.compile(r"(\+|\bcom\b|\bpacote\b|\bbundle\b|\bkit\b).{0,40}\b(jogo|jogos|game|astro|gran turismo|ghost|spider|god of war|returnal|ratchet|fc ?2\d|gta)")


def classify_model(title: str, price: float | None = None, url: str = "") -> dict:
    """Retorna {'model': str|None, 'bundle': bool, 'note': str}."""
    t = norm(title)
    out = {"model": None, "bundle": bool(BUNDLE.search(t)), "note": ""}

    if REJECT.search(t):
        out["note"] = "descartado: usado/importado/acessório não original"
        return out

    # Controles
    looks_controller = "dualsense" in t or ("controle" in t and CONSOLE_HINT.search(t) and "console" not in t)
    if looks_controller and (price is None or price < 1500):
        if "access" in t:
            out["note"] = "controle Access (fora do escopo)"
            return out
        if "edge" not in t and price is not None and price < 140:
            out["note"] = "preço incompatível com DualSense original (acessório/paralelo)"
            return out
        out["model"] = "dualsense_edge" if "edge" in t else (
            "dualsense_especial" if SPECIAL_DS.search(t) else "dualsense")
        if "console" in t:  # "console ... com controle dualsense"
            out["model"] = None
        else:
            return out

    if not CONSOLE_HINT.search(t):
        return out

    # Leitor de disco vendido separadamente
    if re.search(r"\bleitor\b", t) and "console" not in t and (price is not None and price < 1500):
        out["note"] = "leitor de disco avulso (fora do escopo)"
        return out

    if PRO.search(t):
        out["model"] = "ps5_pro"
        return out

    if DIGITAL.search(t):
        out["model"] = "ps5_slim_digital"
        return out

    if "825" in t:
        out["note"] = "modelo 825 GB (fora do escopo)"
        return out

    if price is not None and price < 1500:
        return out  # jogo/acessório com "PS5" no título

    catalog_ok = any(cid in (url or "") for cid in KNOWN_DISC_CATALOG_IDS)
    disc = bool(DISC.search(t)) or catalog_ok
    # O único PS5 com leitor de 1 TB vendido hoje é o Slim (CFI-2014/2114);
    # "Slim Disk" sem "1TB" no título também é 1 TB.
    if disc and (ONE_TB.search(t) or SLIM.search(t) or SLIM_DISC_CODES.search(t)):
        out["model"] = "ps5_slim_disco_1tb"
        if catalog_ok and not DISC.search(t):
            out["note"] = "leitor confirmado pelo código do catálogo"
        return out

    out["model"] = "modelo_a_confirmar"
    out["note"] = "título não comprova leitor de disco + 1 TB"
    return out
