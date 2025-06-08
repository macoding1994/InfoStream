from datetime import datetime

import feedparser
import jieba.analyse
import requests
from config import API_KEY
from loguru import logger

from db_manager import DatabaseManager


def get_feed_entry(feed_url):
    data = []
    feed = feedparser.parse(feed_url)
    for entry_index, entry in enumerate(feed.entries, start=1):
        url = entry.get('url', '') or entry.get('link', '')
        title = entry.get('title', '')
        description = entry.get('description', '') or entry.get('summary', '')
        logger.debug(url)
        logger.debug(title)
        # logger.debug(description)
        logger.debug("*" * 50)
        data.append({
            "url": url,
            "title": title,
            "description": description,
        })
    return data


def get_keywords_from_jieba(text, top_k=5):
    return jieba.analyse.extract_tags(text, topK=top_k)


def get_keywords_from_deepseek(text):
    prompt = f"请根据以下内容提取3~5个相关关键词，英文返回，用逗号分隔：\n\n{text}"
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers)
    result = response.json()
    output = result['choices'][0]['message']['content']
    return [kw.strip() for kw in output.split(',') if kw.strip()]


def insert_feed(url, title, description):
    db = DatabaseManager()
    query = """
        INSERT INTO feeds (url, title, description, last_fetched_at)
        VALUES (%s, %s, %s, %s)
    """
    params = (url, title, description, datetime.now())
    try:
        logger.info(f"{query} \n{params}")
        feed_id = db.execute_query(query, params, return_last_id=True)
        return feed_id
    except Exception as e:
        logger.exception(e)
        return None



def insert_keyword(feed_id, keyword):
    db = DatabaseManager()
    query = """
            INSERT INTO keyword (feed_id, keyword, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
        """
    params = (feed_id, keyword, datetime.now(), datetime.now())
    try:
        logger.info(f"{query} \n{params}")
        db.execute_query(query, params)
    except Exception as e:
        logger.exception(e)
        return False
    return True


if __name__ == '__main__':
    feed_url = "feed://eugene-wei.squarespace.com/blog?format=rss"
    FEED_DICT = {
        # "feed://eugene-wei.squarespace.com/blog?format=rss": "technology/blog",
        # "https://ciechanow.ski/atom.xml": "technology",
        # "https://tatianamac.com/feed/feed.xml": "technology",
        "https://interfacelovers.com/feed": "design ",
    }
    for k,v in FEED_DICT.items():
        print(len(get_feed_entry(feed_url)))

    # print(get_keywords_from_deepseek("https://www.eugenewei.com/blog/2023/7/6/how-to-blow-up-a-timeline"))
