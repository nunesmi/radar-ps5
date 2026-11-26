"""Descobre o TELEGRAM_CHAT_ID e manda uma mensagem de teste.

1. Crie o bot no @BotFather e mande qualquer mensagem (ex.: "oi") para o seu bot.
2. Rode:  python tools/descobrir_chat_id.py
3. Cole o token quando pedir (ele não aparece na tela e não é salvo em lugar nenhum).
"""
import getpass
import json
import urllib.request

token = getpass.getpass("Cole o token do bot (não aparece na tela): ").strip()
base = f"https://api.telegram.org/bot{token}"
try:
    with urllib.request.urlopen(base + "/getUpdates", timeout=20) as r:
        upd = json.loads(r.read())
except Exception as e:
    raise SystemExit(f"Não consegui falar com o Telegram ({type(e).__name__}). Confira o token.")

chats = {u["message"]["chat"]["id"]: u["message"]["chat"].get("first_name", "")
         for u in upd.get("result", []) if "message" in u}
if not chats:
    raise SystemExit("Nenhuma mensagem encontrada. Mande um 'oi' para o seu bot no Telegram e rode de novo.")

for cid, name in chats.items():
    print(f"TELEGRAM_CHAT_ID = {cid}   ({name})")
    body = json.dumps({"chat_id": cid, "text": "✅ Radar PS5 conectado! Os alertas vão chegar aqui."}).encode()
    req = urllib.request.Request(base + "/sendMessage", data=body, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20)
print("Mensagem de teste enviada. Use o número acima no secret TELEGRAM_CHAT_ID do GitHub.")
