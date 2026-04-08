"""
============================================
Disease Recommendation Engine
============================================
Provides smart treatment recommendations after a disease is detected.
Uses rule-based logic with data curated by agronomists.
"""

import os
from datetime import datetime
from database import get_database


def get_recommendations_collection():
    db = get_database()
    return db['recommendations']


# =========================================================
# Disease Recommendation Database (Expert Curated)
# =========================================================
DISEASE_RECOMMENDATIONS = {
    "Black Rot": {
        "disease_name": "Black Rot",
        "scientific_name": "Guignardia bidwellii",
        "severity": "High",
        "description": "Black rot is a fungal disease causing dark lesions on leaves, stems, and fruit. It can destroy an entire harvest if left untreated.",
        "symptoms": [
            "Small yellow spots on leaves that turn brown with black borders",
            "Mummified shriveled black berries remaining on vine",
            "White to tan lesions on shoots with black dots (pycnidia)",
            "Circular lesions on leaves with a tan center and dark border"
        ],
        "treatments": [
            {
                "type": "Chemical",
                "name": "Mancozeb 75% WP",
                "dosage": "2.5 kg per acre mixed with 500 liters of water",
                "frequency": "Every 10-14 days during wet weather",
                "cost_estimate": "₹450-600 per application"
            },
            {
                "type": "Chemical",
                "name": "Captan 50% WP",
                "dosage": "2 kg per acre in 500L water",
                "frequency": "Every 7-10 days",
                "cost_estimate": "₹350-500 per application"
            },
            {
                "type": "Biological",
                "name": "Trichoderma viride",
                "dosage": "500g per acre with 200L water as foliar spray",
                "frequency": "Every 15-21 days",
                "cost_estimate": "₹200-300 per application"
            }
        ],
        "preventive_measures": [
            "Remove and destroy infected plant parts immediately",
            "Apply dormant spray (lime sulfur) before bud break",
            "Maintain proper vine spacing for air circulation",
            "Avoid overhead irrigation; use drip irrigation instead",
            "Apply preventive fungicide sprays from bud break onwards"
        ],
        "best_time_to_spray": "Early morning (6-9 AM) or evening (4-6 PM). Avoid spraying in hot sun.",
        "government_assistance": "Apply for PMFBY crop insurance to cover disease losses",
        "estimated_yield_loss": "20-80% if untreated",
        "recovery_time": "2-4 weeks with proper treatment",
        "cost_analysis": {
            "treatment_cost_per_acre": "₹2,000 - ₹4,500 for full season",
            "potential_loss_if_untreated": "₹25,000 - ₹50,000 per acre",
            "roi": "Treatment cost is 10-15x less than potential loss"
        }
    },

    "Esca (Black Measles)": {
        "disease_name": "Esca (Black Measles)",
        "scientific_name": "Phaeomoniella chlamydospora / Phaeoacremonium spp.",
        "severity": "Very High",
        "description": "Esca is a serious wood disease of grapevines causing internal wood decay, leaf scorch, and in severe cases, sudden vine death ('apoplexy').",
        "symptoms": [
            "Tiger-stripe pattern on leaves (yellow between veins)",
            "Brown necrotic spots on grape berries",
            "Yellowish or reddish margins on leaves",
            "Internal wood staining when cut - shows dark brown/black woody tissue",
            "Sudden wilting (apoplexy) of entire vine in summer heat"
        ],
        "treatments": [
            {
                "type": "Preventive Chemical",
                "name": "Tebuconazole 25.9% EC",
                "dosage": "500ml per acre in 500L water",
                "frequency": "Apply at bud swell and again 21 days later",
                "cost_estimate": "₹700-900 per application"
            },
            {
                "type": "Wood Treatment",
                "name": "Thiophanate-methyl paste",
                "dosage": "Apply directly to pruning wounds",
                "frequency": "After every pruning operation",
                "cost_estimate": "₹150 per vine"
            },
            {
                "type": "Biological",
                "name": "Trichoderma harzianum",
                "dosage": "1g per vine as soil drench",
                "frequency": "Twice a year",
                "cost_estimate": "₹50-100 per vine"
            }
        ],
        "preventive_measures": [
            "Always disinfect pruning shears between vines with 0.5% sodium hypochlorite",
            "Make clean cuts and immediately cover with wound sealant paste",
            "Remove and burn infected wood material - never leave on field",
            "Replace severely infected vines with certified disease-free material",
            "Avoid water stress by maintaining proper irrigation"
        ],
        "best_time_to_spray": "Apply wood treatments immediately after pruning. Foliar sprays: early morning only.",
        "government_assistance": "Check Maharashtra Horticulture Dept for replanting subsidies",
        "estimated_yield_loss": "30-100% in severely infected vineyards",
        "recovery_time": "No full cure possible; management reduces spread",
        "cost_analysis": {
            "treatment_cost_per_acre": "₹5,000 - ₹15,000 for season",
            "potential_loss_if_untreated": "Complete vineyard loss over 5-10 years",
            "roi": "Early intervention is critical – costs increase 5x if delayed"
        }
    },

    "Leaf Blight (Isariopsis Leaf Spot)": {
        "disease_name": "Leaf Blight (Isariopsis Leaf Spot)",
        "scientific_name": "Isariopsis clavispora",
        "severity": "Medium",
        "description": "Leaf blight causes dark angular spots on leaves, reducing photosynthesis and weakening the vine. Can cause premature defoliation.",
        "symptoms": [
            "Angular dark brown spots with yellow halos on leaves",
            "Spots limited by leaf veins giving angular appearance",
            "Premature leaf drop in severe infections",
            "Lesions often appear in clusters on older leaves first"
        ],
        "treatments": [
            {
                "type": "Chemical",
                "name": "Copper Oxychloride 50% WP",
                "dosage": "2 kg per acre in 500L water",
                "frequency": "Every 10-12 days",
                "cost_estimate": "₹250-400 per application"
            },
            {
                "type": "Chemical",
                "name": "Ziram 80% WP",
                "dosage": "2.5 kg per acre",
                "frequency": "Every 10-14 days",
                "cost_estimate": "₹300-450 per application"
            },
            {
                "type": "Organic",
                "name": "Neem Oil Spray (5000 ppm)",
                "dosage": "3ml per liter of water",
                "frequency": "Every 7 days",
                "cost_estimate": "₹100-200 per application"
            }
        ],
        "preventive_measures": [
            "Remove fallen diseased leaves from the field",
            "Improve ventilation by proper pruning",
            "Avoid overhead irrigation that keeps leaves wet",
            "Apply preventive sprays from early leaf stage"
        ],
        "best_time_to_spray": "Early morning. Ensure leaves are dry by evening.",
        "government_assistance": "PMFBY insurance covers disease-related losses",
        "estimated_yield_loss": "10-30% if untreated",
        "recovery_time": "1-3 weeks with consistent treatment",
        "cost_analysis": {
            "treatment_cost_per_acre": "₹1,500 - ₹3,000 per season",
            "potential_loss_if_untreated": "₹10,000 - ₹20,000 per acre",
            "roi": "Treatment highly cost-effective at 5-7x ROI"
        }
    },

    "Healthy": {
        "disease_name": "Healthy Plant",
        "scientific_name": "N/A",
        "severity": "None",
        "description": "Your grapevine appears healthy! Maintain good agricultural practices to keep it that way.",
        "symptoms": [],
        "treatments": [],
        "preventive_measures": [
            "Continue regular monitoring every 7-10 days",
            "Maintain balanced fertilization (N:P:K as per soil test)",
            "Ensure proper irrigation scheduling (drip preferred)",
            "Apply preventive fungicide spray at bud break stage as a precaution",
            "Keep records for better yield planning"
        ],
        "best_time_to_spray": "Apply preventive sprays at bud break and fruit set stages.",
        "government_assistance": "Explore PKVY for organic farming subsidies to maximize profits",
        "estimated_yield_loss": "0% - Excellent condition!",
        "recovery_time": "N/A",
        "cost_analysis": {
            "treatment_cost_per_acre": "₹800 - ₹1,500 for preventive measures",
            "potential_loss_if_untreated": "N/A",
            "roi": "Prevention is always cheaper than cure"
        }
    }
}

