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
    logger.info(f"Fetching entries from: {feed_url}")
    for entry_index, entry in enumerate(feed.entries, start=1):
        url = entry.get('url', '') or entry.get('link', '')
        title = entry.get('title', '')
        description = entry.get('description', '') or entry.get('summary', '')
        logger.debug(f"Entry {entry_index}: {url} | {title}")
        logger.debug("*" * 50)
        data.append({
            "url": url,
            "title": title,
            "description": description,
        })
    logger.info(f"Fetched {len(data)} entries from: {feed_url}")
    return data

def get_keywords_from_jieba(text, top_k=5):
    logger.info("Extracting keywords using jieba.")
    return jieba.analyse.extract_tags(text, topK=top_k)

def get_keywords_from_deepseek(text):
    logger.info("Extracting keywords using DeepSeek API.")
    prompt = f"Please extract 3~5 relevant keywords based on the following content, return in English, separated by commas:\n\n{text}"
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
    keywords = [kw.strip() for kw in output.split(',') if kw.strip() and "由于无法直接访问链接内容" not in kw]
    logger.info(f"Extracted keywords: {keywords}")
    return keywords

def insert_feed(url, title, description):
    db = DatabaseManager(use_slave=False)
    query = """
        INSERT INTO feeds (url, title, description, last_fetched_at)
        VALUES (%s, %s, %s, %s)
    """
    params = (url, title, description, datetime.now())
    try:
        logger.info(f"Inserting feed: {title} | {url}")
        feed_id = db.execute_query(query, params, return_lastrowid=True)
        logger.info(f"Inserted feed with ID: {feed_id}")
        return feed_id
    except Exception as e:
        logger.exception(e)
        return None

def insert_keyword(feed_id, keyword):
    db = DatabaseManager(use_slave=False)
    query = """
        INSERT INTO keyword (feed_id, keyword, created_at, updated_at)
        VALUES (%s, %s, %s, %s)
    """
    params = (feed_id, keyword, datetime.now(), datetime.now())
    try:
        logger.info(f"Inserting keyword '{keyword}' for feed ID: {feed_id}")
        db.execute_query(query, params)
        logger.info(f"Inserted keyword '{keyword}' successfully.")
    except Exception as e:
        logger.exception(e)
        return False
    return True
