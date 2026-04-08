"""
============================================
Equipment Marketplace Module (OLX-type)
============================================
Buy/sell farm equipment listings with image upload support.
Farmers can post ads and contact sellers via WhatsApp or phone.
"""

import os
import json
from datetime import datetime
from bson.objectid import ObjectId
from database import get_database


def get_ads_collection():
    db = get_database()
    return db['equipment_ads']


EQUIPMENT_CATEGORIES = [
    {"id": "tractor", "label": "Tractors", "icon": "🚜"},
    {"id": "sprayer", "label": "Sprayers & Pumps", "icon": "💦"},
    {"id": "harvester", "label": "Harvesters", "icon": "⚙️"},
    {"id": "irrigation", "label": "Irrigation Equipment", "icon": "💧"},
    {"id": "tools", "label": "Hand Tools", "icon": "🔧"},
    {"id": "storage", "label": "Storage & Packaging", "icon": "📦"},
    {"id": "vehicle", "label": "Farm Vehicles", "icon": "🛻"},
    {"id": "other", "label": "Other Equipment", "icon": "🌾"}
]


def create_ad(user_id: str, user_name: str, user_phone: str,
              title: str, description: str, price: float,
              category: str, condition: str, location: str,
              negotiable: bool = True, image_paths: list = None) -> dict:
    """Create a new equipment listing."""
    try:
        col = get_ads_collection()
        doc = {
            'user_id': user_id,
            'user_name': user_name,
            'user_phone': user_phone,
            'title': title,
            'description': description,
            'price': float(price),
            'category': category,
            'condition': condition,          # 'new', 'good', 'fair', 'poor'
            'location': location,
            'negotiable': negotiable,
            'image_paths': image_paths or [],
            'status': 'active',             # 'active', 'sold', 'inactive'
            'views': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = col.insert_one(doc)
        return {'success': True, 'ad_id': str(result.inserted_id)}
    except Exception as e:
        print(f"[ERROR] create_ad: {str(e)}")
        return {'success': False, 'error': str(e)}


def get_ads(category: str = None, search: str = None,
            min_price: float = None, max_price: float = None,
            condition: str = None, location: str = None,
            page: int = 1, per_page: int = 12) -> dict:
    """Fetch paginated equipment ads with filters."""
    try:
        col = get_ads_collection()
        query = {'status': 'active'}

        if category and category != 'all':
            query['category'] = category
        if search:
            query['$or'] = [
                {'title': {'$regex': search, '$options': 'i'}},
                {'description': {'$regex': search, '$options': 'i'}}
            ]
        if condition:
            query['condition'] = condition
        if location:
            query['location'] = {'$regex': location, '$options': 'i'}
        if min_price is not None or max_price is not None:
            query['price'] = {}
            if min_price is not None:
                query['price']['$gte'] = float(min_price)
            if max_price is not None:
                query['price']['$lte'] = float(max_price)

        total = col.count_documents(query)
        skip = (page - 1) * per_page

        ads = list(col.find(query).sort('created_at', -1).skip(skip).limit(per_page))

        for a in ads:
            a['_id'] = str(a['_id'])
            a['created_at'] = _format_time(a.get('created_at'))

        return {
            'success': True,
            'ads': ads,
            'total': total,
            'page': page,
            'pages': (total + per_page - 1) // per_page
        }
    except Exception as e:
        print(f"[ERROR] get_ads: {str(e)}")
        return {'success': False, 'ads': [], 'total': 0}


def get_ad_detail(ad_id: str) -> dict:
    """Get a single ad with full details."""
    try:
        col = get_ads_collection()
        ad = col.find_one({'_id': ObjectId(ad_id)})
        if not ad:
            return {'success': False, 'error': 'Ad not found'}

        col.update_one({'_id': ObjectId(ad_id)}, {'$inc': {'views': 1}})
        ad['_id'] = str(ad['_id'])
        ad['created_at'] = ad['created_at'].strftime('%d %b %Y') if ad.get('created_at') else ''

        return {'success': True, 'ad': ad}
    except Exception as e:
        print(f"[ERROR] get_ad_detail: {str(e)}")
        return {'success': False, 'error': str(e)}


def update_ad_status(ad_id: str, user_id: str, status: str) -> dict:
    """Update ad status (sold/inactive). Only owner can do this."""
    try:
        col = get_ads_collection()
        result = col.update_one(
            {'_id': ObjectId(ad_id), 'user_id': user_id},
            {'$set': {'status': status, 'updated_at': datetime.utcnow()}}
        )
        if result.matched_count == 0:
            return {'success': False, 'error': 'Ad not found or unauthorized'}
        return {'success': True, 'message': f'Ad marked as {status}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def delete_ad(ad_id: str, user_id: str) -> dict:
    """Delete an ad. Only owner can delete."""
    try:
        col = get_ads_collection()
        result = col.delete_one({'_id': ObjectId(ad_id), 'user_id': user_id})
        if result.deleted_count == 0:
            return {'success': False, 'error': 'Ad not found or unauthorized'}
        return {'success': True, 'message': 'Ad deleted successfully'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_user_ads(user_id: str) -> list:
    """Get all ads posted by a specific user."""
    try:
        col = get_ads_collection()
        ads = list(col.find({'user_id': user_id}).sort('created_at', -1))
        for a in ads:
            a['_id'] = str(a['_id'])
            a['created_at'] = _format_time(a.get('created_at'))
        return ads
    except Exception as e:
        print(f"[ERROR] get_user_ads: {str(e)}")
        return []


def get_marketplace_stats() -> dict:
    """Get marketplace stats."""
    try:
        col = get_ads_collection()
        return {
            'total_ads': col.count_documents({'status': 'active'}),
            'total_sold': col.count_documents({'status': 'sold'}),
            'categories': len(EQUIPMENT_CATEGORIES)
        }
    except Exception as e:
        return {'total_ads': 0, 'total_sold': 0, 'categories': 8}


def _format_time(dt) -> str:
    if not dt:
        return ''
    now = datetime.utcnow()
    diff = now - dt
    if diff.days > 30:
        return dt.strftime('%d %b %Y')
    if diff.days > 0:
        return f"{diff.days}d ago"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    minutes = diff.seconds // 60
    return f"{minutes}m ago" if minutes > 0 else "Just now"
