from uuid import uuid4
import subprocess
from datetime import datetime, timezone

from pymongo import MongoClient
from backend.core.config import settings


WSL_DISTRIBUTION = settings.WSL_DISTRIBUTION


def _wsl(*args, timeout=45):
    if settings.SCANNER_MODE == "local":
        command = list(args)
    else:
        command = ["wsl.exe", "-d", WSL_DISTRIBUTION, "--", *args]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            (result.stderr.strip() or "WSL command failed.")[:500]
        )
    return result.stdout


def _read_os():
    raw = _wsl("cat", "/etc/os-release")
    details = {}

    for line in raw.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            details[key] = value.strip().strip('"')

    return {
        "name": details.get("NAME", "Unknown"),
        "version": details.get("VERSION_ID", "Unknown"),
        "pretty_name": details.get("PRETTY_NAME", "Unknown"),
        "codename": details.get("VERSION_CODENAME", "Unknown"),
        "architecture": _wsl("dpkg", "--print-architecture").strip(),
        "kernel": _wsl("uname", "-r").strip(),
        "environment": (
            "WSL2" if settings.SCANNER_MODE != "local"
            else "Linux (local/container)"
        ),
    }


def _read_packages():
    raw = _wsl("dpkg-query", "-W")
    packages = []

    for line in raw.splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue

        name, version = parts
        if name and version and version != "<none>":
            packages.append({
                "name": name,
                "base_name": name.split(":")[0].lower(),
                "version": version.strip(),
            })

    return packages


