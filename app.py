import time
from datetime import datetime
import jieba.analyse
from loguru import logger
import feedparser
from flask import Flask, request, render_template, redirect, url_for, jsonify
from celery import Celery
from db_manager import DatabaseManager
from tool import get_feed_entry, insert_feed, insert_keyword, get_keywords_from_deepseek

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://:5bAlEv0xt4tV@192.168.133.132:16379/3'
app.config['CELERY_RESULT_BACKEND'] = 'redis://:5bAlEv0xt4tV@192.168.133.132:16379/3'
app.config['CELERY_INCLUDE'] = []

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

FEED_DICT = {
    "feed://eugene-wei.squarespace.com/blog?format=rss": "technology/blog",
}


@celery.task(bind=True)
def get_feed_info(self):
    all_entries = []

    for feed_url, fclass in FEED_DICT.items():
        for entry in get_feed_entry(feed_url):
            url = entry.get('url', '') or entry.get('link', '')
            title = entry.get('title', '')
            description = entry.get('description', '')
            feed_id = insert_feed(url, title, description)
            if feed_id:
                for feed_class in fclass.split('/'):
                    insert_keyword(feed_id, feed_class)

    return {
        'current': len(all_entries),
        'total': len(all_entries),
        'status': 'Task completed!',
        'result': len(all_entries)
    }


@celery.task(name="tag_unprocessed_feeds")
def tag_unprocessed_feeds():
    db = DatabaseManager()

    # 查询未打标签的 feeds
    query = "SELECT id, url FROM feeds WHERE is_tagged = 0 LIMIT 50"
    feeds = db.execute_query(query, fetch=True)

    if not feeds:
        logger.info("✅ 没有未处理的 feeds")
        return {"result": 0, "status": "No untagged feeds"}

    insert_keyword_query = """
        INSERT INTO keyword (feed_id, keyword, created_at, updated_at)
        VALUES (%s, %s, %s, %s)
    """

    update_feed_tagged_query = "UPDATE feeds SET is_tagged = 1 WHERE id = %s"

    tagged_count = 0
    for feed in feeds:
        feed_id = feed['id']
        url = feed['url']
        keywords = get_keywords_from_deepseek(url)
        logger.info(f"🔖 为 Feed ID {feed_id} 提取关键词: {keywords}")
        for kw in keywords:
            try:
                insert_keyword(feed_id, kw)
                logger.info(f"✅ 插入关键词 '{kw}' 到 feed {feed_id}")
            except Exception as e:
                logger.warning(f"❌ 插入失败（Feed ID {feed_id} / 关键词：{kw}）：{e}")

        try:
            db.execute_query(update_feed_tagged_query, (feed_id,))
            tagged_count += 1
        except Exception as e:
            logger.warning(f"⚠️ 标记 feed {feed_id} 已打标签失败：{e}")
    logger.info(f"🎉 共处理并打标签 {tagged_count} 条 feed")
    return {"result": tagged_count, "status": "Completed"}


# =======================================================================================================================

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    return redirect(url_for('index'))


@app.route('/longtask', methods=['POST'])
def longtask():
    task = tag_unprocessed_feeds.apply_async()
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}


@app.route('/tagfeeds', methods=['POST'])
def start_tagging_task():
    task = tag_unprocessed_feeds.apply_async()
    return jsonify({}), 202, {'Location': url_for('taskstatus', task_id=task.id)}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = get_feed_info.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


if __name__ == '__main__':
    # task = get_feed_info.apply_async()
    # print(task.id)  # 可用于查看状态
    task = tag_unprocessed_feeds.apply_async()
    print(task.id)  # 可用于查看状态
