import asyncio
import time
import json
import os
import httpx
from bilibili_api import Credential, comment, user

# 导入配置
from config import (
    SESSDATA, BILI_JCT, BUVID3, OWNER_UIDS,
    AI_BASE_URL, AI_MODEL, AI_API_KEY,
    POLL_INTERVAL, REPLY_INTERVAL
)

# 已处理的评论ID持久化文件
PROCESSED_FILE = "processed_ids.json"

# 已处理的评论ID集合，防止重复回复
processed_rps = set()

# 上次回复时间，用于控制回复频率
last_reply_time = 0


def load_processed_ids():
    """从文件加载已处理的ID"""
    global processed_rps
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                processed_rps = set(data)
                print(f"已加载 {len(processed_rps)} 个已处理的ID")
        except Exception as e:
            print(f"加载已处理ID失败: {e}")
            processed_rps = set()


def save_processed_ids():
    """保存已处理的ID到文件"""
    try:
        with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
            json.dump(list(processed_rps), f)
    except Exception as e:
        print(f"保存已处理ID失败: {e}")


async def get_ai_reply(user_message: str, video_title: str = "") -> str:
    """调用AI接口生成回复内容"""
    prompt = f"""你是一个B站用户的自动回复助手。有人在评论区@了主人，请帮主人回复。

规则：
1. 回复要简短友好，像真人一样自然
2. 不要太长，B站评论有字数限制（约100字以内）
3. 语气可以轻松幽默一点
4. 如果对方问了问题，尽量给出有帮助的回答
5. 只输出回复内容，不要输出思考过程或任何其他内容
6. 不要输出"首先"、"然后"、"最后"等思考过程词汇

视频标题：{video_title}
对方的评论内容：{user_message}

请直接给出回复内容（只需要回复内容，不要任何其他文字）："""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{AI_BASE_URL}/v1/messages",
                headers={
                    "x-api-key": AI_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": AI_MODEL,
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            print(f"  [调试] 状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # 解析Anthropic格式: content[0].text
                content = data.get("content", [])
                stop_reason = data.get("stop_reason", "")

                # 提取text类型的内容
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "").strip()
                        if text:
                            return text

                # 如果没有text内容（只有thinking），返回默认回复
                print(f"  [调试] 没有text内容，stop_reason={stop_reason}")
                print(f"  [调试] 返回内容: {content}")
                return "收到啦～"

            print(f"  [调试] 错误响应: {response.text}")
            return "收到啦～"

    except Exception as e:
        print(f"调用AI失败: {e}")
        import traceback
        traceback.print_exc()
        return "收到啦～"


async def check_at_notifications(credential: Credential) -> list:
    """检查@通知，返回新的@消息列表"""
    global processed_rps
    at_messages = []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # 调用B站通知接口获取@消息
            resp = await client.get(
                "https://api.bilibili.com/x/msgfeed/at",
                params={"platform": "web", "build": 0, "mobi_app": "web"},
                cookies={
                    "SESSDATA": SESSDATA,
                    "bili_jct": BILI_JCT,
                    "buvid3": BUVID3
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.bilibili.com"
                }
            )

            if resp.status_code != 200:
                print(f"[错误] 获取通知失败: HTTP {resp.status_code}")
                return []

            data = resp.json()
            if data.get("code") != 0:
                print(f"[错误] 获取通知失败: {data.get('message', '未知错误')}")
                return []

            items = data.get("data", {}).get("items", [])

            # 统计已处理的消息数量
            skipped_count = 0
            new_count = 0

            # 调试：打印第一条通知的完整结构
            if items and len(items) > 0:
                print(f"[调试] 第一条通知结构: {json.dumps(items[0], ensure_ascii=False, indent=2)}")

            for item in items:
                # 获取通知ID（用于去重）
                rpid = item.get("rpid", 0)
                if rpid == 0:
                    rpid = item.get("id", 0)
                if rpid == 0:
                    continue

                # 检查是否已处理
                if rpid in processed_rps:
                    skipped_count += 1
                    continue

                # 提取消息信息
                user_info = item.get("user", {})
                sender_uid = user_info.get("mid", 0)
                sender_name = user_info.get("nickname", "未知用户")
                content = item.get("item", {}).get("source_content", "")
                title = item.get("item", {}).get("title", "")
                oid = item.get("item", {}).get("subject_id", 0)
                root_id = item.get("item", {}).get("root_id", 0)
                target_id = item.get("item", {}).get("target_id", 0)
                # 获取真正的评论ID（用于回复）
                comment_id = item.get("item", {}).get("source_id", 0)

                new_count += 1
                print(f"\n[新消息] {sender_name}: {content}")
                print(f"[调试] rpid={rpid}, oid={oid}, comment_id={comment_id}")

                at_messages.append({
                    "rpid": rpid,
                    "sender_uid": sender_uid,
                    "sender_name": sender_name,
                    "content": content,
                    "title": title,
                    "oid": oid,
                    "root_id": root_id,
                    "target_id": target_id,
                    "comment_id": comment_id
                })

    except Exception as e:
        print(f"[错误] 检查通知时出错: {e}")
        import traceback
        traceback.print_exc()

    # 只在有新消息或跳过消息时显示统计
    if new_count > 0 or skipped_count > 0:
        print(f"[统计] 新消息: {new_count} 条, 已跳过: {skipped_count} 条")

    return at_messages


async def send_reply(credential: Credential, oid: int, comment_id: int, text: str):
    """发送评论回复"""
    global last_reply_time
    now = time.time()

    # 频率控制：距离上次回复至少间隔REPLY_INTERVAL秒
    wait_time = REPLY_INTERVAL - (now - last_reply_time)
    if wait_time > 0:
        print(f"等待 {wait_time:.0f} 秒后发送回复（避免风控）...")
        await asyncio.sleep(wait_time)

    try:
        print(f"[调试] 回复参数: oid={oid}, comment_id={comment_id}")

        # 回复这条评论（楼中楼）
        # 使用 comment_id 作为 parent，这样就是回复这条评论
        print(f"[调试] 回复模式: 楼中楼回复 (parent={comment_id})")
        await comment.send_comment(
            text=text,
            oid=oid,
            type_=comment.CommentResourceType.VIDEO,
            root=comment_id,
            parent=comment_id,
            credential=credential
        )

        last_reply_time = time.time()
        print(f"回复发送成功！")

    except Exception as e:
        print(f"发送回复失败: {e}")


async def main_loop():
    """主循环：轮询通知并自动回复"""
    global processed_rps

    # 启动时加载已处理的ID
    load_processed_ids()

    # 检查配置
    if not SESSDATA or not BILI_JCT or not BUVID3:
        print("错误：请先在 config.py 中填入B站Cookie信息！")
        print("获取方法：")
        print("1. 用浏览器登录 bilibili.com")
        print("2. 按F12打开开发者工具")
        print("3. 切到 Application -> Cookies")
        print("4. 复制 SESSDATA、bili_jct、buvid3 三个值")
        return

    if not OWNER_UIDS:
        print("错误：请先在 config.py 中填入主人UID列表！")
        return

    # 创建B站凭证
    credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)

    print("=" * 50)
    print("B站自动回复Bot已启动！")
    print(f"主人UID列表: {OWNER_UIDS}")
    print(f"轮询间隔: {POLL_INTERVAL}秒")
    print(f"回复间隔: {REPLY_INTERVAL}秒")
    print(f"AI模型: {AI_MODEL}")
    print("=" * 50)
    print("等待新@消息中... (按 Ctrl+C 停止)")
    print("提示: 用小号@大号来测试")

    while True:
        try:
            # 检查@通知
            at_messages = await check_at_notifications(credential)

            for msg in at_messages:
                rpid = msg["rpid"]
                sender_uid = msg["sender_uid"]
                sender_name = msg["sender_name"]
                content = msg["content"]
                title = msg["title"]
                oid = msg["oid"]
                comment_id = msg["comment_id"]

                # 标记为已处理
                processed_rps.add(rpid)
                save_processed_ids()

                # 检查是否是主人发的
                if sender_uid not in OWNER_UIDS:
                    print(f"[跳过] 非主人消息 - {sender_name}: {content}")
                    continue

                print(f"\n[收到@] {sender_name}: {content}")
                print(f"  视频: {title}")

                # 调用AI生成回复
                print("  正在生成AI回复...")
                ai_reply = await get_ai_reply(content, title)
                print(f"  AI回复: {ai_reply}")

                # 发送回复
                print("  正在发送回复...")
                await send_reply(credential, oid, comment_id, ai_reply)

        except Exception as e:
            print(f"[错误] 主循环出错: {e}")
            import traceback
            traceback.print_exc()

        # 等待下次轮询
        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    import sys

    # 如果传入 --clear 参数，清空已处理的ID
    if "--clear" in sys.argv:
        processed_rps = set()
        save_processed_ids()
        print("已清空所有已处理的ID")
        sys.exit(0)

    asyncio.run(main_loop())
