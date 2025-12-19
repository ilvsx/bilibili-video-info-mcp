import re
import requests
import xml.etree.ElementTree as ET
import os
import time
import urllib.parse
from functools import reduce
from hashlib import md5
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_seesdata() -> str:
    """Get the Bilibili SESSDATA from environment variables"""
    seesdata = os.getenv("SESSDATA")
    if not seesdata:
        raise ValueError("SESSDATA environment variable is required")
    return seesdata

SESSDATA = get_seesdata()


# Bilibili API endpoints
API_GET_VIEW_INFO = "https://api.bilibili.com/x/web-interface/view"
API_GET_SUBTITLE = "https://api.bilibili.com/x/player/wbi/v2"
API_GET_DANMAKU = "https://api.bilibili.com/x/v1/dm/list.so"
API_GET_COMMENTS = "https://api.bilibili.com/x/v2/reply"
API_SEARCH_TYPE = "https://api.bilibili.com/x/web-interface/search/type"

# Valid search types
SEARCH_TYPES = {
    'video': '视频',
    'media_bangumi': '番剧',
    'media_ft': '影视',
    'live': '直播间及主播',
    'live_room': '直播间',
    'live_user': '主播',
    'article': '专栏',
    'topic': '话题',
    'bili_user': '用户',
    'photo': '相簿'
}

# Valid order options for different search types
SEARCH_ORDER_OPTIONS = {
    'video': ['totalrank', 'click', 'pubdate', 'dm', 'stow', 'scores'],
    'article': ['totalrank', 'click', 'pubdate', 'stow', 'scores', 'attention'],
    'photo': ['totalrank', 'click', 'pubdate', 'stow', 'scores'],
    'live_room': ['online', 'live_time'],
    'bili_user': ['0', 'fans', 'level']
}

# WBI signature mixin key encoding table
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]

# WBI keys cache
_wbi_keys_cache = {
    'img_key': None,
    'sub_key': None,
    'last_update': 0
}
WBI_KEYS_CACHE_TTL = 3600  # Cache TTL in seconds (1 hour)

# buvid3 cache
_buvid3_cache = {
    'buvid3': None,
    'b_nut': None,
    'last_update': 0
}
BUVID3_CACHE_TTL = 86400  # Cache TTL in seconds (24 hours)

# Default Headers for requests
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Referer': 'https://www.bilibili.com/'
}

def _get_buvid3() -> tuple:
    """Get buvid3 and b_nut cookies from bilibili.com with caching."""
    global _buvid3_cache
    current_time = time.time()

    # Check if cache is valid
    if (_buvid3_cache['buvid3'] and
            current_time - _buvid3_cache['last_update'] < BUVID3_CACHE_TTL):
        return _buvid3_cache['buvid3'], _buvid3_cache['b_nut']

    # Fetch new buvid3 from bilibili.com
    headers = DEFAULT_HEADERS.copy()
    try:
        resp = requests.get('https://www.bilibili.com/', headers=headers, timeout=10)
        buvid3 = resp.cookies.get('buvid3', '')
        b_nut = resp.cookies.get('b_nut', '')

        if buvid3:
            _buvid3_cache['buvid3'] = buvid3
            _buvid3_cache['b_nut'] = b_nut
            _buvid3_cache['last_update'] = current_time
            return buvid3, b_nut

    except requests.RequestException as e:
        print(f"Failed to get buvid3: {e}")

    # Return cached values if available
    if _buvid3_cache['buvid3']:
        return _buvid3_cache['buvid3'], _buvid3_cache['b_nut']

    return '', ''


def _get_headers(with_buvid3: bool = False):
    headers = DEFAULT_HEADERS.copy()
    cookies = []
    if SESSDATA:
        cookies.append(f'SESSDATA={SESSDATA}')
    if with_buvid3:
        buvid3, b_nut = _get_buvid3()
        if buvid3:
            cookies.append(f'buvid3={buvid3}')
        if b_nut:
            cookies.append(f'b_nut={b_nut}')
    if cookies:
        headers['Cookie'] = '; '.join(cookies)
    return headers


def _get_mixin_key(orig: str) -> str:
    """Generate mixin key from img_key + sub_key using the encoding table."""
    return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, '')[:32]


