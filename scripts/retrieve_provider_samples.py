#!/usr/bin/env python3
"""Fetch small optional samples from public and configured key-gated providers."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._path_integrity import PathIntegrityError, path_error_payload, safe_input_file, safe_output_dir

import argparse
import hashlib
import json
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from strategy_validator.contracts.provider_capabilities import (
    ProviderAccessType,
    all_provider_capabilities,
    capability_by_provider_id,
)

from scripts.provider_sample_public import (
    CLASS_PENDING_BROKER,
    CLASS_PENDING_KEY,
    CLASS_POLICY_SKIP,
    CLASS_SKIPPED_NO_NETWORK,
    analyze_sample_body,
    classify_keyed_fetch,
    classify_public_fetch,
    normalized_metadata_for_manifest,
    redact_secret_in_url,
)

TIMEOUT_S = 15
BROWSER_COMPAT_UA = (
    "Mozilla/5.0 (compatible; StrategyValidatorSamples/1.0; +https://example.invalid/contact)"
)


def _browser_ua_headers() -> dict[str, str]:
    return {"User-Agent": BROWSER_COMPAT_UA, "Accept": "application/json,*/*;q=0.8"}

CLI_ALIASES: dict[str, str] = {
    "sec": "sec_edgar",
    "world_bank": "world_bank_open_data",
    "imf": "imf_data",
    "binance": "binance_public",
    "kraken": "kraken_public",
}

PUBLIC_DEFAULT_ORDER: tuple[str, ...] = (
    "sec_edgar",
    "world_bank_open_data",
    "ecb",
    "eurostat",
    "oecd",
    "imf_data",
    "bls",
    "gdelt",
    "binance_public",
    "kraken_public",
)


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if "#" in value and not (value.startswith('"') or value.startswith("'")):
            value = value.split("#", 1)[0].rstrip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            values[key] = value
    return values


def _merged_env(*, env_file: Path | None) -> dict[str, str]:
    import os

    merged = dict(os.environ)
    if env_file and env_file.is_file():
        for key, value in _parse_env_file(env_file).items():
            merged[key] = value
    return merged


def _truthy(raw: str | None) -> bool:
    if raw is None:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _first_key(env: dict[str, str], names: tuple[str, ...]) -> str | None:
    for name in names:
        raw = env.get(name, "").strip()
        if raw and raw.upper() not in {"CHANGEME", "REPLACE_ME", "YOUR_KEY_HERE"}:
            return raw
    return None


def _http_get(
    url: str,
    headers: Mapping[str, str] | None = None,
    *,
    timeout: float | None = None,
) -> tuple[int, bytes, str | None]:
    req = Request(url, headers=dict(headers or {}), method="GET")
    wait = TIMEOUT_S if timeout is None else timeout
    try:
        with urlopen(req, timeout=wait) as resp:  # noqa: S310
            body = resp.read()
            return int(getattr(resp, "status", 200)), body, None
    except HTTPError as exc:
        try:
            body = exc.read()
        except OSError:
            body = b""
        return int(exc.code), body, str(exc)
    except URLError as exc:
        return -1, b"", str(exc)
    except OSError as exc:
        return -1, b"", str(exc)


@dataclass
class SampleRecord:
    provider_id: str
    endpoint: str
    retrieved_at_utc: str
    query_params: dict[str, str]
    status: str
    classified_status: str
    http_status: int
    sha256: str
    sample_path: str
    trust_level: str
    pit_suitability: str
    notes: str
    normalized_metadata: dict[str, Any] = field(default_factory=dict)

    def as_manifest_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "provider_id": self.provider_id,
            "endpoint": self.endpoint,
            "retrieved_at_utc": self.retrieved_at_utc,
            "query_params": dict(sorted(self.query_params.items())),
            "status": self.status,
            "classified_status": self.classified_status,
            "http_status": self.http_status,
            "sha256": self.sha256,
            "sample_path": self.sample_path,
            "trust_level": self.trust_level,
            "pit_suitability": self.pit_suitability,
            "notes": self.notes,
            "normalized_metadata": normalized_metadata_for_manifest(self.normalized_metadata),
        }
        return dict(sorted(d.items()))


def _cap() -> dict[str, Any]:
    return {p.provider_id: p for p in all_provider_capabilities()}


def _classified_for_stub(status: str) -> str:
    if status == "PENDING_KEY":
        return CLASS_PENDING_KEY
    if status == "PENDING_MANUAL_BROKER_SETUP":
        return CLASS_PENDING_BROKER
    if status == "POLICY_SKIP":
        return CLASS_POLICY_SKIP
    return CLASS_SKIPPED_NO_NETWORK


def _stub_record(
    pid: str,
    *,
    endpoint: str,
    params: dict[str, str],
    notes: str,
    status: str = "SKIPPED_NO_NETWORK",
) -> SampleRecord:
    cap = _cap().get(pid)
    trust = cap.default_trust_level.value if cap else "UNAVAILABLE"
    pit = cap.pit_suitability.value if cap else "NOT_PIT_SAFE_WITHOUT_ARCHIVE"
    body = json.dumps({"stub": True, "provider_id": pid, "notes": notes}, indent=2).encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()
    return SampleRecord(
        provider_id=pid,
        endpoint=endpoint,
        retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
        query_params=params,
        status=status,
        classified_status=_classified_for_stub(status),
        http_status=-2,
        sha256=digest,
        sample_path=f"{pid}.json",
        trust_level=trust,
        pit_suitability=pit,
        notes=notes,
        normalized_metadata={},
    )


def _write_sample(out_dir: Path, pid: str, body: bytes, ext: str) -> str:
    name = f"{pid}.{ext}"
    path = out_dir / name
    path.write_bytes(body)
    return name


def _transport_label(http_code: int) -> str:
    return "OK" if http_code == 200 else f"HTTP_{http_code}"


def _extension_for_kind(kind: str) -> str:
    return {"json": "json", "xml": "xml", "csv_like": "csv"}.get(kind, "txt")


def _finalize_public_bytes(
    pid: str,
    url: str,
    params: dict[str, str],
    code: int,
    body: bytes,
    err: str | None,
    out_dir: Path,
) -> SampleRecord:
    classified, meta = classify_public_fetch(code, err, body)
    ext = "txt"
    if code == 200:
        kind, _ = analyze_sample_body(body)
        ext = _extension_for_kind(kind)
    raw = body if body else b""
    name = _write_sample(out_dir, pid, raw, ext)
    cap = _cap()[pid]
    return SampleRecord(
        provider_id=pid,
        endpoint=url,
        retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
        query_params=params,
        status=_transport_label(code),
        classified_status=classified,
        http_status=code,
        sha256=hashlib.sha256(raw).hexdigest(),
        sample_path=name,
        trust_level=cap.default_trust_level.value,
        pit_suitability=cap.pit_suitability.value,
        notes=(err or "")[:500],
        normalized_metadata=normalized_metadata_for_manifest(meta),
    )


def _public_download(
    pid: str,
    url: str,
    params: dict[str, str],
    env: dict[str, str],
    no_network: bool,
    out_dir: Path,
    *,
    headers: Mapping[str, str] | None = None,
    timeout: float | None = None,
) -> SampleRecord:
    if no_network:
        rec = _stub_record(pid, endpoint=url, params=params, notes="no_network mode")
        _write_sample(out_dir, pid, json.dumps({"note": rec.notes}, indent=2).encode(), "json")
        return rec
    code, body, err = _http_get(url, headers=headers, timeout=timeout)
    return _finalize_public_bytes(pid, url, params, code, body, err, out_dir)


def fetch_sec_edgar(env: dict[str, str], no_network: bool, out_dir: Path) -> SampleRecord:
    url = "https://data.sec.gov/submissions/CIK0000320193.json"
    params = {"cik": "0000320193"}
    ua = (
        env.get("SEC_USER_AGENT")
        or env.get("SEC_EDGAR_USER_AGENT")
        or "StrategyValidatorSamples/1.0 (local research; https://example.invalid/contact)"
    )
    if no_network:
        rec = _stub_record("sec_edgar", endpoint=url, params=params, notes="no_network mode")
        _write_sample(out_dir, "sec_edgar", json.dumps({"note": rec.notes}, indent=2).encode(), "json")
        return rec
    code, body, err = _http_get(url, headers={"User-Agent": ua, "Accept": "application/json"})
    return _finalize_public_bytes("sec_edgar", url, params, code, body, err, out_dir)


def _registry_fetchers() -> dict[str, Callable[[dict[str, str], bool, Path], SampleRecord]]:
    def wb(env: dict[str, str], no_network: bool, out_dir: Path) -> SampleRecord:
        url = "https://api.worldbank.org/v2/country/US/indicator/SP.POP.TOTL?format=json&per_page=5"
        return _public_download(
            "world_bank_open_data",
            url,
            {"country": "US", "indicator": "SP.POP.TOTL"},
            env,
            no_network,
            out_dir,
        )

    def ecb(env: dict[str, str], no_network: bool, out_dir: Path) -> SampleRecord:
        url = (
            "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"
            "?startPeriod=2023-01&format=jsondata"
        )
        return _public_download("ecb", url, {"series": "10Y_YC"}, env, no_network, out_dir)

    def eurostat(env: dict[str, str], no_network: bool, out_dir: Path) -> SampleRecord:
        url = (
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_gind"
            "?format=JSON&lang=en&geo=EU27_2020&indic_de=GDP"
        )
        return _public_download(
            "eurostat",
            url,
            {"dataset": "demo_gind"},
            env,
            no_network,
            out_dir,
            headers=_browser_ua_headers(),
        )

    def oecd(env: dict[str, str], no_network: bool, out_dir: Path) -> SampleRecord:
        # Single dataflow metadata is small, valid JSON. The unscoped dataflow catalog can truncate
        # mid-response on some paths; Stats SDMX-JSON data queries often return multi‑MiB envelopes.
        attempts: list[tuple[str, dict[str, str]]] = [
            (
                "https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.STES?references=none&format=jsondata",
                {"dataflow": "OECD.SDD.STES", "endpoint": "sdmx_dataflow_single"},
            ),
            (
                "https://sdmx.oecd.org/public/rest/dataflow?format=jsondata",
                {"dataset": "dataflow_catalog", "endpoint": "sdmx_dataflow"},
            ),
        ]
        if no_network:
            return _public_download("oecd", attempts[0][0], attempts[0][1], env, no_network, out_dir)
        headers = _browser_ua_headers()
        last: tuple[str, dict[str, str], int, bytes, str | None] | None = None
        for url, params in attempts:
            code, body, err = _http_get(url, headers=headers, timeout=40.0)
            last = (url, params, code, body, err)
            if code != 200:
                continue
            try:
                json.loads((body or b"").decode("utf-8"))
            except (json.JSONDecodeError, UnicodeError):
                continue
            break
        assert last is not None
        url_l, params_l, code, body, err = last
        return _finalize_public_bytes("oecd", url_l, params_l, code, body, err, out_dir)

    def imf(env: dict[str, str], no_network: bool, out_dir: Path) -> SampleRecord:
        url = "https://www.imf.org/external/datamapper/api/v1/indicators"
        return _public_download(
            "imf_data",
            url,
            {"api": "datamapper_v1", "resource": "indicators"},
            env,
            no_network,
            out_dir,
            headers=_browser_ua_headers(),
            timeout=25.0,
        )

    def bls(env: dict[str, str], no_network: bool, out_dir: Path) -> SampleRecord:
        url = "https://api.bls.gov/publicAPI/v1/timeseries/data/LNS14000000"
        return _public_download("bls", url, {"series": "LNS14000000"}, env, no_network, out_dir)

    def gdelt(env: dict[str, str], no_network: bool, out_dir: Path) -> SampleRecord:
        url = (
            "https://api.gdeltproject.org/api/v2/doc/doc"
            "?query=Business&mode=ArtList&maxrecords=3&format=json"
        )
        params = {"mode": "ArtList"}
        if no_network:
            return _public_download("gdelt", url, params, env, no_network, out_dir)
        headers = _browser_ua_headers()
        code, body, err = _http_get(url, headers=headers, timeout=20.0)
        if code == 429:
            time.sleep(2.5)
            code, body, err = _http_get(url, headers=headers, timeout=20.0)
        return _finalize_public_bytes("gdelt", url, params, code, body, err, out_dir)

    def binance(env: dict[str, str], no_network: bool, out_dir: Path) -> SampleRecord:
        url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
        return _public_download("binance_public", url, {"symbol": "BTCUSDT"}, env, no_network, out_dir)

    def kraken(env: dict[str, str], no_network: bool, out_dir: Path) -> SampleRecord:
        url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
        return _public_download("kraken_public", url, {"pair": "XBTUSD"}, env, no_network, out_dir)

    return {
        "sec_edgar": fetch_sec_edgar,
        "world_bank_open_data": wb,
        "ecb": ecb,
        "eurostat": eurostat,
        "oecd": oecd,
        "imf_data": imf,
        "bls": bls,
        "gdelt": gdelt,
        "binance_public": binance,
        "kraken_public": kraken,
    }


def _keyed_fetch(
    pid: str,
    env: dict[str, str],
    no_network: bool,
    out_dir: Path,
    *,
    build_url: Callable[[str], tuple[str, dict[str, str]]],
) -> SampleRecord:
    cap = capability_by_provider_id()[pid]
    key = _first_key(env, cap.env_vars)
    if not key:
        rec = _stub_record(
            pid,
            endpoint="",
            params={},
            notes="PENDING_HUMAN_SIGNUP_OR_KEY",
            status="PENDING_KEY",
        )
        _write_sample(out_dir, pid, json.dumps({"note": rec.notes}, indent=2).encode(), "json")
        return rec
    if no_network:
        url, params = build_url("REDACTED")
        rec = _stub_record(pid, endpoint=url.split("REDACTED")[0], params=params, notes="no_network mode (key present)")
        _write_sample(out_dir, pid, json.dumps({"note": rec.notes}, indent=2).encode(), "json")
        return rec
    url, params = build_url(key)
    code, body, err = _http_get(url)
    classified, meta = classify_keyed_fetch(code, err, body)
    ext = "txt"
    if code == 200:
        kind, _ = analyze_sample_body(body)
        ext = _extension_for_kind(kind)
    raw = body if body else b""
    name = _write_sample(out_dir, pid, raw, ext)
    return SampleRecord(
        provider_id=pid,
        endpoint=redact_secret_in_url(url, key),
        retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
        query_params={k: ("<redacted>" if v == key else v) for k, v in params.items()},
        status=_transport_label(code),
        classified_status=classified,
        http_status=code,
        sha256=hashlib.sha256(raw).hexdigest(),
        sample_path=name,
        trust_level=cap.default_trust_level.value,
        pit_suitability=cap.pit_suitability.value,
        notes=(err or "")[:500],
        normalized_metadata=normalized_metadata_for_manifest(meta),
    )


def _keyed_registry() -> dict[str, Callable[[dict[str, str], bool, Path], SampleRecord]]:
    def fred(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"series_id": "GDP", "api_key": k, "file_type": "json", "limit": "5"})
            return f"https://api.stlouisfed.org/fred/series/observations?{q}", {"series_id": "GDP"}

        return _keyed_fetch("fred", e, nn, od, build_url=b)

    def av(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"function": "GLOBAL_QUOTE", "symbol": "IBM", "apikey": k})
            return f"https://www.alphavantage.co/query?{q}", {"function": "GLOBAL_QUOTE"}

        return _keyed_fetch("alpha_vantage", e, nn, od, build_url=b)

    def fmp(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"apikey": k})
            return f"https://financialmodelingprep.com/api/v3/profile/AAPL?{q}", {"symbol": "AAPL"}

        return _keyed_fetch("financial_modeling_prep", e, nn, od, build_url=b)

    def fh(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"symbol": "AAPL", "token": k})
            return f"https://finnhub.io/api/v1/quote?{q}", {"symbol": "AAPL"}

        return _keyed_fetch("finnhub", e, nn, od, build_url=b)

    def td(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"symbol": "AAPL", "interval": "1day", "outputsize": "2", "apikey": k})
            return f"https://api.twelvedata.com/time_series?{q}", {"symbol": "AAPL"}

        return _keyed_fetch("twelve_data", e, nn, od, build_url=b)

    def tiingo(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            return (
                "https://api.tiingo.com/tiingo/daily/AAPL/prices?startDate=2024-01-01&token=" + k,
                {"symbol": "AAPL"},
            )

        return _keyed_fetch("tiingo", e, nn, od, build_url=b)

    def eod(e_: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"from": "2024-01-02", "api_token": k, "fmt": "json"})
            return f"https://eodhistoricaldata.com/api/eod/AAPL.US?{q}", {"symbol": "AAPL.US"}

        return _keyed_fetch("eodhd", e_, nn, od, build_url=b)

    def ndl(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"rows": "2", "api_key": k})
            return f"https://data.nasdaq.com/api/v3/datasets/WIKI/AAPL.json?{q}", {"dataset": "WIKI/AAPL"}

        return _keyed_fetch("nasdaq_data_link", e, nn, od, build_url=b)

    def guardian(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"q": "climate", "api-key": k, "page-size": "2"})
            return f"https://content.guardianapis.com/search?{q}", {"q": "climate"}

        return _keyed_fetch("guardian_open_platform", e, nn, od, build_url=b)

    def news(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"country": "us", "pageSize": "2", "apiKey": k})
            return f"https://newsapi.org/v2/top-headlines?{q}", {"country": "us"}

        return _keyed_fetch("newsapi", e, nn, od, build_url=b)

    def media(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"countries": "us", "limit": "2", "access_key": k})
            return f"http://api.mediastack.com/v1/news?{q}", {"countries": "us"}

        return _keyed_fetch("mediastack", e, nn, od, build_url=b)

    def cg(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        cap = capability_by_provider_id()["coingecko"]
        key = _first_key(e, cap.env_vars)
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        params = {"ids": "bitcoin"}
        if nn:
            rec = _stub_record("coingecko", endpoint=url, params=params, notes="no_network mode")
            _write_sample(od, "coingecko", json.dumps({"note": rec.notes}).encode(), "json")
            return rec
        headers = {"x-cg-demo-api-key": key} if key else {}
        code, body, err = _http_get(url, headers=headers)
        classified, meta = (
            classify_keyed_fetch(code, err, body) if key else classify_public_fetch(code, err, body)
        )
        ext = "txt"
        if code == 200:
            kind, _ = analyze_sample_body(body)
            ext = _extension_for_kind(kind)
        raw = body if body else b""
        name = _write_sample(od, "coingecko", raw, ext)
        return SampleRecord(
            provider_id="coingecko",
            endpoint=url,
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            query_params=params,
            status=_transport_label(code),
            classified_status=classified,
            http_status=code,
            sha256=hashlib.sha256(raw).hexdigest(),
            sample_path=name,
            trust_level=cap.default_trust_level.value,
            pit_suitability=cap.pit_suitability.value,
            notes=(err or "")[:500],
            normalized_metadata=normalized_metadata_for_manifest(meta),
        )

    def cmc(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        cap = capability_by_provider_id()["coinmarketcap"]
        key = _first_key(e, cap.env_vars)
        if not key:
            return _keyed_fetch("coinmarketcap", e, nn, od, build_url=lambda k_: ("", {}))
        if nn:
            return _keyed_fetch("coinmarketcap", e, nn, od, build_url=lambda k_: ("https://pro-api.coinmarketcap.com/", {}))
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?id=1"
        headers = {"X-CMC_PRO_API_KEY": key}
        code, body, err = _http_get(url, headers=headers)
        classified, meta = classify_keyed_fetch(code, err, body)
        ext = "txt"
        if code == 200:
            kind, _ = analyze_sample_body(body)
            ext = _extension_for_kind(kind)
        raw = body if body else b""
        name = _write_sample(od, "coinmarketcap", raw, ext)
        return SampleRecord(
            provider_id="coinmarketcap",
            endpoint=url,
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            query_params={"id": "1"},
            status=_transport_label(code),
            classified_status=classified,
            http_status=code,
            sha256=hashlib.sha256(raw).hexdigest(),
            sample_path=name,
            trust_level=cap.default_trust_level.value,
            pit_suitability=cap.pit_suitability.value,
            notes=(err or "")[:500],
            normalized_metadata=normalized_metadata_for_manifest(meta),
        )

    def odds(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            q = urlencode({"apiKey": k})
            return f"https://api.the-odds-api.com/v4/sports?{q}", {}

        return _keyed_fetch("the_odds_api", e, nn, od, build_url=b)

    def fb(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        cap = capability_by_provider_id()["football_data_org"]
        key = _first_key(e, cap.env_vars)
        if not key:
            return _keyed_fetch("football_data_org", e, nn, od, build_url=lambda _: ("", {}))
        if nn:
            rec = _stub_record(
                "football_data_org",
                endpoint="https://api.football-data.org/v4/competitions",
                params={},
                notes="no_network mode",
            )
            _write_sample(od, "football_data_org", json.dumps({"note": rec.notes}).encode(), "json")
            return rec
        url = "https://api.football-data.org/v4/competitions"
        code, body, err = _http_get(url, headers={"X-Auth-Token": key})
        classified, meta = classify_keyed_fetch(code, err, body)
        ext = "txt"
        if code == 200:
            kind, _ = analyze_sample_body(body)
            ext = _extension_for_kind(kind)
        raw = body if body else b""
        name = _write_sample(od, "football_data_org", raw, ext)
        return SampleRecord(
            provider_id="football_data_org",
            endpoint=url,
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            query_params={},
            status=_transport_label(code),
            classified_status=classified,
            http_status=code,
            sha256=hashlib.sha256(raw).hexdigest(),
            sample_path=name,
            trust_level=cap.default_trust_level.value,
            pit_suitability=cap.pit_suitability.value,
            notes=(err or "")[:500],
            normalized_metadata=normalized_metadata_for_manifest(meta),
        )

    def apisports(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        cap = capability_by_provider_id()["api_sports"]
        key = _first_key(e, cap.env_vars)
        if not key:
            return _keyed_fetch("api_sports", e, nn, od, build_url=lambda _: ("", {}))
        if nn:
            rec = _stub_record("api_sports", endpoint="https://v3.football.api-sports.io/status", params={}, notes="no_network")
            _write_sample(od, "api_sports", json.dumps({"note": rec.notes}).encode(), "json")
            return rec
        url = "https://v3.football.api-sports.io/status"
        code, body, err = _http_get(url, headers={"x-apisports-key": key})
        classified, meta = classify_keyed_fetch(code, err, body)
        ext = "txt"
        if code == 200:
            kind, _ = analyze_sample_body(body)
            ext = _extension_for_kind(kind)
        raw = body if body else b""
        name = _write_sample(od, "api_sports", raw, ext)
        return SampleRecord(
            provider_id="api_sports",
            endpoint=url,
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            query_params={},
            status=_transport_label(code),
            classified_status=classified,
            http_status=code,
            sha256=hashlib.sha256(raw).hexdigest(),
            sample_path=name,
            trust_level=cap.default_trust_level.value,
            pit_suitability=cap.pit_suitability.value,
            notes=(err or "")[:500],
            normalized_metadata=normalized_metadata_for_manifest(meta),
        )

    def sm(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        def b(k: str) -> tuple[str, dict[str, str]]:
            return "https://api.sportmonks.com/v3/my/football/leagues?api_token=" + k, {}

        return _keyed_fetch("sportmonks", e, nn, od, build_url=b)

    def bls2(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        cap = capability_by_provider_id()["bls_registered_api"]
        key = _first_key(e, cap.env_vars)
        if not key:
            return _keyed_fetch("bls_registered_api", e, nn, od, build_url=lambda _: ("", {}))
        if nn:
            rec = _stub_record("bls_registered_api", endpoint="https://api.bls.gov/publicAPI/v2/timeseries/data/", params={}, notes="no_network")
            _write_sample(od, "bls_registered_api", json.dumps({"note": rec.notes}).encode(), "json")
            return rec
        payload = json.dumps(
            {"seriesid": ["LNS14000000"], "startyear": "2020", "endyear": "2020", "registrationkey": key}
        ).encode()
        req = Request(
            "https://api.bls.gov/publicAPI/v2/timeseries/data/",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=TIMEOUT_S) as resp:  # noqa: S310
                body = resp.read()
                code = int(getattr(resp, "status", 200))
                err = None
        except HTTPError as exc:
            code = int(exc.code)
            try:
                body = exc.read()
            except OSError:
                body = b""
            err = str(exc)
        except (URLError, OSError) as exc:
            code = -1
            body = b""
            err = str(exc)
        classified, meta = classify_keyed_fetch(code, err, body)
        ext = "txt"
        if code == 200:
            kind, _ = analyze_sample_body(body)
            ext = _extension_for_kind(kind)
        raw = body if body else b""
        name = _write_sample(od, "bls_registered_api", raw, ext)
        return SampleRecord(
            provider_id="bls_registered_api",
            endpoint="https://api.bls.gov/publicAPI/v2/timeseries/data/",
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            query_params={"seriesid": "LNS14000000"},
            status=_transport_label(code),
            classified_status=classified,
            http_status=code,
            sha256=hashlib.sha256(raw).hexdigest(),
            sample_path=name,
            trust_level=cap.default_trust_level.value,
            pit_suitability=cap.pit_suitability.value,
            notes=(err or "")[:500],
            normalized_metadata=normalized_metadata_for_manifest(meta),
        )

    def _polygon_aggs(k: str) -> tuple[str, dict[str, str]]:
        q = urlencode(
            {
                "adjusted": "true",
                "sort": "asc",
                "limit": "2",
                "apiKey": k,
            }
        )
        return f"https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-02/2024-01-10?{q}", {"ticker": "AAPL"}

    def poly(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        return _keyed_fetch("polygon_io", e, nn, od, build_url=_polygon_aggs)

    def massive(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        return _keyed_fetch("massive", e, nn, od, build_url=_polygon_aggs)

    def alpaca_sample(e: dict[str, str], nn: bool, od: Path) -> SampleRecord:
        cap = capability_by_provider_id()["alpaca"]
        kid = _first_key(e, ("ALPACA_API_KEY", "APCA_API_KEY_ID"))
        sec = _first_key(e, ("ALPACA_API_SECRET", "APCA_API_SECRET_KEY"))
        base = (e.get("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets").rstrip("/")
        if base.endswith("/v2"):
            base = base[:-3].rstrip("/")
        mode = (e.get("ALPACA_TRADING_MODE") or "paper").strip().lower()
        personal = _truthy(e.get("PERSONAL_LIVE_APPROVED")) or _truthy(e.get("STRATEGY_VALIDATOR_PERSONAL_LIVE_APPROVED"))
        if not kid or not sec:
            rec = _stub_record(
                "alpaca",
                endpoint=base + "/v2/account",
                params={},
                notes="PENDING_MANUAL_BROKER_SETUP",
                status="PENDING_MANUAL_BROKER_SETUP",
            )
            _write_sample(od, "alpaca", json.dumps({"note": rec.notes}).encode(), "json")
            return rec
        if mode == "live" and not personal:
            rec = _stub_record(
                "alpaca",
                endpoint=base + "/v2/account",
                params={},
                notes="live mode blocked without PERSONAL_LIVE_APPROVED",
                status="POLICY_SKIP",
            )
            _write_sample(od, "alpaca", json.dumps({"note": rec.notes}).encode(), "json")
            return rec
        if "paper-api" not in base and not personal:
            rec = _stub_record(
                "alpaca",
                endpoint=base + "/v2/account",
                params={},
                notes="non-paper base URL without personal live approval",
                status="POLICY_SKIP",
            )
            _write_sample(od, "alpaca", json.dumps({"note": rec.notes}).encode(), "json")
            return rec
        if nn:
            rec = _stub_record("alpaca", endpoint=base + "/v2/account", params={}, notes="no_network mode")
            _write_sample(od, "alpaca", json.dumps({"note": rec.notes}).encode(), "json")
            return rec
        url = base + "/v2/account"
        headers = {"APCA-API-KEY-ID": kid, "APCA-API-SECRET-KEY": sec}
        code, body, err = _http_get(url, headers=headers)
        classified, meta = classify_keyed_fetch(code, err, body if body else b"")
        out_body = body if body else b"{}"
        try:
            parsed = json.loads(out_body.decode("utf-8", errors="strict"))
            redacted = json.dumps(parsed, indent=2).encode("utf-8")
        except (json.JSONDecodeError, UnicodeError):
            redacted = out_body
        name = _write_sample(od, "alpaca", redacted, "json")
        return SampleRecord(
            provider_id="alpaca",
            endpoint=url,
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            query_params={},
            status=_transport_label(code),
            classified_status=classified,
            http_status=code,
            sha256=hashlib.sha256(redacted).hexdigest(),
            sample_path=name,
            trust_level=cap.default_trust_level.value,
            pit_suitability=cap.pit_suitability.value,
            notes=(err or "")[:500],
            normalized_metadata=normalized_metadata_for_manifest(meta),
        )

    return {
        "fred": fred,
        "alpha_vantage": av,
        "financial_modeling_prep": fmp,
        "finnhub": fh,
        "twelve_data": td,
        "tiingo": tiingo,
        "eodhd": eod,
        "nasdaq_data_link": ndl,
        "guardian_open_platform": guardian,
        "newsapi": news,
        "mediastack": media,
        "coingecko": cg,
        "coinmarketcap": cmc,
        "the_odds_api": odds,
        "football_data_org": fb,
        "api_sports": apisports,
        "sportmonks": sm,
        "bls_registered_api": bls2,
        "polygon_io": poly,
        "massive": massive,
        "alpaca": alpaca_sample,
    }


def _resolve_ids(
    raw: str | None,
    *,
    public_only: bool,
    keyed_only: bool,
) -> list[str]:
    caps = capability_by_provider_id()
    if raw:
        parts = [CLI_ALIASES.get(p.strip(), p.strip()) for p in raw.split(",") if p.strip()]
        unknown = [p for p in parts if p not in caps]
        if unknown:
            sys.stderr.write("Unknown provider id(s): " + ", ".join(unknown) + "\n")
        return [p for p in parts if p in caps]
    if public_only:
        return list(PUBLIC_DEFAULT_ORDER)
    if keyed_only:
        return sorted(
            pid
            for pid, c in caps.items()
            if c.access_type
            in (
                ProviderAccessType.FREE_KEY_REQUIRED,
                ProviderAccessType.FREEMIUM_KEY_REQUIRED,
                ProviderAccessType.PAID_OR_TRIAL,
                ProviderAccessType.BROKER_ACCOUNT_REQUIRED,
            )
        )
    return list(PUBLIC_DEFAULT_ORDER)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Retrieve small provider API samples.")
    parser.add_argument("--providers", default="", help="Comma-separated provider ids or aliases.")
    parser.add_argument("--output-dir", default="artifacts/provider_samples", type=Path)
    parser.add_argument("--manifest-json", action="store_true", help="Write manifest.json under output dir.")
    parser.add_argument("--no-network", action="store_true", help="Write stubs only (for tests/offline).")
    parser.add_argument("--max-samples", type=int, default=0, help="Limit providers processed (0 = no limit).")
    parser.add_argument("--public-only", action="store_true", help="Only public/no-signup providers.")
    parser.add_argument(
        "--configured-keyed-only",
        action="store_true",
        help="Only key-gated / broker providers (uses env for keys).",
    )
    parser.add_argument("--env-file", default="", help="Load KEY=VALUE pairs before checking keys.")
    ns = parser.parse_args(argv)
    try:
        out_dir = safe_output_dir(ns.output_dir, label="RETRIEVE_PROVIDER_OUTPUT_DIR")
        env_path = safe_input_file(ns.env_file, label="RETRIEVE_PROVIDER_ENV_FILE", required=False) if ns.env_file else None
    except PathIntegrityError as exc:
        sys.stdout.write(json.dumps(path_error_payload(exc), sort_keys=True) + "\n")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    env = _merged_env(env_file=env_path)

    public_fetchers = _registry_fetchers()
    keyed_fetchers = _keyed_registry()

    if ns.public_only and ns.configured_keyed_only:
        sys.stderr.write("Choose at most one of --public-only and --configured-keyed-only.\n")
        return 2

    ids = _resolve_ids(ns.providers or None, public_only=ns.public_only, keyed_only=ns.configured_keyed_only)
    if ns.max_samples > 0:
        ids = ids[: ns.max_samples]

    records: list[SampleRecord] = []
    for pid in ids:
        if pid in public_fetchers:
            records.append(public_fetchers[pid](env, ns.no_network, out_dir))
        elif pid in keyed_fetchers:
            records.append(keyed_fetchers[pid](env, ns.no_network, out_dir))
        else:
            sys.stderr.write(f"No fetcher registered for {pid!r}\n")

    explicit_provider_request = bool((ns.providers or "").strip())
    blockers: list[str] = []
    warnings: list[str] = []
    canonical_status_counts: dict[str, int] = {}
    for row in records:
        st = str(row.status or "").upper()
        canonical = "UNKNOWN"
        if st == "OK":
            canonical = "OK"
        elif st in {"PENDING_KEY", "PENDING_MANUAL_BROKER_SETUP"}:
            canonical = "PENDING_KEY"
        elif row.classified_status.upper() in {"TEMPORARILY_UNAVAILABLE", "NETWORK_BLOCKED"}:
            canonical = "UNAVAILABLE"
        elif row.classified_status.upper() in {"AUTH_FAILED", "PLAN_LIMITED", "RATE_LIMITED", "ENDPOINT_CHANGED", "PARSE_ERROR", "ERROR", "HTTP_ERROR"}:
            canonical = "DEGRADED"
        elif st in {"SKIPPED_NO_NETWORK", "POLICY_SKIP"}:
            canonical = "UNKNOWN"
        canonical_status_counts[canonical] = int(canonical_status_counts.get(canonical, 0)) + 1
        if explicit_provider_request and st in {"PENDING_KEY", "PENDING_MANUAL_BROKER_SETUP"}:
            blockers.append(f"PROVIDER_KEY_PENDING:{row.provider_id}")
        elif canonical in {"UNAVAILABLE", "DEGRADED"}:
            warnings.append(f"PROVIDER_{canonical}:{row.provider_id}")

    if ns.manifest_json:
        generated_at = datetime.now(timezone.utc).isoformat()
        command_args_redacted = [
            "<redacted>" if any(tok in str(arg).lower() for tok in ("key", "secret", "token", "password")) else str(arg)
            for arg in (argv or [])
        ]
        manifest = {
            "entries": [r.as_manifest_dict() for r in sorted(records, key=lambda r: r.provider_id)],
            "generated_at_utc": generated_at,
            "paper_only": True,
            "live_trading_blocked": True,
            "replayable_offline": True,
            "command": "python scripts/retrieve_provider_samples.py",
            "command_args_redacted": command_args_redacted,
            "schema_version": "provider_samples_manifest/v1",
            "status_summary": {
                "providers_processed": len(records),
                "canonical_status_counts": dict(sorted(canonical_status_counts.items())),
            },
            "warnings": sorted(set(warnings)),
            "blockers": sorted(set(blockers)),
        }
        (out_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    result_code = 3 if blockers else 0
    sys.stdout.write(
        json.dumps(
            {
                "providers_processed": len(records),
                "output_dir": str(out_dir),
                "status": "BLOCKED" if blockers else "OK",
                "canonical_status_counts": dict(sorted(canonical_status_counts.items())),
                "warnings": sorted(set(warnings)),
                "blockers": sorted(set(blockers)),
            },
            indent=2,
        )
        + "\n"
    )
    return result_code


if __name__ == "__main__":
    raise SystemExit(main())
