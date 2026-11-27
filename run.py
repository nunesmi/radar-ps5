"""Uma verificação completa do radar: coleta -> filtra -> classifica -> alerta -> painel.

Uso:  python run.py            (normal)
      python run.py --dry-run  (não envia alertas nem grava estado)
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

from radar import config, notify, pricing, sources, storage
from radar.http import FetchError
from radar.models import classify_model, norm

DRY = "--dry-run" in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def collect():
    items, logs = [], []
    jobs = [("Pelando", q, sources.pelando_search) for q in config.PELANDO_QUERIES]
    jobs += [("Telegram", q, sources.telegram_search) for q in config.TELEGRAM_QUERIES]
    jobs += [("KaBuM!", q, sources.kabum_search) for q in config.KABUM_QUERIES]
    for src, q, fn in jobs:
        try:
            got = fn(q)
            items.extend(got)
            logs.append({"ts": now_iso(), "source": src, "query": q, "ok": 1, "items": len(got), "error": ""})
        except (FetchError, Exception) as e:
            logs.append({"ts": now_iso(), "source": src, "query": q, "ok": 0, "items": 0, "error": str(e)[:200]})
        time.sleep(1.5)  # gentil com os sites
    # remove duplicados (mesma oferta encontrada por buscas diferentes)
    uniq = {}
    for it in items:
        uniq[(it["source"], it["id"])] = it
    return list(uniq.values()), logs


def main():
    ts = now_iso()
    state = storage.load_state()
    items, logs = collect()
    ok_sources = sum(l["ok"] for l in logs)

    # ---- identificar modelo e loja
    for it in items:
        m = classify_model(it["title"], it["price"], it.get("offer_url", ""))
        it["model"], it["bundle"], it["model_note"] = m["model"], m["bundle"], m["note"]
        it["trust"] = config.TRUSTED_STORES.get(norm(it["store"]))
        it["ts"] = ts

    relevant = [i for i in items if i["model"]]

    # ---- histórico: registra preço novo ou alterado (evita linhas repetidas)
    new_obs = []
    for it in relevant:
        key = f"{it['source']}|{it['id']}"
        last = state["last_seen"].get(key)
        if not last or last["price"] != it["price"] or last["status"] != it["status"]:
            new_obs.append({**it, "price_card": it.get("price_card") or ""})
        state["last_seen"][key] = {"price": it["price"], "status": it["status"], "ts": ts}
    if not DRY:
        storage.append_obs(new_obs)
    obs = storage.load_obs(days=180) + ([] if not DRY else new_obs)

    # ---- classificar
    bases = {m: pricing.baseline(m, obs) for m in config.REFERENCE}
    evaluated = []
    for it in relevant:
        if it["model"] == "modelo_a_confirmar":
            it.update({"classe": "MONITORAR", "desconto": None, "queda": None,
                       "motivo": it["model_note"], "tipico": None, "minimo": None})
            evaluated.append(it)
            continue
        base = bases[it["model"]]
        c = pricing.classify(it["price"], it["model"], base, it["trust"], it["model"] == config.MAIN_PRODUCT)
        it.update(c, tipico=base["tipico"], minimo=base["minimo"], fonte_media=base["fonte"])
        if it["model"] == config.MAIN_PRODUCT and it["price"] < config.PRICE_ERROR_BELOW:
            it["motivo"] += " — possível ERRO DE PREÇO: risco de cancelamento pela loja"
        evaluated.append(it)

    # ---- alertas
    sent = 0
    for it in evaluated:
        if it["status"] != "ativa":
            continue
        is_main = it["model"] == config.MAIN_PRODUCT
        wanted = config.ALERT_CLASSES_MAIN if is_main else config.ALERT_CLASSES_SECONDARY
        # console principal: avisa TODA oferta de loja confiável até o preço máximo configurado
        under_max = (is_main and it["trust"] is not None
                     and it["price"] <= config.ALERT_MAX_PRICE_MAIN)
        if it["classe"] not in wanted and not under_max:
            continue
        key = f"{it['source']}|{it['id']}"
        prev = state["alerted"].get(key)
        if prev and it["price"] > prev["price"] - config.REALERT_DROP:
            continue  # já avisado
        # a mesma oferta pode aparecer no site do Pelando e no Telegram: assinatura loja+modelo+preço
        sig = f"{it['model']}|{norm(it['store'])}|{round(it['price'])}"
        sig_ts = state.setdefault("alerted_sig", {}).get(sig)
        if sig_ts and sig_ts >= (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat():
            continue
        if it["source"] == "Pelando":
            sources.pelando_details(it)
            if it["status"] != "ativa":
                continue
        alert = {
            **it,
            "produto": config.PRODUCT_LABELS.get(it["model"], it["model"]),
            "confiabilidade": {"alta": "Alta", "media": "Média"}.get(it["trust"], "Baixa"),
            "vendedor": it["store"] if it["kind"] == "listing" else None,
            "pagamento": ("Pix (à vista); cartão no valor indicado" if it["kind"] == "listing"
                          else "conforme o post (Pix/cartão/cupom)"),
            "observacao": it["motivo"] + (f". {it['model_note']}" if it.get("model_note") else "")
                          + (f". Post: {it['conditions']}" if it.get("conditions") else "")
                          + (". Oferta vista em canal do Telegram: o canal não informa se ela já acabou — abra rápido"
                             if it["source"].startswith("Telegram") else ""),
            "fonte_media": it.get("fonte_media", ""),
        }
        if not DRY:
            notify.send(notify.build_alert(alert))
            state["alerted"][key] = {"price": it["price"], "ts": ts}
            state["alerted_sig"][sig] = ts
        else:
            print(notify.build_alert(alert)); print("-" * 40)
        sent += 1

    # ---- saúde do monitoramento
    if ok_sources == 0:
        state["fail_streak"] = state.get("fail_streak", 0) + 1
    else:
        state["fail_streak"] = 0
        state["health_alerted"] = False
    if state["fail_streak"] >= config.HEALTH_FAIL_RUNS and not state.get("health_alerted") and not DRY:
        notify.send("⚠️ Radar PS5: todas as fontes falharam nas últimas "
                    f"{state['fail_streak']} verificações. Confira os logs no GitHub.")
        state["health_alerted"] = True

    # limpa memória de ofertas antigas (> 14 dias)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    state["last_seen"] = {k: v for k, v in state["last_seen"].items() if v["ts"] >= cutoff}
    state["last_run"] = ts
    state["last_ok_sources"] = ok_sources

    if not DRY:
        storage.append_log(logs)
        storage.save_state(state)
    write_dashboard(evaluated, obs, bases, logs, state, ts)
    print(f"{ts}: {len(items)} itens, {len(relevant)} relevantes, {sent} alertas, "
          f"{ok_sources}/{len(logs)} consultas ok")


def write_dashboard(evaluated, obs, bases, logs, state, ts):
    os.makedirs(DOCS, exist_ok=True)
    cutoff24 = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    offers = []
    for it in evaluated:
        offers.append({k: it.get(k) for k in (
            "source", "id", "title", "store", "price", "price_card", "status", "kind", "model",
            "bundle", "classe", "desconto", "queda", "motivo", "url", "offer_url", "coupon",
            "created_at", "trust", "installments", "conditions")})
    history = {}
    for r in obs:
        if r["model"] in config.REFERENCE and r["price"]:
            history.setdefault(r["model"], []).append(
                {"ts": r["ts"], "price": r["price"], "store": r["store"], "kind": r["kind"],
                 "status": r["status"], "title": r["title"]})
    data = {
        "updated": ts,
        "status": {
            "last_run": ts,
            "queries_ok": sum(l["ok"] for l in logs),
            "queries_total": len(logs),
            "fail_streak": state.get("fail_streak", 0),
            "logs": logs,
        },
        "labels": config.PRODUCT_LABELS,
        "main": config.MAIN_PRODUCT,
        "baselines": bases,
        "offers": offers,
        "offers_24h_cutoff": cutoff24,
        "history": history,
    }
    with open(os.path.join(DOCS, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


if __name__ == "__main__":
    if "--test-telegram" in sys.argv:
        ok = notify.send("✅ Radar PS5 conectado! Os alertas de promoção vão chegar aqui.")
        print("teste do Telegram:", "enviado" if ok else "FALHOU (confira os secrets)")
        sys.exit(0 if ok else 1)
    if "--loop" in sys.argv:
        # Várias verificações seguidas numa mesma execução do GitHub Actions:
        #   python run.py --loop 5 --every 240   -> 5 verificações, 4 min de intervalo
        n = int(sys.argv[sys.argv.index("--loop") + 1])
        every = int(sys.argv[sys.argv.index("--every") + 1]) if "--every" in sys.argv else 240
        for i in range(n):
            try:
                main()
            except Exception as e:  # uma falha não derruba as próximas verificações
                print(f"verificação {i + 1} falhou: {type(e).__name__}: {e}")
            if i < n - 1:
                time.sleep(every)
    else:
        main()