def _get_wbi_keys() -> tuple:
    """Get WBI keys (img_key, sub_key) from nav API with caching."""
    global _wbi_keys_cache
    current_time = time.time()

    # Check if cache is valid
    if (_wbi_keys_cache['img_key'] and _wbi_keys_cache['sub_key'] and
            current_time - _wbi_keys_cache['last_update'] < WBI_KEYS_CACHE_TTL):
        return _wbi_keys_cache['img_key'], _wbi_keys_cache['sub_key']

    # Fetch new keys from nav API
    headers = _get_headers()
    try:
        resp = requests.get('https://api.bilibili.com/x/web-interface/nav', headers=headers)
        resp.raise_for_status()
        json_content = resp.json()

        # wbi_img is available even when not logged in (code=-101)
        wbi_img = json_content.get('data', {}).get('wbi_img', {})
        img_url = wbi_img.get('img_url', '')
        sub_url = wbi_img.get('sub_url', '')

        # Extract keys from URLs
        img_key = img_url.rsplit('/', 1)[-1].split('.')[0] if img_url else ''
        sub_key = sub_url.rsplit('/', 1)[-1].split('.')[0] if sub_url else ''

        if img_key and sub_key:
            _wbi_keys_cache['img_key'] = img_key
            _wbi_keys_cache['sub_key'] = sub_key
            _wbi_keys_cache['last_update'] = current_time
            return img_key, sub_key

    except requests.RequestException as e:
        print(f"Failed to get WBI keys: {e}")

    # Return cached keys if available, even if expired
    if _wbi_keys_cache['img_key'] and _wbi_keys_cache['sub_key']:
        return _wbi_keys_cache['img_key'], _wbi_keys_cache['sub_key']

    return '', ''


def _enc_wbi(params: dict, img_key: str, sub_key: str) -> dict:
    """Encode parameters with WBI signature."""
    mixin_key = _get_mixin_key(img_key + sub_key)
    curr_time = round(time.time())
    params['wts'] = curr_time

    # Sort parameters by key
    params = dict(sorted(params.items()))

    # Filter special characters from values
    params = {
        k: ''.join(filter(lambda c: c not in "!'()*", str(v)))
        for k, v in params.items()
    }

    # Generate query string and calculate signature
    query = urllib.parse.urlencode(params)
    wbi_sign = md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = wbi_sign

    return params


def _sign_params_wbi(params: dict) -> dict:
    """Sign parameters with WBI signature."""
    img_key, sub_key = _get_wbi_keys()
    if not img_key or not sub_key:
        return params  # Return unsigned params if keys unavailable
    return _enc_wbi(params, img_key, sub_key)

def extract_bvid(url):
    # 先尝试直接从URL中提取BV号
    match = re.search(r'BV[a-zA-Z0-9_]+', url)
    if match:
        return match.group(0)
    
    # 如果是短链接（如b23.tv），则跟踪重定向获取完整URL
    if 'b23.tv' in url:
        try:
            response = requests.head(url, headers=_get_headers(), allow_redirects=True)
            if response.status_code == 200:
                # 获取最终重定向后的URL
                final_url = response.url
                match = re.search(r'BV[a-zA-Z0-9_]+', final_url)
                if match:
                    return match.group(0)
        except requests.RequestException as e:
            print(f"Error resolving short URL: {e}")
    
    return None

def get_video_basic_info(bvid):
    """Gets aid and cid for a given bvid."""
    headers = _get_headers()
    try:
        params_view = {'bvid': bvid}
        response_view = requests.get(API_GET_VIEW_INFO, params=params_view, headers=headers)
        response_view.raise_for_status()
        data_view = response_view.json()

        if data_view['code'] != 0:
            return None, None, {'error': 'Failed to get video info', 'details': data_view}

        video_data = data_view['data']
        return video_data.get('aid'), video_data.get('cid'), None
    except requests.RequestException as e:
        return None, None, {'error': f'Failed to fetch video details: {e}'}

def get_subtitles(aid, cid):
    """Fetches subtitles for a given aid and cid."""
    headers = _get_headers()
    subtitles = []
    try:
        params_subtitle = {'aid': aid, 'cid': cid}
        response_subtitle = requests.get(API_GET_SUBTITLE, params=params_subtitle, headers=headers)
        response_subtitle.raise_for_status()
        subtitle_data = response_subtitle.json()
        if subtitle_data.get('code') == 0 and subtitle_data.get('data', {}).get('subtitle', {}).get('subtitles'):
            for sub_meta in subtitle_data['data']['subtitle']['subtitles']:
                if sub_meta.get('subtitle_url'):
                    try:
                        subtitle_json_url = f"https:{sub_meta['subtitle_url']}"
                        response_sub_content = requests.get(subtitle_json_url, headers=headers)
                        response_sub_content.raise_for_status()
                        sub_content = response_sub_content.json()
                        subtitle_body = sub_content.get('body', [])
                        content_list = [item.get('content', '') for item in subtitle_body]
                        subtitles.append({
                            'lan': sub_meta['lan'],
                            'content': content_list
                        })
                    except requests.RequestException as e:
                        print(f"Could not fetch or parse subtitle content from {sub_meta.get('subtitle_url')}: {e}")
        return subtitles, None
    except requests.RequestException as e:
        return [], {'error': f'Could not fetch subtitles: {e}'}

