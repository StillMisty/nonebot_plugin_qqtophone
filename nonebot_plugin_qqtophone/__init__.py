from nonebot.plugin import PluginMetadata
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, Bot, MessageEvent
from nonebot.params import CommandArg
from nonebot.log import logger

import httpx
from asyncio import sleep

__plugin_meta__ = PluginMetadata(
    name="QQ查询",
    description="通过QQ号查询手机号",
    type="application",
    usage="开 [QQ号|@群友]",
    homepage="https://github.com/StillMisty/nonebot_plugin_qqtophone",
)

qqtophone = on_command("开", priority=5, block=True)


async def query_qq(qq: str) -> tuple[str, bool]:
    if not 5 <= len(qq) <= 11 or not qq.isdigit():
        return "QQ号格式错误", False
    try:
        url = r"https://api.xywlapi.cc/qqapi"
        async with httpx.AsyncClient() as httpx_client:
            res = await httpx_client.get(url=url, params={"qq": qq}, timeout=10)
    except TimeoutError:
        return "查询失败，请稍后再试", False

    if res.status_code != 200:
        return f"查询失败，服务器错误，状态码{res.status_code}", False

    res = res.json()
    status = res.get("status")
    if status == 200:
        return (
            f'查询结果：\nQQ号:{res["qq"]}\n手机号:{res["phone"]}\n属地:{res["phonediqu"]}',
            True,
        )
    elif status == 500:
        return "查询失败，信息不存在", False
    else:
        logger.error(f"查询失败，未知错误，返回信息：{res}")
        return "查询失败，未知错误", False


@qqtophone.handle()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    qq = None
    for seg in args:
        if seg.type == "at":
            qq = str(seg.data["qq"])
            break
        elif seg.type == "text" and seg.data["text"].strip().isdigit():
            qq = seg.data["text"].strip()
            break

    if not qq:
        await qqtophone.finish("请输入QQ号或@群友", at_sender=True)

    msg, success = await query_qq(qq)
    msg_id = (await bot.send(event, msg, at_sender=True))["message_id"]
    if success:
        await sleep(20)
        await bot.delete_msg(message_id=msg_id)
