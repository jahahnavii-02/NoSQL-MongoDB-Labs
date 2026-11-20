from flask import Blueprint, jsonify

from database import db


# ==========================================
# Blueprint
# ==========================================

threats_bp = Blueprint(
    "threats",
    __name__
)


# ==========================================
# Get all threats
# ==========================================

@threats_bp.route("/", methods=["GET"])
def get_threats():

    threats = list(
        db.threats.find(
            {},
            {
                "_id": 0
            }
        ).sort(
            "publishedDate",
            -1
        )
    )

    return jsonify(threats)


# ==========================================
# Get single threat
# ==========================================

@threats_bp.route("/<threat_id>", methods=["GET"])
def get_threat(threat_id):

    threat = db.threats.find_one(
        {
            "_id": threat_id
        },
        {
            "_id": 0
        }
    )

    if not threat:

        return jsonify({
            "error": "Threat not found"
        }), 404

    return jsonify(threat)


# ==========================================
# Threat classification
# ==========================================

@threats_bp.route("/<threat_id>/classification", methods=["GET"])
def get_classification(threat_id):

    threat = db.threats.find_one(
        {
            "_id": threat_id
        },
        {
            "_id": 0,
            "classification": 1,
            "severity": 1,
            "category": 1,
            "title": 1
        }
    )

    if not threat:

        return jsonify({
            "error": "Threat not found"
        }), 404

    return jsonify({
        "title": threat.get(
            "title",
            "Unknown"
        ),
        "category": threat.get(
            "category",
            "Unknown"
        ),
        "severity": threat.get(
            "severity",
            "Unknown"
        ),
        "classification": threat.get(
            "classification",
            {}
        )
    })