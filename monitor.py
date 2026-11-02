import os, json, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URL = "https://www.unifg.it/it/studiare/post-lauream/formazione-insegnanti/tfa-sostegno/tfa-sostegno-aa-2025-2026/tfa-sostegno-aa-2025-2026-idonei-cicli-precedenti"
STATE = Path("monitor-state.json")
STATUS = Path("status.json")
KEYWORDS = re.compile(r"calendari|calendario|lezion|didattic|orario|schedule", re.I)

def main():
    r = requests.get(URL, timeout=40, headers={"User-Agent":"Mozilla/5.0 TFA-UniFG-monitor/1.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for a in soup.find_all("a", href=True):
        label = " ".join(a.get_text(" ", strip=True).split())
        href = a["href"].strip()
        if KEYWORDS.search(label + " " + href):
            if href.startswith("/"):
                href = "https://www.unifg.it" + href
            items.append({"title": label or href, "url": href})
    # Include relevant visible page text to catch calendar date/notice edits.
    relevant_text = []
    for node in soup.find_all(["h1","h2","h3","p","li"]):
        t = " ".join(node.get_text(" ", strip=True).split())
        if t and KEYWORDS.search(t):
            relevant_text.append(t)
    snapshot = {"items": sorted(items, key=lambda x:(x["url"],x["title"])),
                "text": sorted(set(relevant_text))}
    digest = hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    previous = json.loads(STATE.read_text()) if STATE.exists() else None
    now = datetime.now(timezone.utc).isoformat()
    changed = previous is not None and previous.get("digest") != digest
    STATUS.write_text(json.dumps({
        "checked_at": now,
        "last_change": "Rilevata una modifica ai riferimenti del calendario" if changed else (previous or {}).get("last_change",""),
        "items": snapshot["items"]
    }, ensure_ascii=False, indent=2))
    if changed:
        topic = os.environ.get("NTFY_TOPIC","").strip()
        if not topic:
            raise RuntimeError("Manca il secret NTFY_TOPIC nelle impostazioni GitHub.")
        title = "TFA UniFG: possibile aggiornamento calendario"
        message = "È stata rilevata una modifica alla pagina TFA Sostegno UniFG. Apri la pagina ufficiale e verifica il nuovo calendario: " + URL
        token = os.environ.get("NTFY_TOKEN","").strip()
        headers = {"Title": title, "Priority":"high", "Tags":"calendar"}
        if token:
            headers["Authorization"] = "Bearer " + token
        resp = requests.post("https://ntfy.sh/" + topic, data=message.encode(), headers=headers, timeout=30)
        resp.raise_for_status()
    STATE.write_text(json.dumps({"digest":digest,"snapshot":snapshot,"last_change":(previous or {}).get("last_change","") if not changed else "Modifica rilevata"}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
