"""Requisições HTTP com novas tentativas (somente biblioteca padrão)."""
import time
import urllib.error
import urllib.request

from .config import USER_AGENT


class FetchError(Exception):
    pass


def get(url: str, attempts: int = 3, timeout: int = 25) -> str:
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
                    "Accept-Language": "pt-BR,pt;q=0.9",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (403, 404):  # bloqueio/inexistente: não insistir
                break
        except Exception as e:  # rede, timeout
            last = f"{type(e).__name__}: {e}"
        time.sleep(2 * (i + 1))
    raise FetchError(f"{url} -> {last}")
