from flask_caching import Cache
from flask import current_app

cache = Cache(config={
    'CACHE_TYPE': 'filesystem',  # or 'redis' if you have Redis installed
    'CACHE_DIR': 'cache',  # directory for filesystem cache
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_THRESHOLD': 1000,  # maximum number of items the cache will store
    'CACHE_OPTIONS': {
        'mode': 0o600  # file permissions
    }
})

def clear_all_caches():
    """Clear all caches across all processes"""
    try:
        # Clear the cache
        cache.clear()
        
        # Also clear memoized functions
        cache.delete_memoized(get_performance)
        cache.delete_memoized(get_all_student_performance)
        cache.delete_memoized(get_at_risk_students)
        cache.delete_memoized(get_subjects)
        cache.delete_memoized(school_year_summary)
        
        # Force clear all caches for these routes
        for page in range(1, 11):
            cache.delete_memoized(get_all_student_performance, page=page)
            cache.delete_memoized(get_at_risk_students, page=page)
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error clearing cache: {str(e)}")
        return False