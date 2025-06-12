import os
import socket
from loguru import logger
from flask import Flask, request, jsonify
from celery import Celery
from db_manager import DatabaseManager, initialize_database
from tool import get_feed_entry, insert_feed, insert_keyword, get_keywords_from_deepseek

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'

# Celery configuration
app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL')
app.config['CELERY_INCLUDE'] = []
app.config['CELERY_ROUTES'] = {
    'get_feed_info': {'queue': 'fetcher'},
    'tag_unprocessed_feeds': {'queue': 'tagger'}
}

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

FEED_DICT = {
    "feed://eugene-wei.squarespace.com/blog?format=rss": "technology/blog",
    "https://ciechanow.ski/atom.xml": "technology",
    "https://tatianamac.com/feed/feed.xml": "technology",
    "https://interfacelovers.com/feed": "design ",
}


@celery.task(name='get_feed_info')
def get_feed_info(feed_dict=None):
    all_entries = []
    if isinstance(feed_dict, dict):
        logger.info(f"Updating FEED_DICT with: {feed_dict}")
        FEED_DICT.update(feed_dict)

    for feed_url, fclass in FEED_DICT.items():
        logger.info(f"Fetching feed: {feed_url} with class: {fclass}")
        for entry in get_feed_entry(feed_url):
            url = entry.get('url', '') or entry.get('link', '')
            title = entry.get('title', '')
            description = entry.get('description', '')
            feed_id = insert_feed(url, title, description)
            if feed_id:
                logger.info(f"Inserted feed: {feed_id} - {title}")
                for feed_class in fclass.split('/'):
                    insert_keyword(feed_id, feed_class)
                    logger.info(f"Inserted keyword '{feed_class}' for feed {feed_id}")

    return {
        'current': len(all_entries),
        'total': len(all_entries),
        'status': 'Task completed!',
        'result': len(all_entries)
    }


@celery.task(name="tag_unprocessed_feeds")
def tag_unprocessed_feeds():
    db = DatabaseManager()

    # Query feeds that are not tagged yet
    query = "SELECT id, url FROM feeds WHERE is_tagged = 0 LIMIT 50"
    feeds = db.execute_query(query, fetch=True)

    if not feeds:
        logger.info("✅ No untagged feeds found.")
        return {"result": 0, "status": "No untagged feeds"}

    tagged_count = 0
    for feed in feeds:
        feed_id = feed['id']
        url = feed['url']
        logger.info(f"Processing Feed ID {feed_id}, URL: {url}")

        keywords = get_keywords_from_deepseek(url)
        logger.info(f"🔖 Extracted keywords for Feed ID {feed_id}: {keywords}")

        for kw in keywords:
            try:
                insert_keyword(feed_id, kw)
                logger.info(f"✅ Inserted keyword '{kw}' for feed {feed_id}")
            except Exception as e:
                logger.warning(f"❌ Failed to insert keyword (Feed ID {feed_id} / Keyword: {kw}): {e}")

        try:
            update_feed_tagged_query = "UPDATE feeds SET is_tagged = 1 WHERE id = %s"
            DatabaseManager(use_slave=False).execute_query(update_feed_tagged_query, (feed_id,))
            tagged_count += 1
            logger.info(f"✅ Marked feed {feed_id} as tagged.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to mark feed {feed_id} as tagged: {e}")

    logger.info(f"🎉 Finished tagging {tagged_count} feed(s).")
    return {"result": tagged_count, "status": "Completed"}


# =======================================================================================================================

@app.route('/api/feeds_with_keywords', methods=['GET'])
def get_feeds_with_keywords():
    db = DatabaseManager(use_slave=True)

    # Get pagination parameters
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        if page < 1 or page_size < 1:
            raise ValueError()
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    offset = (page - 1) * page_size

    # Query paginated feeds (from master only)
    feed_query = """
        SELECT id, url, title, description, is_tagged
        FROM feeds
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """
    feeds = db.execute_query(feed_query, (page_size, offset), fetch=True)

    if not feeds:
        return jsonify({
            'server_ip': socket.gethostbyname(socket.gethostname()),
            'page': page,
            'page_size': page_size,
            'total': 0,
            'feeds': []
        })

    # Collect feed_ids for keyword lookup
    feed_ids = [feed['id'] for feed in feeds]
    keyword_query = """
        SELECT feed_id, keyword FROM keyword WHERE feed_id IN %s
    """
    keyword_rows = db.execute_query(keyword_query, (feed_ids,), fetch=True)

    # Build keyword mapping
    keyword_map = {}
    for row in keyword_rows:
        keyword_map.setdefault(row['feed_id'], []).append(row['keyword'])

    # Attach keywords to feed data
    for feed in feeds:
        feed['is_tagged'] = bool(feed['is_tagged'])
        feed['keywords'] = keyword_map.get(feed['id'], [])

    # Get total count
    total = db.execute_query("SELECT COUNT(*) AS total FROM feeds", fetch=True)[0]['total']

    return jsonify({
        'server_ip': socket.gethostbyname(socket.gethostname()),
        'page': page,
        'page_size': page_size,
        'total': total,
        'feeds': feeds
    })


@app.route('/trigger_fetch', methods=['POST'])
def trigger_fetch():
    logger.info("Triggering get_feed_info task.")
    get_feed_info.apply_async()
    return 'Fetch task triggered', 200


@app.route('/trigger_tag', methods=['POST'])
def trigger_tag():
    logger.info("Triggering tag_unprocessed_feeds task.")
    tag_unprocessed_feeds.apply_async()
    return 'Tag task triggered', 200


@app.route('/test_backend', methods=['GET'])
def test_backend():
    import socket
    from flask import request
    return jsonify({
        "backend_ip": socket.gethostbyname(socket.gethostname()),
        "backend_port": request.host
    })


if __name__ == '__main__':
    logger.info("Initializing database.")
    initialize_database()
    logger.info("Starting Flask app.")
    app.run(debug=True, host="0.0.0.0")
