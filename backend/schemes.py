"""
============================================
Government Schemes, Subsidies & Carbon Credit Module
============================================
Provides information on government agri schemes and carbon credit opportunities.
Data is curated (no public API available) and stored in MongoDB.
"""

import os
from datetime import datetime
from database import get_database


def get_schemes_collection():
    db = get_database()
    return db['schemes']


def get_carbon_collection():
    db = get_database()
    return db['carbon_credits']


# =========================================================
# Government Schemes Data (Curated for Maharashtra Farmers)
# =========================================================
GOVERNMENT_SCHEMES = [
    {
        "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "category": "Income Support",
        "description": "Central government scheme providing ₹6,000/year direct income support to all farmer families in 3 equal instalments.",
        "benefit": "₹6,000 per year (₹2,000 every 4 months)",
        "eligibility": ["Small and marginal farmers", "Landholding of 2 hectares or less", "Valid Aadhaar card", "Active bank account"],
        "how_to_apply": "Apply at CSC Centre or pmkisan.gov.in portal. Need Aadhaar, land records, and bank passbook.",
        "documents": ["Aadhaar Card", "Land Records (7/12 Utara)", "Bank Passbook", "Mobile Number"],
        "state": "All India",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "active": True,
        "website": "https://pmkisan.gov.in"
    },
    {
        "name": "PKVY (Paramparagat Krishi Vikas Yojana)",
        "category": "Organic Farming",
        "description": "Promotes organic farming by providing financial assistance to farmer clusters for cluster development and certification.",
        "benefit": "₹50,000 per hectare over 3 years for organic certification",
        "eligibility": ["Minimum 20 farmers in a cluster", "Min 50 acres of land", "Willing to adopt organic practices"],
        "how_to_apply": "Contact local Krishi Vibhag or apply via pgsindia.net",
        "documents": ["Aadhaar Card", "Land Records", "Farmer ID", "Group Registration"],
        "state": "All India",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "active": True,
        "website": "https://pgsindia-ncof.gov.in"
    },
    {
        "name": "PMFBY (Pradhan Mantri Fasal Bima Yojana)",
        "category": "Crop Insurance",
        "description": "Crop Insurance scheme to provide financial support to farmers suffering crop loss/damage due to unforeseen events.",
        "benefit": "Crop coverage up to sum insured; premium: 1.5%-2% for Rabi, 2% for Kharif",
        "eligibility": ["All farmers growing notified crops", "Loanee farmers (mandatory)", "Non-loanee voluntary"],
        "how_to_apply": "Through banks or pmfby.gov.in before cut-off dates",
        "documents": ["Aadhaar Card", "Bank Account", "Sowing Certificate", "Land Records"],
        "state": "All India",
        "ministry": "Ministry of Agriculture",
        "active": True,
        "website": "https://pmfby.gov.in"
    },
    {
        "name": "Nanaji Deshmukh Krishi Sanjivani Project (MH)",
        "category": "Climate Resilient Farming",
        "description": "Maharashtra government project to make farming climate resilient with micro-irrigation, soil health improvement, and crop diversification.",
        "benefit": "Up to 65-95% subsidy on micro-irrigation systems for grape farmers",
        "eligibility": ["Farmers in Vidharbha, Marathwada regions", "Small & marginal farmers prioritized"],
        "how_to_apply": "Apply at cluster level project offices or mahapocra.gov.in",
        "documents": ["7/12 Utara", "Aadhaar Card", "Bank Details", "Caste Certificate (if applicable)"],
        "state": "Maharashtra",
        "ministry": "Maharashtra Agriculture Department",
        "active": True,
        "website": "https://mahapocra.gov.in"
    },
    {
        "name": "PM Kisan Maan Dhan Yojana (PM-KMY)",
        "category": "Pension",
        "description": "Pension scheme for small and marginal farmers. Monthly pension of ₹3,000 after 60 years of age.",
        "benefit": "₹3,000/month pension after age 60",
        "eligibility": ["Age 18-40 years", "Small/marginal farmer (up to 2 ha land)", "Not covered under NPS, ESIC, EPFO"],
        "how_to_apply": "Register at CSC centres with Aadhaar and bank details",
        "documents": ["Aadhaar Card", "Bank Passbook", "Land Records", "Photo"],
        "state": "All India",
        "ministry": "Ministry of Agriculture",
        "active": True,
        "website": "https://maandhan.in"
    },
    {
        "name": "Grape Grower Development Scheme (Maharashtra)",
        "category": "Crop Specific",
        "description": "Maharashtra state scheme specifically for grape growers for modern viticultural practices, training, and subsidy on grape varieties.",
        "benefit": "₹25,000 to ₹40,000 per acre subsidy for new vineyard development",
        "eligibility": ["Maharashtra grape farmers", "Min 0.5 acre land", "Adoption of recommended varieties"],
        "how_to_apply": "Contact District Superintendent Officer (DSO) at Horticulture Department",
        "documents": ["7/12 Utara", "Aadhaar Card", "Photo", "Bank Account"],
        "state": "Maharashtra",
        "ministry": "Maharashtra Horticulture Department",
        "active": True,
        "website": "https://mahaagri.gov.in"
    },
    {
        "name": "KCC (Kisan Credit Card)",
        "category": "Credit",
        "description": "Credit card for farmers providing timely credit for cultivation expenses, post-harvest expenses, and allied activities.",
        "benefit": "Credit up to ₹3 lakh at 4% interest rate per year (with subsidy)",
        "eligibility": ["All farmers, share croppers, tenant farmers", "Joint liability groups"],
        "how_to_apply": "Apply at nearest bank branch (SBI, Bank of Maharashtra, etc.)",
        "documents": ["Aadhaar Card", "Land Records", "Passport photo", "Bank Account"],
        "state": "All India",
        "ministry": "Ministry of Finance / RBI",
        "active": True,
        "website": "https://pmkisan.gov.in/kcc.aspx"
    },
    {
        "name": "Drip Irrigation Subsidy (Maharashtra)",
        "category": "Irrigation",
        "description": "Maharashtra government provides subsidy on drip and sprinkler irrigation systems to save water and increase yield.",
        "benefit": "55-65% subsidy for small/marginal, 45% for others; special 95% for SC/ST farmers",
        "eligibility": ["All farmers in Maharashtra", "Valid land ownership"],
        "how_to_apply": "Apply through registered micro-irrigation dealers or MahaAgri portal",
        "documents": ["7/12 Utara", "Aadhaar Card", "Dealer Quotation", "Bank Details"],
        "state": "Maharashtra",
        "ministry": "Maharashtra Agriculture Dept",
        "active": True,
        "website": "https://mahaagri.gov.in"
    }
]

