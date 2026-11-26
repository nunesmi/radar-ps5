"""Inteligência de preços: preço médio de mercado, menor preço e classificação."""
import statistics
from datetime import datetime, timedelta, timezone

from . import config


def baseline(model: str, obs: list[dict]) -> dict:
    """Preço médio de mercado do modelo.

    Usa a MEDIANA dos preços de vitrine (listings) das lojas nos últimos 30 dias.
    Ofertas relâmpago da comunidade NÃO entram na média, para não confundir preço
    promocional com preço habitual. Sem dados suficientes, usa a referência.
    """
    ref = config.REFERENCE.get(model, {})
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.BASELINE_WINDOW_DAYS)
    def is_bundle(r):
        return str(r.get("bundle")) == "True"

    listings = [
        r for r in obs
        if r["model"] == model and r["kind"] == "listing" and r["price"] and not is_bundle(r)
        and datetime.fromisoformat(r["ts"]) >= cutoff
    ]
    stores = {r["store"] for r in listings}
    if (len(listings) >= config.MIN_OBS_FOR_OWN_BASELINE
            and len(stores) >= config.MIN_STORES_FOR_OWN_BASELINE):
        typical, src = statistics.median(r["price"] for r in listings), "mediana das lojas (30 dias)"
    else:
        typical, src = ref.get("tipico"), "referência de mercado"
    # Menor preço: só lojas confiáveis, sem kits, e descartando valores absurdos (erro/outlier)
    floor = 0.5 * typical if typical else 0
    trusted = [
        r["price"] for r in obs
        if r["model"] == model and r["price"] and not is_bundle(r) and r["price"] >= floor
        and config.TRUSTED_STORES.get((r["store"] or "").strip().lower())
    ]
    known_min = min(trusted + ([ref["minimo"]] if ref.get("minimo") else []), default=None)
    return {"tipico": typical, "fonte": src, "minimo": known_min, "n_obs": len(listings), "lojas": sorted(stores)}


def classify(price: float, model: str, base: dict, trust: str | None, is_main: bool) -> dict:
    if trust is None:
        return {"classe": "DESCARTAR", "desconto": None, "queda": None,
                "motivo": "loja fora da lista de confiáveis"}
    typical = base.get("tipico")
    if not typical:
        return {"classe": "MONITORAR", "desconto": None, "queda": None,
                "motivo": "sem histórico suficiente para este modelo"}
    drop = typical - price
    disc = drop / typical
    below_min = base.get("minimo") is not None and price < base["minimo"]
    classe = "MONITORAR" if drop > 0 else "DESCARTAR"
    motivo = "preço igual ou acima do habitual" if drop <= 0 else "abaixo do habitual, mas pode melhorar"
    for name, (pct, abs_drop) in config.CLASS_RULES.items():  # ordem: do melhor para o pior
        hit = disc >= pct or (is_main and drop >= abs_drop)
        if name == "EXCEPCIONAL" and below_min and is_main and disc >= 0.10:
            hit = True
        if hit:
            classe = name
            motivo = {
                "EXCEPCIONAL": "muito abaixo do mercado" + (" e abaixo do menor preço já visto" if below_min else ""),
                "IMPERDÍVEL": "desconto real expressivo frente ao histórico",
                "BOA OFERTA": "preço competitivo",
            }[name]
            break
    # Produtos secundários só são EXCEPCIONAIS se também estiverem no menor preço já visto (±5%)
    if (not is_main and classe == "EXCEPCIONAL" and base.get("minimo")
            and price > base["minimo"] * 1.05):
        classe, motivo = "IMPERDÍVEL", "desconto real expressivo, mas acima do menor preço já visto"
    if trust == "media" and classe == "EXCEPCIONAL":
        motivo += " (marketplace: confira se o vendedor é a plataforma ou loja oficial)"
    return {"classe": classe, "desconto": round(disc * 100, 1), "queda": round(drop, 2), "motivo": motivo}
