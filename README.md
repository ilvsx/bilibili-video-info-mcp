# MCP Server for Bilibili Video Info

[![smithery badge](https://smithery.ai/badge/@lesir831/bilibili-video-info-mcp)](https://smithery.ai/server/@lesir831/bilibili-video-info-mcp)
[![English](https://img.shields.io/badge/language-English-blue.svg)](./README.md) [![中文](https://img.shields.io/badge/language-中文-red.svg)](./README.zh.md)

A Bilibili MCP Server that can retrieve subtitles, danmaku (bullet comments), comments, and search videos using the video URL.

## Features

- **Get Subtitles**: Fetch video subtitles with language selection (supports AI-generated subtitles)
- **Get Danmaku**: Retrieve bullet comments from videos
- **Get Comments**: Fetch popular comments from videos
- **Search**: Search Bilibili for videos, users, live rooms, articles, and more with time filtering

## Usage

This MCP server supports three transport methods:

### 1. stdio

```json
{
    "mcpServers": {
        "bilibili-video-info-mcp": {
            "command": "uvx",
            "args": [
                "bilibili-video-info-mcp"
            ],
            "env": {
                "SESSDATA": "your valid sessdata"
            }
        }
    }
}
```

### 2. sse (Server-Sent Events)

Run bilibili-video-info-mcp in sse mode:
```bash
cp .env.example .env
# Edit .env and set your SESSDATA
uvx bilibili-video-info-mcp sse
```

Then config your MCP client:
```json
{
    "mcpServers": {
        "bilibili-video-info-mcp": {
            "url": "http://localhost:8000/sse"
        }
    }
}
```

### 3. streamable-http (HTTP Streaming)

Run bilibili-video-info-mcp in streamable-http mode:
```bash
cp .env.example .env
# Edit .env and set your SESSDATA
uvx bilibili-video-info-mcp streamable-http
```

Then config your MCP client:
```json
{
    "mcpServers": {
        "bilibili-video-info-mcp": {
            "url": "http://localhost:8000/mcp"
        }
    }
}
```

## MCP Tools List

### 1. Get Video Subtitles

Fetch subtitles from a video. Supports language selection and AI-generated subtitles.

```json
{
  "name": "get_subtitles",
  "arguments": {
    "url": "https://www.bilibili.com/video/BV1x341177NN",
    "lang": "ai-zh",
    "all_languages": false
  }
}
```

Parameters:
- `url` (required): Bilibili video URL
- `lang` (optional): Language code (zh, ai-zh, en, ai-en, ja, ai-ja). Default uses priority: zh > ai-zh > en > ai-en > ja > ai-ja
- `all_languages` (optional): Set to true to fetch all available languages

### 2. Get Video Danmaku (Bullet Comments)

```json
{
  "name": "get_danmaku",
  "arguments": {
    "url": "https://www.bilibili.com/video/BV1x341177NN"
  }
}
```

### 3. Get Video Comments

```json
{
  "name": "get_comments",
  "arguments": {
    "url": "https://www.bilibili.com/video/BV1x341177NN"
  }
}
```

### 4. Search Bilibili

Search for videos, users, live rooms, articles, and more.

```json
{
  "name": "search",
  "arguments": {
    "keyword": "Python tutorial",
    "search_type": "video",
    "order": "click",
    "recent_days": 7,
    "page": 1
  }
}
```

Parameters:
- `keyword` (required): Search keyword
- `search_type` (optional): Type of content to search
  - `video` (default), `media_bangumi`, `media_ft`, `live`, `live_room`, `live_user`, `article`, `topic`, `bili_user`, `photo`
- `order` (optional): Sort order (default: click)
  - For video: `click`, `totalrank`, `pubdate`, `dm`, `stow`, `scores`
- `recent_days` (optional): Filter content from last N days
- `recent_weeks` (optional): Filter content from last N weeks
- `page` (optional): Page number (1-50, 20 results per page)
- `duration` (optional): Video duration filter (0-4)
- `tids` (optional): Video category ID

## FAQ

### 1. How to find SESSDATA?

1. Log in to the Bilibili website
2. Open browser developer tools (F12)
3. Go to Application/Storage -> Cookies -> bilibili.com
4. Find the value corresponding to SESSDATA

### 2. Error "SESSDATA environment variable is required"

Make sure you have set the environment variable:

```bash
export SESSDATA="your SESSDATA value"
```

Or create a `.env` file:
```
SESSDATA=your_sessdata_value
```

### 3. What video link formats are supported?

Standard Bilibili video links are supported, such as:
- https://www.bilibili.com/video/BV1x341177NN
- https://b23.tv/xxxxx (short links)
- Any link containing a BV number

### 4. AI subtitles not showing?

Some accounts may not have access to AI-generated subtitles. The exact requirements are unclear, but if AI subtitles are not available, try using a different account's SESSDATA.

## License

MIT