def get_danmaku(cid):
    """Fetches danmaku for a given cid."""
    headers = _get_headers()
    danmaku_list = []
    try:
        params_danmaku = {'oid': cid}
        response_danmaku = requests.get(API_GET_DANMAKU, params=params_danmaku, headers=headers)
        danmaku_content = response_danmaku.content.decode('utf-8', errors='ignore')
        root = ET.fromstring(danmaku_content)
        for d in root.findall('d'):
            danmaku_list.append(d.text)
        return danmaku_list, None
    except (requests.RequestException, ET.ParseError) as e:
        return [], {'error': f'Failed to get or parse danmaku: {e}'}

def get_comments(aid):
    """Fetches comments for a given aid."""
    headers = _get_headers()
    comments_list = []
    try:
        params_comments = {'type': 1, 'oid': aid, 'sort': 2}  # sort=2 fetches hot comments
        response_comments = requests.get(API_GET_COMMENTS, params=params_comments, headers=headers)
        response_comments.raise_for_status()
        comments_data = response_comments.json()

        if comments_data.get('code') == 0 and comments_data.get('data', {}).get('replies'):
            for comment in comments_data['data']['replies']:
                if comment.get('content', {}).get('message'):
                    comments_list.append({
                        'user': comment.get('member', {}).get('uname', 'Unknown User'),
                        'content': comment['content']['message'],
                        'likes': comment.get('like', 0)
                    })
        return comments_list, None
    except requests.RequestException as e:
        return [], {'error': f'Failed to get comments: {e}'}