# =========================================================
# Carbon Credit Information Data
# =========================================================
CARBON_CREDIT_INFO = [
    {
        "title": "What are Carbon Credits?",
        "description": "Carbon credits are certificates representing the reduction of 1 tonne of CO₂ emissions. Farmers can earn these by adopting eco-friendly practices and sell them in carbon markets for extra income.",
        "potential_earning": "₹500 to ₹2,000 per tonne of CO₂ reduced",
        "category": "basics"
    },
    {
        "title": "Organic Farming Carbon Credits",
        "description": "By switching to organic farming, farmers reduce chemical inputs and build soil carbon. Each acre of organic grape farming can sequester 1-2 tonnes of CO₂ per year.",
        "potential_earning": "₹1,000 - ₹4,000 per acre per year",
        "how_to": ["Get PGS/NOP organic certification", "Maintain 3-year organic records", "Register with carbon aggregator like CarbonCopy or Terra CO2"],
        "category": "organic"
    },
    {
        "title": "Drip Irrigation Water Conservation Credits",
        "description": "By using drip irrigation instead of flood irrigation, farmers save significant water and energy, qualifying for carbon credits.",
        "potential_earning": "₹600 - ₹1,200 per acre per year",
        "how_to": ["Install government-subsidized drip system", "Maintain usage logs", "Register with VERRA or CDM project developers"],
        "category": "irrigation"
    },
    {
        "title": "Agroforestry Carbon Credits",
        "description": "Planting trees alongside crops (agroforestry) captures CO₂ through photosynthesis. Grape farmers can plant shade trees on field borders.",
        "potential_earning": "₹500 - ₹3,000 per acre depending on tree density",
        "how_to": ["Plant approved tree species (Neem, Pongamia, Fruit trees)", "Maintain 5-year records", "Partner with Tree Planet or similar aggregator"],
        "category": "agroforestry"
    },
    {
        "title": "Biochar Application Credits",
        "description": "Applying biochar (burnt organic waste) to farm soil locks carbon for 100+ years and improves soil fertility for grape vines.",
        "potential_earning": "₹2,000 - ₹5,000 per tonne of biochar applied",
        "how_to": ["Source or produce biochar from crop residues", "Document soil application", "Register under Verra VCS standard"],
        "category": "biochar"
    },
    {
        "title": "How to Register for Carbon Credits in India",
        "description": "India is launching a Carbon Market under BEE (Bureau of Energy Efficiency). Farmers can register through aggregators.",
        "steps": [
            "Contact certified carbon aggregators: Terra CO2, CarbonCopy India, AgriCarbon",
            "Get your farm assessed for carbon sequestration potential",
            "Sign a 5-10 year agreement with the aggregator",
            "Adopt recommended sustainable practices",
            "Receive annual payments for verified carbon credits"
        ],
        "contact": "Bureau of Energy Efficiency (BEE): www.beeindia.gov.in",
        "category": "registration"
    }
]


