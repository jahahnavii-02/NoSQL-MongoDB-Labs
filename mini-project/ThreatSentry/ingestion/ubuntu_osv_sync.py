import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from ingestion.osv_ingest import ingest_osv_vulnerability


OSV_BASE = "https://api.osv.dev"
WSL_DISTRIBUTION = os.getenv("WSL_DISTRIBUTION", "Ubuntu")
SCANNER_MODE = os.getenv("SCANNER_MODE", "wsl").lower()


def _host_cmd(*args):
    """Command list that runs on the monitored Ubuntu system (WSL or local)."""
    if SCANNER_MODE == "local":
        return list(args)
    return ["wsl.exe", "-d", WSL_DISTRIBUTION, "--", *args]
REQUEST_TIMEOUT = 45
MAX_BATCH = 1000


def _installed_source_packages():
    """Read installed Ubuntu binary packages using dpkg-query."""
    result = subprocess.run(
        _host_cmd("dpkg-query", "-W"),
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )

    packages = []
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue

        binary, installed_version = parts
        if not binary or not installed_version:
            continue

        packages.append({
            "binary_name": binary.split(":")[0],
            "source_name": binary.split(":")[0],
            "source_version": installed_version.strip(),
        })

    if not packages:
        raise RuntimeError(
            "Ubuntu returned no usable package metadata from dpkg-query."
        )

    return packages

def _map_binary_to_source(packages, ecosystem):
    binary_names = list(dict.fromkeys(
        item["binary_name"] for item in packages
    ))

    mappings = {}
    mapping_method = "OSV experimental mapping API"

    for start in range(0, len(binary_names), MAX_BATCH):
        batch = binary_names[start:start + MAX_BATCH]

        response = requests.post(
            f"{OSV_BASE}/v1experimental/ubuntu/binary-to-source",
            json={
                "ecosystem": ecosystem,
                "binary_names": batch,
            },
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        results = response.json().get("results", [])

        if len(results) != len(batch):
            raise RuntimeError(
                "OSV package mapping returned an unexpected result count."
            )

        for binary, result in zip(batch, results):
            mappings[binary] = result.get("source_names", [])

    return mappings, mapping_method


def _query_batch(queries):
    response = requests.post(
        f"{OSV_BASE}/v1/querybatch",
        json={"queries": queries},
        headers={"Accept": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    if len(results) != len(queries):
        raise RuntimeError(
            "OSV batch response did not match the submitted queries."
        )

    found_ids = set()

    for query, result in zip(queries, results):
        for vulnerability in result.get("vulns", []):
            vulnerability_id = vulnerability.get("id")
            if vulnerability_id:
                found_ids.add(vulnerability_id)

        page_token = result.get("next_page_token")

        while page_token:
            next_query = dict(query)
            next_query["page_token"] = page_token

            page_response = requests.post(
                f"{OSV_BASE}/v1/querybatch",
                json={"queries": [next_query]},
                headers={"Accept": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
            page_response.raise_for_status()

            page_results = page_response.json().get("results", [])
            if not page_results:
                break

            page = page_results[0]

            for vulnerability in page.get("vulns", []):
                vulnerability_id = vulnerability.get("id")
                if vulnerability_id:
                    found_ids.add(vulnerability_id)

            page_token = page.get("next_page_token")

    return found_ids


def _import_one(vulnerability_id):
    try:
        return {
            "id": vulnerability_id,
            "success": True,
            "result": ingest_osv_vulnerability(vulnerability_id),
        }
    except Exception as exc:
        return {
            "id": vulnerability_id,
            "success": False,
            "error": str(exc)[:250],
        }


def sync_ubuntu_osv():
    packages = _installed_source_packages()

    os_release = subprocess.run(
        _host_cmd("cat", "/etc/os-release"),
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    ).stdout

    version = "Unknown"
    for line in os_release.splitlines():
        if line.startswith("VERSION_ID="):
            version = line.split("=", 1)[1].strip().strip('"')
            break

    if version == "Unknown":
        raise RuntimeError("Could not determine Ubuntu release.")

    ecosystem = f"Ubuntu:{version}:LTS"

    try:
        mappings, mapping_method = _map_binary_to_source(
            packages, ecosystem
        )
    except requests.RequestException:
        # Fallback to source package metadata supplied by dpkg.
        mappings = {}
        mapping_method = "dpkg source metadata fallback"

    queries_by_key = {}

    for item in packages:
        binary = item["binary_name"]
        source_names = mappings.get(binary) or [item["source_name"]]

        for source_name in source_names:
            source_name = source_name.strip()
            source_version = item["source_version"]

            if not source_name or not source_version:
                continue

            key = (source_name, source_version)

            queries_by_key[key] = {
                "package": {
                    "ecosystem": ecosystem,
                    "name": source_name,
                },
                "version": source_version,
            }

    queries = list(queries_by_key.values())

    if not queries:
        raise RuntimeError(
            "No source package/version queries could be constructed."
        )

    vulnerability_ids = set()

    for start in range(0, len(queries), MAX_BATCH):
        batch = queries[start:start + MAX_BATCH]
        vulnerability_ids.update(_query_batch(batch))

    imported = 0
    failed = 0
    import_errors = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_import_one, vulnerability_id):
            vulnerability_id
            for vulnerability_id in sorted(vulnerability_ids)
        }

        for future in as_completed(futures):
            result = future.result()

            if result["success"]:
                imported += 1
            else:
                failed += 1
                if len(import_errors) < 20:
                    import_errors.append(result)

    return {
        "message": "Ubuntu OSV intelligence sync finished.",
        "ubuntu_version": version,
        "osv_ecosystem": ecosystem,
        "binary_packages_read": len(packages),
        "unique_source_package_versions": len(queries),
        "mapping_method": mapping_method,
        "advisories_discovered": len(vulnerability_ids),
        "advisories_imported_or_updated": imported,
        "advisory_import_failures": failed,
        "sample_advisory_ids": sorted(vulnerability_ids)[:20],
        "errors": import_errors,
        "online_sync": True,
        "system_modified": False,
    }
