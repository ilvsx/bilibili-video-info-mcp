# Bilibili 视频信息 MCP 服务器

[![English](https://img.shields.io/badge/language-English-blue.svg)](./README.md) [![中文](https://img.shields.io/badge/language-中文-red.svg)](./README.zh.md)

Bilibili MCP Server，可以根据视频 URL 获取视频的字幕、弹幕、评论信息，以及搜索视频。

## 功能特性

- **获取字幕**：支持语言选择，支持 AI 生成字幕
- **获取弹幕**：获取视频弹幕列表
- **获取评论**：获取视频热门评论
- **搜索功能**：搜索视频、用户、直播间、专栏等，支持时间范围筛选

## 使用方法

MCP Server 支持三种通信方式：

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
                "SESSDATA": "你的 SESSDATA"
            }
        }
    }
}
```

### 2. sse（服务器发送事件）

在 sse 模式下运行：
```bash
cp .env.example .env
# 编辑 .env 文件，设置你的 SESSDATA
uvx bilibili-video-info-mcp sse
```

然后配置你的 MCP 客户端：
```json
{
    "mcpServers": {
        "bilibili-video-info-mcp": {
            "url": "http://localhost:8000/sse"
        }
    }
}
```

### 3. streamable-http（HTTP 流式传输）

在 streamable-http 模式下运行：
```bash
cp .env.example .env
# 编辑 .env 文件，设置你的 SESSDATA
uvx bilibili-video-info-mcp streamable-http
```

然后配置你的 MCP 客户端：
```json
{
    "mcpServers": {
        "bilibili-video-info-mcp": {
            "url": "http://localhost:8000/mcp"
        }
    }
}
```

## MCP 工具列表

### 1. 获取视频字幕

获取视频字幕，支持语言选择和 AI 生成字幕。

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

参数说明：
- `url`（必填）：Bilibili 视频链接
- `lang`（可选）：语言代码（zh, ai-zh, en, ai-en, ja, ai-ja）。默认按优先级选择：zh > ai-zh > en > ai-en > ja > ai-ja
- `all_languages`（可选）：设为 true 获取所有可用语言的字幕

### 2. 获取视频弹幕

```json
{
  "name": "get_danmaku",
  "arguments": {
    "url": "https://www.bilibili.com/video/BV1x341177NN"
  }
}
```

### 3. 获取视频评论

```json
{
  "name": "get_comments",
  "arguments": {
    "url": "https://www.bilibili.com/video/BV1x341177NN"
  }
}
```

### 4. 搜索 Bilibili

搜索视频、用户、直播间、专栏等内容。

```json
{
  "name": "search",
  "arguments": {
    "keyword": "Python 教程",
    "search_type": "video",
    "order": "click",
    "recent_days": 7,
    "page": 1
  }
}
```

参数说明：
- `keyword`（必填）：搜索关键词
- `search_type`（可选）：搜索类型
  - `video`（默认）、`media_bangumi`（番剧）、`media_ft`（影视）、`live`（直播间及主播）、`live_room`（直播间）、`live_user`（主播）、`article`（专栏）、`topic`（话题）、`bili_user`（用户）、`photo`（相簿）
- `order`（可选）：排序方式（默认：click 按点击量）
  - 视频：`click`（点击量）、`totalrank`（综合排序）、`pubdate`（发布时间）、`dm`（弹幕数）、`stow`（收藏数）、`scores`（评论数）
- `recent_days`（可选）：筛选最近 N 天内的内容
- `recent_weeks`（可选）：筛选最近 N 周内的内容
- `page`（可选）：页码（1-50，每页 20 条结果）
- `duration`（可选）：视频时长筛选（0-4）
- `tids`（可选）：视频分区 ID

## 常见问题

### 1. 如何获取 SESSDATA？

1. 登录 Bilibili 网站
2. 打开浏览器开发者工具（F12）
3. 进入 Application/存储 -> Cookies -> bilibili.com
4. 找到 SESSDATA 对应的值

### 2. 报错 "SESSDATA environment variable is required"

确保已经设置了环境变量：

```bash
export SESSDATA="你的 SESSDATA 值"
```

或者创建 `.env` 文件：
```
SESSDATA=你的SESSDATA值
```

### 3. 视频链接支持哪些格式？

支持标准的 Bilibili 视频链接，例如：
- https://www.bilibili.com/video/BV1x341177NN
- https://b23.tv/xxxxx（短链接）
- 包含 BV 号的任何链接

### 4. AI 字幕无法获取？

部分账号可能无法获取 AI 生成字幕，具体原因未知。如果无法获取 AI 字幕，请尝试使用其他账号的 SESSDATA。

## 许可证

MIT
