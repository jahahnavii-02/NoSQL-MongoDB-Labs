from flask import Blueprint, jsonify

from database import db


# ==========================================
# Blueprint
# ==========================================

analytics_bp = Blueprint(
    "analytics",
    __name__
)


# ==========================================
# Dashboard statistics
# ==========================================

@analytics_bp.route(
    "/dashboard",
    methods=["GET"]
)
def dashboard():

    total_threats = db.threats.count_documents({})

    total_indicators = db.indicators.count_documents({})

    total_sources = db.sources.count_documents({})


    critical_threats = db.threats.count_documents({
        "severity": "Critical"
    })


    high_threats = db.threats.count_documents({
        "severity": "High"
    })


    ransomware_threats = db.threats.count_documents({
        "category": "Ransomware"
    })


    malware_threats = db.threats.count_documents({
        "category": "Malware"
    })


    phishing_threats = db.threats.count_documents({
        "category": "Phishing"
    })


    return jsonify({

        "totalThreats": total_threats,

        "totalIndicators": total_indicators,

        "totalSources": total_sources,

        "criticalThreats": critical_threats,

        "highThreats": high_threats,

        "categories": {

            "ransomware": ransomware_threats,

            "malware": malware_threats,

            "phishing": phishing_threats

        }

    })