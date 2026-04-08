"""
============================================
Community Forum Module
============================================
Q&A discussion board for farmers and consultants.
Farmers can ask questions; consultants can answer and provide expert advice.
"""

import os
from datetime import datetime
from bson.objectid import ObjectId
from database import get_database


def get_threads_collection():
    db = get_database()
    return db['forum_threads']


def get_replies_collection():
    db = get_database()
    return db['forum_replies']


# =========================================================
# Thread CRUD
# =========================================================

def create_thread(user_id: str, user_name: str, user_role: str,
                  title: str, body: str, category: str, tags: list = None) -> dict:
    """Create a new discussion thread."""
    try:
        col = get_threads_collection()
        doc = {
            'user_id': user_id,
            'user_name': user_name,
            'user_role': user_role,               # 'farmer' or 'consultant'
            'title': title,
            'body': body,
            'category': category,
            'tags': tags or [],
            'views': 0,
            'reply_count': 0,
            'is_resolved': False,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = col.insert_one(doc)
        return {'success': True, 'thread_id': str(result.inserted_id)}
    except Exception as e:
        print(f"[ERROR] create_thread: {str(e)}")
        return {'success': False, 'error': str(e)}


def get_threads(category: str = None, search: str = None, page: int = 1, per_page: int = 10) -> dict:
    """Fetch paginated list of forum threads."""
    try:
        col = get_threads_collection()
        query = {}
        if category and category != 'all':
            query['category'] = category
        if search:
            query['$or'] = [
                {'title': {'$regex': search, '$options': 'i'}},
                {'body': {'$regex': search, '$options': 'i'}},
                {'tags': {'$regex': search, '$options': 'i'}}
            ]

        total = col.count_documents(query)
        skip = (page - 1) * per_page

        threads = list(col.find(query, {'body': 0}).sort('created_at', -1).skip(skip).limit(per_page))

        for t in threads:
            t['_id'] = str(t['_id'])
            t['created_at'] = _format_time(t.get('created_at'))
            t['updated_at'] = _format_time(t.get('updated_at'))

        return {
            'success': True,
            'threads': threads,
            'total': total,
            'page': page,
            'pages': (total + per_page - 1) // per_page
        }
    except Exception as e:
        print(f"[ERROR] get_threads: {str(e)}")
        return {'success': False, 'threads': [], 'total': 0}


def get_thread_detail(thread_id: str) -> dict:
    """Get full thread with all replies."""
    try:
        col = get_threads_collection()
        thread = col.find_one({'_id': ObjectId(thread_id)})
        if not thread:
            return {'success': False, 'error': 'Thread not found'}

        # Increment view count
        col.update_one({'_id': ObjectId(thread_id)}, {'$inc': {'views': 1}})

        thread['_id'] = str(thread['_id'])
        thread['created_at'] = _format_time(thread.get('created_at'))

        # Get replies
        replies_col = get_replies_collection()
        replies = list(replies_col.find({'thread_id': thread_id}).sort('created_at', 1))
        for r in replies:
            r['_id'] = str(r['_id'])
            r['created_at'] = _format_time(r.get('created_at'))

        return {'success': True, 'thread': thread, 'replies': replies}
    except Exception as e:
        print(f"[ERROR] get_thread_detail: {str(e)}")
        return {'success': False, 'error': str(e)}


def add_reply(thread_id: str, user_id: str, user_name: str,
              user_role: str, body: str, is_solution: bool = False) -> dict:
    """Add a reply to a thread."""
    try:
        replies_col = get_replies_collection()
        threads_col = get_threads_collection()

        doc = {
            'thread_id': thread_id,
            'user_id': user_id,
            'user_name': user_name,
            'user_role': user_role,
            'body': body,
            'is_solution': is_solution,
            'likes': 0,
            'created_at': datetime.utcnow()
        }
        result = replies_col.insert_one(doc)

        # Update reply count and mark resolved if solution
        update = {'$inc': {'reply_count': 1}, '$set': {'updated_at': datetime.utcnow()}}
        if is_solution:
            update['$set']['is_resolved'] = True

        threads_col.update_one({'_id': ObjectId(thread_id)}, update)

        return {'success': True, 'reply_id': str(result.inserted_id)}
    except Exception as e:
        print(f"[ERROR] add_reply: {str(e)}")
        return {'success': False, 'error': str(e)}


def mark_solution(thread_id: str, reply_id: str, user_id: str) -> dict:
    """Mark a reply as the solution (only thread owner can do this)."""
    try:
        threads_col = get_threads_collection()
        thread = threads_col.find_one({'_id': ObjectId(thread_id)})
        if not thread:
            return {'success': False, 'error': 'Thread not found'}
        if thread['user_id'] != user_id:
            return {'success': False, 'error': 'Only thread owner can mark solution'}

        replies_col = get_replies_collection()
        # Clear previous solutions
        replies_col.update_many({'thread_id': thread_id}, {'$set': {'is_solution': False}})
        # Mark new solution
        replies_col.update_one({'_id': ObjectId(reply_id)}, {'$set': {'is_solution': True}})
        threads_col.update_one({'_id': ObjectId(thread_id)}, {'$set': {'is_resolved': True}})

        return {'success': True, 'message': 'Marked as solution'}
    except Exception as e:
        print(f"[ERROR] mark_solution: {str(e)}")
        return {'success': False, 'error': str(e)}


def get_forum_stats() -> dict:
    """Get overall forum statistics."""
    try:
        threads_col = get_threads_collection()
        replies_col = get_replies_collection()
        return {
            'total_threads': threads_col.count_documents({}),
            'resolved_threads': threads_col.count_documents({'is_resolved': True}),
            'total_replies': replies_col.count_documents({}),
            'total_members': get_database()['users'].count_documents({})
        }
    except Exception as e:
        print(f"[ERROR] get_forum_stats: {str(e)}")
        return {'total_threads': 0, 'resolved_threads': 0, 'total_replies': 0, 'total_members': 0}


FORUM_CATEGORIES = [
    {"id": "disease", "label": "Disease & Pests", "icon": "🦠"},
    {"id": "irrigation", "label": "Irrigation", "icon": "💧"},
    {"id": "fertilizer", "label": "Fertilizers & Soil", "icon": "🌱"},
    {"id": "pricing", "label": "Pricing & Market", "icon": "💰"},
    {"id": "schemes", "label": "Govt Schemes", "icon": "📋"},
    {"id": "equipment", "label": "Equipment", "icon": "🚜"},
    {"id": "general", "label": "General Discussion", "icon": "💬"}
]


def _format_time(dt) -> str:
    if not dt:
        return ''
    now = datetime.utcnow()
    diff = now - dt
    if diff.days > 365:
        return dt.strftime('%d %b %Y')
    if diff.days > 30:
        return dt.strftime('%d %b %Y')
    if diff.days > 0:
        return f"{diff.days}d ago"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes}m ago"
    return "Just now"