# Map common disease name variations to our database
DISEASE_NAME_MAP = {
    "black rot": "Black Rot",
    "blackrot": "Black Rot",
    "esca": "Esca (Black Measles)",
    "black measles": "Esca (Black Measles)",
    "esca (black measles)": "Esca (Black Measles)",
    "leaf blight": "Leaf Blight (Isariopsis Leaf Spot)",
    "isariopsis": "Leaf Blight (Isariopsis Leaf Spot)",
    "leaf blight (isariopsis leaf spot)": "Leaf Blight (Isariopsis Leaf Spot)",
    "healthy": "Healthy",
    "grape leaves healthy": "Healthy"
}


def get_recommendation(disease_name: str) -> dict:
    """
    Get recommendation for a detected disease.

    Args:
        disease_name: Name of the detected disease (from ML model)

    Returns:
        dict with detailed recommendation
    """
    # Normalize disease name
    normalized = disease_name.lower().strip()
    mapped_name = DISEASE_NAME_MAP.get(normalized, disease_name)

    recommendation = DISEASE_RECOMMENDATIONS.get(mapped_name)

    if not recommendation:
        # Try partial match
        for key in DISEASE_RECOMMENDATIONS:
            if normalized in key.lower() or key.lower() in normalized:
                recommendation = DISEASE_RECOMMENDATIONS[key]
                break

    if not recommendation:
        # Default unknown disease response
        recommendation = {
            "disease_name": disease_name,
            "severity": "Unknown",
            "description": f"Disease '{disease_name}' detected. Consult your local Krishi Vigyan Kendra (KVK) for expert diagnosis.",
            "symptoms": [],
            "treatments": [{
                "type": "Consult Expert",
                "name": "Contact KVK (Krishi Vigyan Kendra)",
                "dosage": "N/A",
                "frequency": "As advised by expert",
                "cost_estimate": "Free consultation available"
            }],
            "preventive_measures": [
                "Isolate potentially infected plants",
                "Contact your local agriculture officer",
                "Do not apply chemicals without expert advice"
            ],
            "best_time_to_spray": "As per expert recommendation",
            "government_assistance": "Contact District Agriculture Officer for guidance",
            "estimated_yield_loss": "Unknown",
            "recovery_time": "Unknown",
            "cost_analysis": {}
        }

    return {'success': True, 'recommendation': recommendation}


def save_recommendation_log(user_id: str, image_path: str, disease: str, confidence: float) -> str:
    """Save a recommendation log for tracking."""
    try:
        col = get_recommendations_collection()
        doc = {
            'user_id': user_id,
            'image_path': image_path,
            'disease': disease,
            'confidence': confidence,
            'recommendation': get_recommendation(disease).get('recommendation', {}),
            'timestamp': datetime.utcnow()
        }
        result = col.insert_one(doc)
        return str(result.inserted_id)
    except Exception as e:
        print(f"[ERROR] save_recommendation_log: {str(e)}")
        return None