def _version_compare(installed, operator, target):
    result = subprocess.run(
        [
            "wsl.exe", "-d", WSL_DISTRIBUTION, "--",
            "dpkg", "--compare-versions",
            installed, operator, target,
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    if result.returncode not in (0, 1):
        return None

    return result.returncode == 0


def _evaluate_osv_ranges(
    installed,
    affected,
    ubuntu_advisory=False,
    installed_package_name=None,
):
    """
    Ubuntu:
    - Match the exact binary package.
    - Require an OSV fixed event.
    - Compare against that binary's binary_version.
    - Never compare binary versions with source-package versions.

    Debian fallback:
    - Evaluate supported ECOSYSTEM range events.
    """
    if ubuntu_advisory:
        binaries = (
            (affected.get("ecosystem_specific") or {}).get("binaries")
            or []
        )

        installed_name = str(
            installed_package_name or ""
        ).split(":")[0].lower()

        matching_binary = next(
            (
                binary for binary in binaries
                if str(binary.get("binary_name", ""))
                .split(":")[0].lower() == installed_name
            ),
            None,
        )

        if not matching_binary:
            return "version_unknown"

        ranges = affected.get("ranges") or []
        has_fixed_event = any(
            "fixed" in event
            for version_range in ranges
            if version_range.get("type") == "ECOSYSTEM"
            for event in (version_range.get("events") or [])
        )

        if not has_fixed_event:
            return "version_unknown"

        fixed_binary_version = matching_binary.get("binary_version")

        if not fixed_binary_version:
            return "version_unknown"

        comparison = _version_compare(
            installed, "lt", fixed_binary_version
        )

        if comparison is None:
            return "version_unknown"

        return "affected" if comparison else "not_affected"

    exact_versions = affected.get("versions") or []
    ranges = affected.get("ranges") or []

    if exact_versions and not ranges:
        return (
            "affected"
            if installed in exact_versions
            else "not_affected"
        )

    if not ranges:
        return "version_unknown"

    assessments = []

    for version_range in ranges:
        if version_range.get("type") != "ECOSYSTEM":
            continue

        active = False
        evaluable = True

        for event in version_range.get("events") or []:
            if "introduced" in event:
                introduced = event["introduced"]

                if introduced == "0":
                    active = True
                else:
                    comparison = _version_compare(
                        installed, "ge", introduced
                    )
                    if comparison is None:
                        evaluable = False
                        break
                    active = comparison

            elif "fixed" in event:
                comparison = _version_compare(
                    installed, "lt", event["fixed"]
                )
                if comparison is None:
                    evaluable = False
                    break
                active = active and comparison

            elif "last_affected" in event:
                comparison = _version_compare(
                    installed, "le", event["last_affected"]
                )
                if comparison is None:
                    evaluable = False
                    break
                active = active and comparison

        if evaluable:
            assessments.append(
                "affected" if active else "not_affected"
            )

    if "affected" in assessments:
        return "affected"

    if assessments and all(
        item == "not_affected" for item in assessments
    ):
        return "not_affected"

    return "version_unknown"


def _load_osv_records():
    client = MongoClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=4000,
    )

    try:
        collection = client[settings.MONGO_DATABASE]["threats"]

        return list(collection.find(
            {"threat_id": {"$regex": "^OSV-"}},
            {
                "_id": 0,
                "threat_id": 1,
                "external_id": 1,
                "name": 1,
                "severity": 1,
                "cvss_score": 1,
                "affected": 1,
                "source": 1,
            },
        ))
    finally:
        client.close()


def _is_matching_ubuntu_ecosystem(ecosystem, ubuntu_version):
    ecosystem = str(ecosystem or "").strip()

    if not ecosystem:
        return False

    if ecosystem.lower() == "ubuntu":
        return True

    expected = f"Ubuntu:{ubuntu_version}:LTS"
    return ecosystem.lower() == expected.lower()


def _get_matching_installed_packages(affected, package_lookup):
    """
    Match Canonical binary package names exactly.
    Source-package fallback is retained for inventory visibility;
    its assessment remains unknown without binary metadata.
    """
    ecosystem_specific = affected.get("ecosystem_specific") or {}
    binaries = ecosystem_specific.get("binaries") or []

    package_names = [
        str(binary.get("binary_name", "")).split(":")[0].lower()
        for binary in binaries
        if binary.get("binary_name")
    ]

    if not package_names:
        source_name = str(
            (affected.get("package") or {}).get("name", "")
        ).split(":")[0].lower()

        if source_name:
            package_names.append(source_name)

    matched = []
    seen = set()

    for package_name in package_names:
        for installed in package_lookup.get(package_name, []):
            identity = (
                installed["name"],
                installed["version"],
            )

            if identity not in seen:
                seen.add(identity)
                matched.append(installed)

    return matched


def run_linux_scan():
    started_at = datetime.now(timezone.utc)

    os_info = _read_os()
    packages = _read_packages()
    advisories = _load_osv_records()

    ubuntu_version = os_info["version"]

    findings = []
    advisory_matches = 0
    affected_count = 0
    unknown_count = 0
    not_affected_count = 0

    package_lookup = {}

    for package in packages:
        package_lookup.setdefault(
            package["base_name"], []
        ).append(package)

    seen_findings = set()

    for advisory in advisories:
        for affected in advisory.get("affected", []) or []:
            package_info = affected.get("package") or {}
            ecosystem = str(
                package_info.get("ecosystem", "")
            ).strip()

            if ecosystem.lower().startswith("ubuntu:"):
                if not _is_matching_ubuntu_ecosystem(
                    ecosystem, ubuntu_version
                ):
                    continue
                ubuntu_advisory = True

            elif ecosystem.lower() == "ubuntu":
                ubuntu_advisory = True

            elif ecosystem.lower() == "debian":
                ubuntu_advisory = False

            else:
                continue

            installed_packages = _get_matching_installed_packages(
                affected, package_lookup
            )

            for installed in installed_packages:
                identity = (
                    advisory.get("threat_id"),
                    installed["name"],
                    installed["version"],
                    ecosystem,
                )

                if identity in seen_findings:
                    continue

                seen_findings.add(identity)

                assessment = _evaluate_osv_ranges(
                    installed["version"],
                    affected,
                    ubuntu_advisory=ubuntu_advisory,
                    installed_package_name=installed["base_name"],
                )

                advisory_matches += 1

                if assessment == "affected":
                    affected_count += 1
                elif assessment == "version_unknown":
                    unknown_count += 1
                else:
                    not_affected_count += 1

                findings.append({
                    "threat_id": advisory.get("threat_id"),
                    "external_id": advisory.get("external_id"),
                    "name": advisory.get("name"),
                    "severity": advisory.get("severity", "Unknown"),
                    "cvss_score": advisory.get("cvss_score"),
                    "package": installed["name"],
                    "installed_version": installed["version"],
                    "assessment": assessment,
                    "ecosystem": ecosystem,
                })

    completed_at = datetime.now(timezone.utc)
    scan_id = str(uuid4())

    scan_record = {
        "scan_id": scan_id,
        "scan_type": "linux_package_inventory",
        "platform": os_info["pretty_name"],
        "host_id": "wsl-ubuntu",
        "environment": os_info["environment"],
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "completed",
        "package_count": len(packages),
        "advisory_count": len(advisories),
        "advisory_matches": advisory_matches,
        "affected_count": affected_count,
        "unknown_count": unknown_count,
        "not_affected_count": not_affected_count,
        "scanner_mode": "read_only",
    }

    client = MongoClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=4000,
    )

    try:
        db = client[settings.MONGO_DATABASE]

        # Save the scan summary.
        db.scan_runs.insert_one(scan_record)

        # Save every individual package-advisory assessment.
        if findings:
            finding_documents = []

            for finding in findings:
                finding_documents.append({
                    **finding,
                    "finding_id": str(uuid4()),
                    "scan_id": scan_id,
                    "host_id": "wsl-ubuntu",
                    "platform": os_info["pretty_name"],
                    "environment": os_info["environment"],
                    "scanned_at": completed_at,
                })

            db.findings.insert_many(
                finding_documents,
                ordered=False,
            )

    finally:
        client.close()

    return {
        "message": "Read-only Linux scan completed.",
        "scan_id": scan_id,
        "platform": os_info,
        "summary": {
            "installed_packages": len(packages),
            "osv_advisories_checked": len(advisories),
            "package_advisory_matches": advisory_matches,
            "affected_version_matches": affected_count,
            "version_assessment_unknown": unknown_count,
            "not_affected_matches": not_affected_count,
        },
        "findings": findings,
        "safety": {
            "read_only": True,
            "system_modified": False,
            "automatic_remediation": False,
        },
    }
