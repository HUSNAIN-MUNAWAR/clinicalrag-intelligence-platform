"""Download a license-aware open medical corpus for the RAG demo.

The default run is intentionally bounded. It downloads enough real documents
to demonstrate a professional pipeline while keeping the workspace small.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "scripts" / "open_medical_sources.json"
USER_AGENT = "ClinicalRAG-Portfolio-CorpusDownloader/1.0 (+educational portfolio project)"
TEXT_EXTENSIONS = {".xml", ".nxml", ".txt"}


@dataclass
class DownloadedFile:
    source_id: str
    title: str
    url: str
    path: Path
    license: str
    attribution: str
    sha256: str
    bytes: int
    notes: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str, fallback: str = "document") -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip()).strip("_")
    return value[:120] or fallback


def request_url(url: str, timeout: int) -> urllib.response.addinfourl:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=timeout)


def download_bytes(url: str, timeout: int) -> bytes:
    with request_url(url, timeout) as response:
        return response.read()


def write_file(path: Path, content: bytes, force: bool) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return False
    path.write_bytes(content)
    return True


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ledger_row(item: DownloadedFile) -> dict[str, Any]:
    return {
        "downloaded_at": utc_now(),
        "source_id": item.source_id,
        "title": item.title,
        "url": item.url,
        "path": str(item.path.relative_to(ROOT)),
        "license": item.license,
        "attribution": item.attribution,
        "sha256": item.sha256,
        "bytes": item.bytes,
        "notes": item.notes,
    }


def record_file(
    source: dict[str, Any],
    title: str,
    url: str,
    path: Path,
    notes: str = "",
) -> DownloadedFile:
    return DownloadedFile(
        source_id=source["id"],
        title=title,
        url=url,
        path=path,
        license=source.get("license", ""),
        attribution=source.get("attribution", ""),
        sha256=sha256_file(path),
        bytes=path.stat().st_size,
        notes=notes,
    )


def download_direct_file(
    source: dict[str, Any],
    target_dir: Path,
    item: dict[str, str],
    timeout: int,
    force: bool,
) -> DownloadedFile:
    content = download_bytes(item["url"], timeout)
    path = target_dir / source["id"] / item["filename"]
    write_file(path, content, force)
    return record_file(source, item["title"], item["url"], path)


def resolve_medlineplus_latest(source: dict[str, Any], timeout: int) -> tuple[str, str]:
    html = download_bytes(source["source_url"], timeout).decode("utf-8", errors="ignore")
    candidates = re.findall(r'href="([^"]*mplus_topics_[0-9-]+\.zip)"', html)
    if not candidates:
        candidates = re.findall(r'href="([^"]*mplus_topics_[0-9-]+\.xml)"', html)
    if not candidates:
        raise RuntimeError("Could not find a MedlinePlus health-topic XML link.")
    url = urllib.parse.urljoin(source["source_url"], candidates[0])
    return url, Path(urllib.parse.urlparse(url).path).name


def download_medlineplus_latest(
    source: dict[str, Any],
    target_dir: Path,
    timeout: int,
    force: bool,
) -> list[DownloadedFile]:
    url, filename = resolve_medlineplus_latest(source, timeout)
    content = download_bytes(url, timeout)
    source_dir = target_dir / source["id"]
    source_dir.mkdir(parents=True, exist_ok=True)
    xml_path = source_dir / "medlineplus_health_topics.xml"

    if filename.lower().endswith(".zip"):
        archive_path = source_dir / filename
        write_file(archive_path, content, force)
        with zipfile.ZipFile(archive_path) as archive:
            xml_names = [name for name in archive.namelist() if name.lower().endswith(".xml")]
            if not xml_names:
                raise RuntimeError("MedlinePlus archive did not contain XML.")
            extracted_name = xml_names[0]
            if force or not xml_path.exists():
                with archive.open(extracted_name) as src, xml_path.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
    else:
        write_file(xml_path, content, force)

    return [
        record_file(source, source["name"], url, xml_path, notes=f"Resolved latest file from {source['source_url']}")
    ]


def build_openfda_text(record: dict[str, Any]) -> str:
    section_names = [
        "indications_and_usage",
        "purpose",
        "boxed_warning",
        "warnings",
        "contraindications",
        "dosage_and_administration",
        "adverse_reactions",
        "drug_interactions",
        "clinical_pharmacology",
        "patient_medication_information",
    ]
    lines: list[str] = []
    for name in section_names:
        values = record.get(name)
        if not values:
            continue
        if isinstance(values, list):
            text = "\n".join(str(v) for v in values)
        else:
            text = str(values)
        lines.append(f"{name.replace('_', ' ').title()}:\n{text}")
    return "\n\n".join(lines) or json.dumps(record, ensure_ascii=True)


def download_openfda_drug_labels(
    source: dict[str, Any],
    target_dir: Path,
    limit: int,
    timeout: int,
    force: bool,
) -> list[DownloadedFile]:
    params = {"limit": str(limit)}
    if source.get("query"):
        params["search"] = source["query"]
    url = f"{source['api_url']}?{urllib.parse.urlencode(params)}"
    data = json.loads(download_bytes(url, timeout).decode("utf-8"))
    records = data.get("results", [])
    output: list[DownloadedFile] = []
    for index, record in enumerate(records, start=1):
        openfda = record.get("openfda") or {}
        brand = (openfda.get("brand_name") or openfda.get("generic_name") or [f"openFDA label {index}"])[0]
        set_id = record.get("set_id") or record.get("id") or str(index)
        title = f"{brand} drug label"
        payload = {
            "title": title,
            "source": source["name"],
            "set_id": set_id,
            "effective_time": record.get("effective_time"),
            "license": source.get("license"),
            "attribution": source.get("attribution"),
            "text": build_openfda_text(record),
            "raw": record,
        }
        filename = f"{index:03d}_{slugify(str(brand))}_{slugify(str(set_id))}.json"
        path = target_dir / source["id"] / filename
        write_file(path, json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8"), force)
        output.append(record_file(source, title, url, path, notes="openFDA API result"))
    return output


def csv_rows_from_url(url: str, timeout: int):
    with request_url(url, timeout) as response:
        wrapper = io.TextIOWrapper(response, encoding="utf-8", errors="ignore", newline="")
        reader = csv.reader(wrapper)
        for row in reader:
            yield row


def safe_extract_text_members(archive_path: Path, destination: Path, force: bool) -> list[Path]:
    extracted: list[Path] = []
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            suffix = Path(member.name).suffix.lower()
            if suffix not in TEXT_EXTENSIONS:
                continue
            member_file = archive.extractfile(member)
            if member_file is None:
                continue
            out_suffix = ".xml" if suffix == ".nxml" else suffix
            out_name = slugify(Path(member.name).stem) + out_suffix
            out_path = destination / out_name
            if force or not out_path.exists():
                with out_path.open("wb") as handle:
                    shutil.copyfileobj(member_file, handle)
            extracted.append(out_path)
    return extracted


def download_pmc_oa_articles(
    source: dict[str, Any],
    target_dir: Path,
    limit: int,
    timeout: int,
    force: bool,
) -> list[DownloadedFile]:
    allowed = {x.upper() for x in source.get("allowed_licenses", [])}
    output: list[DownloadedFile] = []
    source_dir = target_dir / source["id"]
    packages_dir = source_dir / "packages"
    articles_dir = source_dir / "articles"

    for row in csv_rows_from_url(source["file_list_url"], timeout):
        if len(output) >= limit:
            break
        if len(row) < 6 or row[0].lower() in {"file", "key"}:
            continue
        if len(row) == 1:
            continue

        if len(row) >= 8 and row[0].lower().endswith((".xml", ".txt")):
            object_key = row[0]
            citation = row[2]
            pmcid = row[3]
            license_type = row[6].strip().upper()
            retracted = row[7].strip().lower()
            if license_type not in allowed or retracted == "yes":
                continue
            object_url = urllib.parse.urljoin(source["object_base_url"], object_key)
            suffix = Path(object_key).suffix.lower()
            path = articles_dir / f"{pmcid}{suffix}"
            try:
                write_file(path, download_bytes(object_url, timeout), force)
            except (urllib.error.URLError, OSError) as exc:
                print(f"WARNING: skipped {pmcid}: {exc}")
                continue
            output.append(
                DownloadedFile(
                    source_id=source["id"],
                    title=f"{pmcid} - {citation}",
                    url=object_url,
                    path=path,
                    license=f"{license_type}; {source.get('license', '')}",
                    attribution=source.get("attribution", ""),
                    sha256=sha256_file(path),
                    bytes=path.stat().st_size,
                    notes=f"Downloaded from PMC AWS object key {object_key}",
                )
            )
            time.sleep(0.2)
            continue

        package_path, citation, pmcid = row[0], row[1], row[2]
        license_type = row[5].strip().upper()
        retracted = row[6].strip().lower() if len(row) > 6 else "unknown"
        if license_type not in allowed or retracted == "yes":
            continue

        package_url = urllib.parse.urljoin(source["package_base_url"], package_path)
        package_file = packages_dir / f"{pmcid}.tar.gz"
        try:
            write_file(package_file, download_bytes(package_url, timeout), force)
            extracted = safe_extract_text_members(package_file, articles_dir / pmcid, force)
        except (urllib.error.URLError, tarfile.TarError, OSError) as exc:
            print(f"WARNING: skipped {pmcid}: {exc}")
            continue

        for path in extracted:
            output.append(
                DownloadedFile(
                    source_id=source["id"],
                    title=f"{pmcid} - {citation}",
                    url=package_url,
                    path=path,
                    license=f"{license_type}; {source.get('license', '')}",
                    attribution=source.get("attribution", ""),
                    sha256=sha256_file(path),
                    bytes=path.stat().st_size,
                    notes=f"Extracted from PMC package {package_path}",
                )
            )
            if len(output) >= limit:
                break
        time.sleep(0.2)
    return output


def download_source(
    source: dict[str, Any],
    target_dir: Path,
    limit_override: int | None,
    timeout: int,
    force: bool,
) -> list[DownloadedFile]:
    limit = limit_override if limit_override is not None else int(source.get("limit_default", 1))
    downloader = source["downloader"]
    if downloader == "medlineplus_latest":
        return download_medlineplus_latest(source, target_dir, timeout, force)
    if downloader == "openfda_drug_labels":
        return download_openfda_drug_labels(source, target_dir, limit, timeout, force)
    if downloader == "pmc_oa_articles":
        return download_pmc_oa_articles(source, target_dir, limit, timeout, force)
    if downloader in {"direct_pages", "direct_files"}:
        output: list[DownloadedFile] = []
        for item in source.get("urls", [])[:limit]:
            output.append(download_direct_file(source, target_dir, item, timeout, force))
            time.sleep(0.2)
        return output
    if downloader == "none":
        return []
    raise ValueError(f"Unknown downloader: {downloader}")


def selected_sources(manifest: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    requested = {x.strip() for x in args.sources.split(",") if x.strip()} if args.sources else None
    sources = []
    for source in manifest["sources"]:
        if requested and source["id"] not in requested:
            continue
        if not requested and not source.get("enabled", False):
            continue
        if args.profile == "commercial" and not source.get("commercial_safe", False):
            continue
        sources.append(source)
    return sources


def write_outputs(target_dir: Path, manifest: dict[str, Any], rows: list[DownloadedFile]) -> None:
    metadata_dir = target_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = metadata_dir / "download_manifest.jsonl"
    with ledger_path.open("w", encoding="utf-8") as handle:
        for item in rows:
            handle.write(json.dumps(ledger_row(item), ensure_ascii=True) + "\n")

    summary = {
        "generated_at": utc_now(),
        "source_manifest_version": manifest.get("version"),
        "document_count": len(rows),
        "total_bytes": sum(item.bytes for item in rows),
        "sources": sorted({item.source_id for item in rows}),
        "ledger": str(ledger_path.relative_to(ROOT)),
    }
    (metadata_dir / "source_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    attribution_lines = [
        "# Open Medical Corpus Attribution",
        "",
        f"Generated at: {summary['generated_at']}",
        "",
        "This directory is generated by `python scripts/download_open_medical_corpus.py`.",
        "Review each source licence before public redistribution or commercial deployment.",
        "",
    ]
    for source in manifest["sources"]:
        used = [item for item in rows if item.source_id == source["id"]]
        if not used:
            continue
        attribution_lines.extend(
            [
                f"## {source['name']}",
                "",
                f"- Source: {source.get('source_url', '')}",
                f"- Terms: {source.get('terms_url', '')}",
                f"- Licence notes: {source.get('license', '')}",
                f"- Attribution: {source.get('attribution', '')}",
                f"- Downloaded files: {len(used)}",
                "",
            ]
        )
    (target_dir / "ATTRIBUTION.md").write_text("\n".join(attribution_lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a bounded, license-aware open medical corpus.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--target-dir", type=Path)
    parser.add_argument("--profile", choices=["portfolio", "commercial", "all"], default="portfolio")
    parser.add_argument("--sources", help="Comma-separated source ids. Overrides enabled/profile filtering.")
    parser.add_argument("--limit", type=int, help="Override per-source document limit where applicable.")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--dry-run", action="store_true", help="Print selected sources without downloading.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    target_dir = (args.target_dir or ROOT / manifest["default_target_dir"]).resolve()
    sources = selected_sources(manifest, args)

    print(f"Profile: {args.profile}")
    print(f"Target: {target_dir}")
    print("Selected sources:")
    for source in sources:
        print(f" - {source['id']}: {source['name']}")
    if args.dry_run:
        return

    downloaded: list[DownloadedFile] = []
    for source in sources:
        print(f"\nDownloading {source['id']}...")
        try:
            files = download_source(source, target_dir / "raw", args.limit, args.timeout, args.force)
        except Exception as exc:
            print(f"ERROR: {source['id']} failed: {exc}")
            continue
        downloaded.extend(files)
        print(f"Downloaded {len(files)} files from {source['id']}.")

    write_outputs(target_dir, manifest, downloaded)
    print(f"\nDone. {len(downloaded)} files registered in {target_dir / 'metadata' / 'download_manifest.jsonl'}")


if __name__ == "__main__":
    main()
