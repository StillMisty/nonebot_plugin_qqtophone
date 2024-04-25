from nonebot.plugin import PluginMetadata
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg
from nonebot.log import logger

import httpx

__plugin_meta__ = PluginMetadata(
    name="QQ查询",
    description="通过QQ号查询手机号",
    type="application",
    usage="查询q [QQ号|@群友]",
)

qqtophone = on_command("查询q", priority=5, block=True, aliases=set(["查询Q", "开"]))


async def query_qq(qq: str):
    if qq.isdigit() and 5 <= len(qq) <= 11:
        url = r"https://zy.xywlapi.cc/qqapi"

        try:
            async with httpx.AsyncClient() as httpx_client:
                res = await httpx_client.get(url=url, params={"qq": qq}, timeout=10)

            if res.status_code != 200:
                return f"查询失败，服务器错误，状态码{res.status_code}"

            res = res.json()
            status = res.get("status")
            if status == 200:
                return f'查询结果：\nQQ号:{res["qq"]}\n手机号:{res["phone"]}\n归属地:{res["phonediqu"]}'
            elif status == 500:
                return "查询失败，信息不存在"
            else:
                return "查询失败，未知错误"
        except Exception as e:
            logger.error(f"QQ查询失败,{e}")
            return "查询失败，请稍后再试"

    else:
        return "QQ号格式错误"


@qqtophone.handle()
async def _(args: Message = CommandArg()):
    if not args:
        await qqtophone.finish("请输入QQ号或@群友", at_sender=True)
    for seg in args:
        if seg.type == "at":
            qq = str(seg.data["qq"])
            break
        if seg.type == "text":
            qq = seg.data["text"]
            break

    await qqtophone.finish(await query_qq(qq), at_sender=True)
