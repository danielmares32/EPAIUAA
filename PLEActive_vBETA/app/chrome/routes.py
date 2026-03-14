from flask import Blueprint, jsonify
from .service import get_chrome_profiles

bp = Blueprint('chrome', __name__, url_prefix="/chrome")

@bp.route('/profiles', methods=['GET'])
def profiles():
    """ Devuelve los perfiles de Chrome """
    profiles = get_chrome_profiles()
    return jsonify(profiles)





from .service import get_keywords_for_profile

@bp.route('/keywords/<profile_dir>', methods=['GET'])
def keywords(profile_dir):
    """
    Devuelve hasta 10 URLs distintas + keywords extraídas.
    """
    try:
        data = get_keywords_for_profile(profile_dir, limit=10)
        return jsonify({"profile": profile_dir, "results": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500