def init_schemes_data():
    """Initialize the database with scheme and carbon credit data."""
    try:
        col = get_schemes_collection()
        if col.count_documents({}) == 0:
            for scheme in GOVERNMENT_SCHEMES:
                scheme['created_at'] = datetime.utcnow()
            col.insert_many(GOVERNMENT_SCHEMES)
            print("[✓] Government schemes data initialized")

        col2 = get_carbon_collection()
        if col2.count_documents({}) == 0:
            for credit in CARBON_CREDIT_INFO:
                credit['created_at'] = datetime.utcnow()
            col2.insert_many(CARBON_CREDIT_INFO)
            print("[✓] Carbon credit data initialized")
    except Exception as e:
        print(f"[ERROR] init_schemes_data: {str(e)}")


def get_schemes(category: str = None, state: str = None) -> list:
    """Get government schemes with optional filters."""
    try:
        col = get_schemes_collection()
        query = {'active': True}
        if category:
            query['category'] = {'$regex': category, '$options': 'i'}
        if state and state != 'All':
            query['$or'] = [{'state': 'All India'}, {'state': state}]

        results = list(col.find(query, {'_id': 0, 'created_at': 0}))

        # If DB is empty, return from memory
        if not results:
            results = GOVERNMENT_SCHEMES
            if category:
                results = [s for s in results if category.lower() in s.get('category', '').lower()]

        return results
    except Exception as e:
        print(f"[ERROR] get_schemes: {str(e)}")
        return GOVERNMENT_SCHEMES


def get_carbon_credits() -> list:
    """Get carbon credit information."""
    try:
        col = get_carbon_collection()
        results = list(col.find({}, {'_id': 0, 'created_at': 0}))
        return results if results else CARBON_CREDIT_INFO
    except Exception as e:
        print(f"[ERROR] get_carbon_credits: {str(e)}")
        return CARBON_CREDIT_INFO


def get_scheme_categories() -> list:
    """Return list of unique scheme categories."""
    return list(set([s['category'] for s in GOVERNMENT_SCHEMES]))