def search_by_type(keyword: str, search_type: str = 'video', order: str = None,
                   page: int = 1, duration: int = None, tids: int = None,
                   user_type: int = None, order_sort: int = None, category_id: int = None,
                   pubtime_begin_s: int = 0, pubtime_end_s: int = 0):
    """
    Performs a categorized search on Bilibili.

    Args:
        keyword: Search keyword
        search_type: Type of search (video, media_bangumi, media_ft, live, live_room,
                     live_user, article, topic, bili_user, photo)
        order: Sort order (varies by search_type)
        page: Page number (default 1)
        duration: Video duration filter (0: all, 1: <10min, 2: 10-30min, 3: 30-60min, 4: >60min)
        tids: Video category filter (partition tid)
        user_type: User type filter (0: all, 1: UP主, 2: normal, 3: verified)
        order_sort: User sort order (0: high to low, 1: low to high)
        category_id: Article/photo category filter
        pubtime_begin_s: Publish time range start (Unix timestamp in seconds, 0 for no limit)
        pubtime_end_s: Publish time range end (Unix timestamp in seconds, 0 for no limit)

    Returns:
        Tuple of (results_list, error_dict or None)
    """
    if search_type not in SEARCH_TYPES:
        return [], {'error': f'Invalid search_type: {search_type}. Valid types: {list(SEARCH_TYPES.keys())}'}

    headers = _get_headers(with_buvid3=True)
    params = {
        'keyword': keyword,
        'search_type': search_type,
        'page': page
    }

    if order:
        params['order'] = order
    if duration is not None and search_type == 'video':
        params['duration'] = duration
    if tids is not None and search_type == 'video':
        params['tids'] = tids
    if user_type is not None and search_type == 'bili_user':
        params['user_type'] = user_type
    if order_sort is not None and search_type == 'bili_user':
        params['order_sort'] = order_sort
    if category_id is not None and search_type in ['article', 'photo']:
        params['category_id'] = category_id
    if pubtime_begin_s:
        params['pubtime_begin_s'] = pubtime_begin_s
    if pubtime_end_s:
        params['pubtime_end_s'] = pubtime_end_s

    # Sign parameters with WBI
    signed_params = _sign_params_wbi(params)

    try:
        response = requests.get(API_SEARCH_TYPE, params=signed_params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            return [], {'error': f"API error: {data.get('message', 'Unknown error')}", 'code': data.get('code')}

        result_data = data.get('data', {})
        results = result_data.get('result', [])

        # Handle special case for 'live' search type which returns an object with live_room and live_user
        if search_type == 'live' and isinstance(results, dict):
            formatted_results = {
                'live_room': results.get('live_room', []),
                'live_user': results.get('live_user', [])
            }
            return {
                'results': formatted_results,
                'page': result_data.get('page', 1),
                'pagesize': result_data.get('pagesize', 20),
                'numResults': result_data.get('numResults', 0),
                'numPages': result_data.get('numPages', 0)
            }, None

        # Format results based on search type
        formatted_results = []
        for item in results:
            if search_type == 'video':
                formatted_results.append({
                    'bvid': item.get('bvid'),
                    'title': _strip_html_tags(item.get('title', '')),
                    'author': item.get('author'),
                    'mid': item.get('mid'),
                    'play': item.get('play'),
                    'danmaku': item.get('video_review'),
                    'favorites': item.get('favorites'),
                    'duration': item.get('duration'),
                    'pubdate': item.get('pubdate'),
                    'description': item.get('description'),
                    'pic': item.get('pic'),
                    'tag': item.get('tag')
                })
            elif search_type in ['media_bangumi', 'media_ft']:
                formatted_results.append({
                    'media_id': item.get('media_id'),
                    'season_id': item.get('season_id'),
                    'title': _strip_html_tags(item.get('title', '')),
                    'org_title': item.get('org_title'),
                    'cover': item.get('cover'),
                    'media_type': item.get('media_type'),
                    'areas': item.get('areas'),
                    'styles': item.get('styles'),
                    'cv': item.get('cv'),
                    'staff': item.get('staff'),
                    'pubtime': item.get('pubtime'),
                    'media_score': item.get('media_score')
                })
            elif search_type in ['live_room']:
                formatted_results.append({
                    'roomid': item.get('roomid'),
                    'title': _strip_html_tags(item.get('title', '')),
                    'uname': item.get('uname'),
                    'uid': item.get('uid'),
                    'online': item.get('online'),
                    'cover': item.get('cover'),
                    'user_cover': item.get('user_cover'),
                    'area_name': item.get('cate_name'),
                    'tags': item.get('tags')
                })
            elif search_type == 'live_user':
                formatted_results.append({
                    'uid': item.get('uid'),
                    'uname': item.get('uname'),
                    'uface': item.get('uface'),
                    'roomid': item.get('roomid'),
                    'live_status': item.get('live_status'),
                    'tags': item.get('tags')
                })
            elif search_type == 'article':
                formatted_results.append({
                    'id': item.get('id'),
                    'title': _strip_html_tags(item.get('title', '')),
                    'author': item.get('mid'),
                    'category_name': item.get('category_name'),
                    'view': item.get('view'),
                    'like': item.get('like'),
                    'reply': item.get('reply'),
                    'pub_time': item.get('pub_time'),
                    'desc': item.get('desc'),
                    'image_urls': item.get('image_urls')
                })
            elif search_type == 'bili_user':
                formatted_results.append({
                    'mid': item.get('mid'),
                    'uname': item.get('uname'),
                    'usign': item.get('usign'),
                    'fans': item.get('fans'),
                    'videos': item.get('videos'),
                    'level': item.get('level'),
                    'upic': item.get('upic'),
                    'official_verify': item.get('official_verify')
                })
            elif search_type == 'photo':
                formatted_results.append({
                    'id': item.get('id'),
                    'title': _strip_html_tags(item.get('title', '')),
                    'mid': item.get('mid'),
                    'uname': item.get('uname'),
                    'count': item.get('count'),
                    'like': item.get('like'),
                    'view': item.get('view')
                })
            elif search_type == 'topic':
                formatted_results.append({
                    'topic_id': item.get('topic_id'),
                    'topic_name': _strip_html_tags(item.get('topic_name', '')),
                    'update_count': item.get('update_count'),
                    'view_count': item.get('view_count'),
                    'discuss_count': item.get('discuss_count'),
                    'description': item.get('description')
                })
            else:
                formatted_results.append(item)

        return {
            'results': formatted_results,
            'page': result_data.get('page', 1),
            'pagesize': result_data.get('pagesize', 20),
            'numResults': result_data.get('numResults', 0),
            'numPages': result_data.get('numPages', 0)
        }, None

    except requests.RequestException as e:
        return [], {'error': f'Failed to perform search: {e}'}


def _strip_html_tags(text: str) -> str:
    """Remove HTML tags from text (used for highlighted search results)."""
    return re.sub(r'<[^>]+>', '', text)
