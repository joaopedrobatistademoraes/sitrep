#!/usr/bin/env python3
"""
SITREP Fetcher — chama a API do Claude com web search
e salva o resultado em public/data.json
"""

import os
import json
import time
from datetime import datetime, timezone
import urllib.request
import urllib.error

API_KEY = os.environ["ANTHROPIC_API_KEY"]
API_URL = "https://api.anthropic.com/v1/messages"
TODAY   = datetime.now(timezone.utc).strftime("%d/%m/%Y")

# ── Configuração das 4 seções ────────────────────────────────────────────────

SECTIONS = [
    {
        "key": "conflict",
        "system": f"You are a military OSINT analyst. Today is {TODAY}. Use web search to find the latest news. Return ONLY a valid JSON object. No markdown, no backticks, no extra text.",
        "user": (
            "Search for the very latest news today on the Israel/USA/Iran military conflict "
            "and any Middle East escalation. Return this exact JSON:\n"
            '{"phase":"GUERRA ATIVA","alert_level":"CRÍTICO","summary":"2-3 sentences",'
            '"key_events":["event1","event2","event3","event4"],'
            '"us_israel_actions":["a1","a2","a3"],'
            '"iran_actions":["a1","a2","a3"],'
            '"regional_actors":[{"actor":"name","status":"brief"}],'
            f'"updated_at":"{datetime.now(timezone.utc).strftime("%H:%M")} {TODAY}"}}'
        ),
    },
    {
        "key": "markets",
        "system": f"You are a financial analyst. Today is {TODAY}. Use web search for real-time data. Return ONLY valid JSON, no markdown, no backticks.",
        "user": (
            "Search for current Brent crude price, WTI crude price, S&P500/Dow/Nasdaq futures, gold. "
            "Return this exact JSON:\n"
            '{"brent_price":"XX.XX","brent_change":"+X.XX%",'
            '"wti_price":"XX.XX","wti_change":"+X.XX%",'
            '"futures":[{"index":"S&P 500","change":"-X.XX%"},{"index":"Dow Jones","change":"-XXX pts"},{"index":"Nasdaq","change":"-X.XX%"}],'
            '"safe_havens":["Gold ▲ $XXXX","USD ▲","Treasuries alta"],'
            '"analysis":"brief market outlook",'
            f'"updated_at":"{datetime.now(timezone.utc).strftime("%H:%M")} {TODAY}"}}'
        ),
    },
    {
        "key": "airspace",
        "system": f"You are an aviation safety analyst. Today is {TODAY}. Use web search. Return ONLY valid JSON, no markdown, no backticks.",
        "user": (
            "Search for current Middle East airspace closures and airline suspensions due to the conflict. "
            "Return this exact JSON:\n"
            '{"airspace":[{"country":"Iran","flag":"🇮🇷","status":"FECHADO","detail":"brief note"}],'
            '"suspended_airlines":["airline1","airline2"],'
            f'"updated_at":"{datetime.now(timezone.utc).strftime("%H:%M")} {TODAY}"}}'
        ),
    },
    {
        "key": "maritime",
        "system": f"You are a maritime intelligence analyst. Today is {TODAY}. Use web search. Return ONLY valid JSON, no markdown, no backticks.",
        "user": (
            "Search for Strait of Hormuz shipping traffic, tanker incidents, shipping company decisions today. "
            "Return this exact JSON:\n"
            '{"hormuz_drop":"XX%","alert_level":"CRÍTICO",'
            '"incidents":["i1","i2","i3"],'
            '"shipping_companies":[{"company":"name","action":"brief"}],'
            '"routes":[{"route":"Estreito de Ormuz","status":"⛔ FECHADO"},{"route":"Canal de Suez","status":"⛔ FECHADO"},{"route":"Cabo da Boa Esperança","status":"✅ ALTERNATIVA"}],'
            '"analysis":"brief trade impact",'
            f'"updated_at":"{datetime.now(timezone.utc).strftime("%H:%M")} {TODAY}"}}'
        ),
    },
]


def call_claude(system: str, user: str, retries: int = 3) -> dict:
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "system": system,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "messages": [{"role": "user", "content": user}],
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
    }

    for attempt in range(retries):
        try:
            req = urllib.request.Request(API_URL, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = json.loads(resp.read())

            text = "".join(
                b.get("text", "") for b in raw.get("content", []) if b.get("type") == "text"
            )

            # strip possible markdown fences
            cleaned = text.replace("```json", "").replace("```", "").strip()

            # find JSON object
            start = cleaned.find("{")
            end   = cleaned.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in response")

            return json.loads(cleaned[start:end])

        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                raise


def main():
    results = {}
    errors  = {}

    for section in SECTIONS:
        key = section["key"]
        print(f"[{key.upper()}] Fetching...", flush=True)
        try:
            data = call_claude(section["system"], section["user"])
            results[key] = data
            print(f"[{key.upper()}] ✓ OK", flush=True)
        except Exception as e:
            errors[key] = str(e)
            print(f"[{key.upper()}] ✗ FAILED: {e}", flush=True)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sections": results,
        "errors": errors,
    }

    os.makedirs("public", exist_ok=True)
    out_path = "public/data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved → {out_path}")
    print(f"Sections OK: {list(results.keys())}")
    if errors:
        print(f"Sections FAILED: {errors}")
        # exit 1 only if ALL sections failed
        if len(errors) == len(SECTIONS):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
