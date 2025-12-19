"""
Bilibili视频信息MCP服务器的核心模块
"""

import argparse
from mcp.server.fastmcp import FastMCP
from . import bilibili_api

# 创建 FastMCP 服务器实例，命名为 BilibiliVideoInfo
mcp = FastMCP("BilibiliVideoInfo", dependencies=["requests"])

@mcp.tool(
    annotations={
        "title": "获取视频字幕",
        "readOnlyHint": True,
        "openWorldHint": False
    }
)
async def get_subtitles(url: str) -> list:
    """Get subtitles from a Bilibili video
    
    Args:
        url: Bilibili video URL, e.g., https://www.bilibili.com/video/BV1x341177NN
        
    Returns:
        List of subtitles grouped by language. Each entry contains subtitle content with timestamps.
    """
    bvid = bilibili_api.extract_bvid(url)
    if not bvid:
        return [f"错误: 无法从 URL 提取 BV 号: {url}"]
    
    aid, cid, error = bilibili_api.get_video_basic_info(bvid)
    if error:
        return [f"获取视频信息失败: {error['error']}"]
    
    subtitles, error = bilibili_api.get_subtitles(aid, cid)
    if error:
        return [f"获取字幕失败: {error['error']}"]
    
    if not subtitles:
        return ["该视频没有字幕"]
    
    return subtitles

@mcp.tool(
    annotations={
        "title": "获取视频弹幕",
        "readOnlyHint": True,
        "openWorldHint": False
    }
)
async def get_danmaku(url: str) -> list:
    """Get danmaku (bullet comments) from a Bilibili video
    
    Args:
        url: Bilibili video URL, e.g., https://www.bilibili.com/video/BV1x341177NN
        
    Returns:
        List of danmaku (bullet comments) with content, timestamp and user information
    """
    bvid = bilibili_api.extract_bvid(url)
    if not bvid:
        return [f"错误: 无法从 URL 提取 BV 号: {url}"]
    
    aid, cid, error = bilibili_api.get_video_basic_info(bvid)
    if error:
        return [f"获取视频信息失败: {error['error']}"]
    
    danmaku, error = bilibili_api.get_danmaku(cid)
    if error:
        return [f"获取弹幕失败: {error['error']}"]
    
    if not danmaku:
        return ["该视频没有弹幕"]
    
    return danmaku

@mcp.tool(
    annotations={
        "title": "获取视频评论",
        "readOnlyHint": True,
        "openWorldHint": False
    }
)
async def get_comments(url: str) -> list:
    """Get popular comments from a Bilibili video

    Args:
        url: Bilibili video URL, e.g., https://www.bilibili.com/video/BV1x341177NN

    Returns:
        List of popular comments including comment content, user information, and metadata such as like counts
    """
    bvid = bilibili_api.extract_bvid(url)
    if not bvid:
        return [f"错误: 无法从 URL 提取 BV 号: {url}"]

    aid, cid, error = bilibili_api.get_video_basic_info(bvid)
    if error:
        return [f"获取视频信息失败: {error['error']}"]

    comments, error = bilibili_api.get_comments(aid)
    if error:
        return [f"获取评论失败: {error['error']}"]

    if not comments:
        return ["该视频没有热门评论"]

    return comments


@mcp.tool(
    annotations={
        "title": "分类搜索",
        "readOnlyHint": True,
        "openWorldHint": False
    }
)
async def search(
    keyword: str,
    search_type: str = 'video',
    order: str = None,
    page: int = 1,
    duration: int = None,
    tids: int = None,
    user_type: int = None,
    order_sort: int = None,
    category_id: int = None,
    pubtime_begin_s: int = 0,
    pubtime_end_s: int = 0
) -> dict:
    """Search Bilibili by category

    Args:
        keyword: Search keyword
        search_type: Type of content to search. Options:
            - video: Videos (default)
            - media_bangumi: Anime/番剧
            - media_ft: Movies/TV shows/影视
            - live: Live rooms and streamers/直播间及主播
            - live_room: Live rooms only/直播间
            - live_user: Streamers only/主播
            - article: Articles/专栏
            - topic: Topics/话题
            - bili_user: Users/用户
            - photo: Photo albums/相簿
        order: Sort order (varies by search_type):
            - For video/article/photo: totalrank(综合), click(点击), pubdate(发布时间), dm(弹幕), stow(收藏), scores(评论)
            - For article only: attention(喜欢)
            - For live_room: online(人气), live_time(开播时间)
            - For bili_user: 0(默认), fans(粉丝), level(等级)
        page: Page number (default 1, max 50 pages)
        duration: Video duration filter (video only):
            - 0: All durations
            - 1: Under 10 minutes
            - 2: 10-30 minutes
            - 3: 30-60 minutes
            - 4: Over 60 minutes
        tids: Video category/partition ID filter (video only)
        user_type: User type filter (bili_user only):
            - 0: All users
            - 1: UP主
            - 2: Normal users
            - 3: Verified users
        order_sort: Sort direction for user search (bili_user only):
            - 0: High to low
            - 1: Low to high
        category_id: Category filter for article/photo:
            - Article: 0(全部), 2(动画), 1(游戏), 28(影视), 3(生活), 29(兴趣), 16(轻小说), 17(科技)
            - Photo: 0(全部), 1(画友), 2(摄影)
        pubtime_begin_s: Publish time range start (Unix timestamp in seconds, 0 for no limit)
        pubtime_end_s: Publish time range end (Unix timestamp in seconds, 0 for no limit)

    Returns:
        Search results with pagination info. Results format varies by search_type.
    """
    results, error = bilibili_api.search_by_type(
        keyword=keyword,
        search_type=search_type,
        order=order,
        page=page,
        duration=duration,
        tids=tids,
        user_type=user_type,
        order_sort=order_sort,
        category_id=category_id,
        pubtime_begin_s=pubtime_begin_s,
        pubtime_end_s=pubtime_end_s
    )

    if error:
        return {"error": error['error']}

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bilibili Video Info MCP Server")
    parser.add_argument('transport', nargs='?', default='stdio', choices=['stdio', 'sse', 'streamable-http'],
                        help='Transport type (stdio, sse, or streamable-http)')
    args = parser.parse_args()
    mcp.run(transport=args.transport)