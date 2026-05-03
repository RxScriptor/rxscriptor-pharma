"""DART OpenAPI client used by the P3 companies-portfolio watcher.

Endpoints:
- GET /api/corpCode.xml   one-shot zip listing all KRX corp_codes
- GET /api/list.json      filings for a single corp_code in a date range
- GET /api/document.xml   raw filing body, zipped XML (best-effort context)
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from typing import Iterator
from xml.etree import ElementTree as ET

import requests

DART_BASE = "https://opendart.fss.or.kr/api"


@dataclass(frozen=True)
class Filing:
    rcept_no: str
    corp_code: str
    corp_name: str
    stock_code: str
    report_nm: str
    rcept_dt: str
    flr_nm: str
    rm: str

    @property
    def url(self) -> str:
        return f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={self.rcept_no}"


class DartClient:
    def __init__(self, api_key: str, *, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.sess = requests.Session()

    def fetch_corp_codes(self) -> dict[str, str]:
        """Return mapping stock_code -> corp_code for all listed companies."""
        r = self.sess.get(
            f"{DART_BASE}/corpCode.xml",
            params={"crtfc_key": self.api_key},
            timeout=self.timeout,
        )
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            xml_bytes = zf.read("CORPCODE.xml")
        root = ET.fromstring(xml_bytes)
        out: dict[str, str] = {}
        for entry in root.findall("list"):
            stock = (entry.findtext("stock_code") or "").strip()
            corp_code = (entry.findtext("corp_code") or "").strip()
            if stock and corp_code:
                out[stock] = corp_code
        return out

    def list_filings(
        self,
        corp_code: str,
        bgn_de: str,
        end_de: str,
        *,
        page_count: int = 100,
    ) -> Iterator[Filing]:
        """Yield filings for one company within [bgn_de, end_de] (YYYYMMDD)."""
        page_no = 1
        while True:
            r = self.sess.get(
                f"{DART_BASE}/list.json",
                params={
                    "crtfc_key": self.api_key,
                    "corp_code": corp_code,
                    "bgn_de": bgn_de,
                    "end_de": end_de,
                    "page_no": page_no,
                    "page_count": page_count,
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
            status = data.get("status")
            if status == "013":
                return
            if status != "000":
                raise RuntimeError(
                    f"DART list.json status={status}: {data.get('message')}"
                )
            for row in data.get("list", []):
                yield Filing(
                    rcept_no=row["rcept_no"],
                    corp_code=row["corp_code"],
                    corp_name=row["corp_name"],
                    stock_code=row.get("stock_code", ""),
                    report_nm=row["report_nm"],
                    rcept_dt=row["rcept_dt"],
                    flr_nm=row.get("flr_nm", ""),
                    rm=row.get("rm", ""),
                )
            if page_no >= int(data.get("total_page", 1)):
                return
            page_no += 1

    def fetch_document_text(self, rcept_no: str, *, max_chars: int = 8000) -> str:
        """Return a cleaned text snippet of the filing body, or '' on failure."""
        try:
            r = self.sess.get(
                f"{DART_BASE}/document.xml",
                params={"crtfc_key": self.api_key, "rcept_no": rcept_no},
                timeout=self.timeout,
            )
            r.raise_for_status()
        except requests.RequestException:
            return ""
        try:
            with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                names = zf.namelist()
                if not names:
                    return ""
                xml_bytes = zf.read(names[0])
        except zipfile.BadZipFile:
            return ""
        xml_text = ""
        for enc in ("utf-8", "euc-kr", "cp949"):
            try:
                xml_text = xml_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if not xml_text:
            return ""
        text = re.sub(r"<[^>]+>", " ", xml_text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
