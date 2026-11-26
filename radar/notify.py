"""Envio de alertas pelo Telegram (Bot API oficial).

Precisa das variáveis de ambiente TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID
(cadastradas como *secrets* no GitHub). Sem elas, o alerta só é impresso no log.
"""
import html
import json
import os
import urllib.request


def _fmt(v):
    if v is None:
        return "—"
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_alert(o: dict) -> str:
    e = html.escape
    lines = [
        "🚨 <b>PROMOÇÃO ENCONTRADA!</b>",
        f"<b>Produto:</b> {e(o['produto'])}" + (" (kit com jogos)" if o.get("bundle") else ""),
        f"<b>Anúncio:</b> {e(o['title'])}",
        f"<b>Preço atual:</b> {_fmt(o['price'])}"
        + (f" (cartão: {_fmt(o['price_card'])}" + (f", {e(o['installments'])}" if o.get('installments') else "") + ")" if o.get("price_card") and o["price_card"] != o["price"] else ""),
        f"<b>Preço médio recente:</b> {_fmt(o['tipico'])} ({e(o['fonte_media'])})",
        f"<b>Menor preço histórico identificado:</b> {_fmt(o['minimo'])}",
        f"<b>Desconto real:</b> {o['desconto']}% ({_fmt(o['queda'])} abaixo da média)",
        f"<b>Forma de pagamento:</b> {e(o.get('pagamento') or 'ver anúncio')}",
        f"<b>Cupom:</b> <code>{e(o['coupon'])}</code>" if o.get("coupon") else "<b>Cupom:</b> nenhum informado",
        f"<b>Loja:</b> {e(o['store'])}",
        f"<b>Vendedor:</b> {e(o.get('vendedor') or 'confira no anúncio')}",
        f"<b>Confiabilidade:</b> {e(o['confiabilidade'])}",
        f"<b>Classificação:</b> {e(o['classe'])}",
        f"<b>Link direto:</b> {e(o['offer_url'] or o['url'])}",
    ]
    if o.get("url") and o.get("offer_url") and o["url"] != o["offer_url"]:
        lines.append(f"<b>Post da oferta:</b> {e(o['url'])}")
    lines.append(f"<b>Observação:</b> {e(o['observacao'])}")
    return "\n".join(lines)


def send(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("[alerta - Telegram não configurado]\n" + text)
        return False
    body = json.dumps({"chat_id": chat, "text": text, "parse_mode": "HTML",
                       "disable_web_page_preview": False}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=body,
        headers={"Content-Type": "application/json"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read()).get("ok", False)
        except Exception as ex:  # não imprimir a URL (contém o token)
            print(f"[telegram] falha ao enviar: {type(ex).__name__}")
    return False
