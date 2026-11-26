"""Coletores de ofertas. Cada coletor devolve uma lista de dicts padronizados:

{source, id, title, store, price, price_card, status, created_at, url, offer_url,
 coupon, kind}

kind = "deal"   -> oferta publicada pela comunidade (Pelando)
kind = "listing"-> preço de vitrine da própria loja (KaBuM!)
"""
import html
import json
import re
import urllib.parse
from datetime import datetime, timezone

from . import http


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- Pelando
def _astro_decode(v):
    """Decodifica a serialização de props do Astro ([tipo, valor])."""
    if isinstance(v, list) and len(v) == 2 and isinstance(v[0], int):
        t, x = v
        if t == 0:
            return {k: _astro_decode(i) for k, i in x.items()} if isinstance(x, dict) else x
        if t == 1:
            return [_astro_decode(i) for i in x]
        return x
    if isinstance(v, dict):
        return {k: _astro_decode(i) for k, i in v.items()}
    return v


def _walk_deals(o):
    if isinstance(o, dict):
        if "slug" in o and "price" in o and "status" in o:
            yield o
        for v in o.values():
            yield from _walk_deals(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk_deals(v)


def _pelando_props(page: str):
    for p in re.findall(r'<astro-island[^>]*?props="([^"]*)"', page):
        try:
            yield _astro_decode(json.loads(html.unescape(p)))
        except Exception:
            continue


def pelando_search(query: str) -> list[dict]:
    url = "https://www.pelando.com.br/busca/" + urllib.parse.quote(query)
    page = http.get(url)
    seen, out = set(), []
    for props in _pelando_props(page):
        for d in _walk_deals(props):
            if d.get("price") is None or d.get("kind") not in (None, "promotion"):
                continue
            if d["id"] in seen:
                continue
            seen.add(d["id"])
            store = (d.get("store") or {}).get("name") or ""
            out.append({
                "source": "Pelando",
                "id": d["id"],
                "title": d.get("title") or "",
                "store": store,
                "price": float(d["price"]),
                "price_card": None,
                "status": "ativa" if d.get("status") == "active" else "expirada",
                "created_at": d.get("createdAt") or _now(),
                "url": "https://www.pelando.com.br/d/" + d["slug"],
                "offer_url": d.get("sourceUrl") or "",
                "coupon": None,
                "cashback": d.get("cashback"),
                "kind": "deal",
            })
    return out


def pelando_details(deal: dict) -> dict:
    """Busca cupom e link limpo na página da oferta (só para candidatas a alerta)."""
    try:
        page = http.get(deal["url"])
    except http.FetchError:
        return deal
    for props in _pelando_props(page):
        for d in _walk_deals(props):
            if d.get("id") != deal["id"]:
                continue
            deal["coupon"] = d.get("couponCode") or deal.get("coupon")
            deal["offer_url"] = d.get("sourceUrl") or deal.get("offer_url")
            deal["status"] = "ativa" if d.get("status") == "active" else "expirada"
            return deal
    return deal


# --------------------------------------------------------------------------- KaBuM!
def kabum_search(slug: str) -> list[dict]:
    url = "https://www.kabum.com.br/busca/" + slug
    page = http.get(url)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    if not m:
        raise http.FetchError(f"{url} -> sem dados estruturados")
    data = json.loads(m.group(1))["props"]["pageProps"].get("data")
    if isinstance(data, str):
        data = json.loads(data)
    items = (((data or {}).get("catalogServer") or {}).get("data")) or []
    out = []
    for p in items:
        if not p.get("available"):
            continue
        seller = p.get("sellerName") or "KaBuM!"
        if norm_seller(seller) != "kabum!":
            continue  # só vendido pela própria KaBuM!
        pix = p.get("priceWithDiscount") or p.get("price")
        out.append({
            "source": "KaBuM!",
            "id": f"kabum-{p['code']}",
            "title": p.get("name") or "",
            "store": "KaBuM!",
            "price": float(pix),
            "price_card": float(p.get("price") or pix),
            "status": "ativa",
            "created_at": _now(),
            "url": f"https://www.kabum.com.br/produto/{p['code']}/{p.get('friendlyName', '')}",
            "offer_url": f"https://www.kabum.com.br/produto/{p['code']}/{p.get('friendlyName', '')}",
            "coupon": None,
            "cashback": None,
            "installments": p.get("maxInstallment"),
            "stock": p.get("quantity"),
            "kind": "listing",
        })
    return out


def norm_seller(s: str) -> str:
    return (s or "").strip().lower()
