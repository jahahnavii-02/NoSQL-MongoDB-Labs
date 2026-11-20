from flask import Blueprint, request, jsonify

from database import db


# ==========================================
# Blueprint
# ==========================================

search_bp = Blueprint(
    "search",
    __name__
)


# ==========================================
# Global threat search
# ==========================================

@search_bp.route("/", methods=["GET"])
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    severity = request.args.get(
        "severity",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()


    # --------------------------------------
    # Build MongoDB query
    # --------------------------------------

    mongo_query = {}


    if query:

        mongo_query["$or"] = [

            {
                "title": {
                    "$regex": query,
                    "$options": "i"
                }
            },

            {
                "description": {
                    "$regex": query,
                    "$options": "i"
                }
            },

            {
                "category": {
                    "$regex": query,
                    "$options": "i"
                }
            },

            {
                "tags": {
                    "$regex": query,
                    "$options": "i"
                }
            },

            {
                "indicatorIds": {
                    "$regex": query,
                    "$options": "i"
                }
            }
        ]


    if severity:

        mongo_query["severity"] = {
            "$regex": severity,
            "$options": "i"
        }


    if category:

        mongo_query["category"] = {
            "$regex": category,
            "$options": "i"
        }


    # --------------------------------------
    # Execute search
    # --------------------------------------

    results = list(
        db.threats.find(
            mongo_query,
            {
                "_id": 0
            }
        ).sort(
            "publishedDate",
            -1
        )
    )


    return jsonify({
        "query": query,
        "count": len(results),
        "results": results
    })