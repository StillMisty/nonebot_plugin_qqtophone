import ssl
from asyncio import gather, sleep

import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="QQ查询",
    description="通过QQ号查询手机号",
    type="application",
    usage="开 [QQ号|@群友]",
    homepage="https://github.com/StillMisty/nonebot_plugin_qqtophone",
)

# 忽略ssl证书
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
ssl_context.set_ciphers("DEFAULT@SECLEVEL=2")


async def is_at_qq(args: Message = CommandArg()) -> bool:
    for seg in args:
        if seg.type == "at":
            return True
        if seg.type == "text":
            texts: str = seg.data["text"].strip()
            for text in texts.split():
                if text.isdigit() and 6 <= len(text) <= 12:
                    return True
    return False


qqtophone = on_command("开", priority=5, block=True, rule=is_at_qq)


async def query_qq(qq: str) -> str:
    try:
        url = "https://api.xywlapi.cc/qqapi"
        async with httpx.AsyncClient(timeout=10, verify=ssl_context) as client:
            res = await client.get(url, params={"qq": qq})
            res.raise_for_status()
            data = res.json()
            if data.get("status") == 200:
                return f"查询结果：\nQQ号：{data['qq']}\n手机号：{data['phone']}\n属地：{data['phonediqu']}"

            elif data.get("status") == 500:
                return "查询失败：信息不存在"
            else:
                logger.error(f"未知错误，返回信息：{data}")
                return "查询失败：未知错误"
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        return f"查询失败：服务器错误，状态码{e.response.status_code}"
    except httpx.TimeoutException:
        return "查询失败：请求超时"
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        return "查询失败：请稍后再试"
    except Exception:
        logger.exception("An unexpected error occurred")
        return "查询失败：发生未知错误"


@qqtophone.handle()
async def _(bot: Bot, args: Message = CommandArg()):
    qqs = set()
    for seg in args:
        if seg.type == "at":
            qqs.add(str(seg.data["qq"]))

        elif seg.type == "text":
            texts: str = seg.data["text"].strip()
            for text in texts.split():
                if text.isdigit() and 6 <= len(text) <= 12:
                    qqs.add(text)

    if not qqs:
        await qqtophone.finish("未提供有效的QQ号", at_sender=True)
        return

    tasks = [get_info(bot, qq) for qq in qqs]
    results = await gather(*tasks)
    msg_id = (await qqtophone.send("\n\n".join(results)))["message_id"]
    await sleep(20)
    try:
        await bot.delete_msg(message_id=msg_id)
    except Exception as e:
        logger.exception(f"删除消息失败: {e}")


async def get_info(bot: Bot, qq: str) -> tuple[str, bool]:
    msg = await query_qq(qq)
    nickname = (await bot.get_stranger_info(user_id=qq))["nickname"]
    return f"{nickname}，{msg}"
