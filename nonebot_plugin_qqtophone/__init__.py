from nonebot.plugin import PluginMetadata
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, Event, Message
from nonebot.params import CommandArg

import httpx

__plugin_meta__ = PluginMetadata(
    name="QQ查询",
    description="通过QQ号查询手机号",
    type="application",
    usage="查询qq [QQ号|@群友]",
)

qqtophone = on_command("查询qq",priority=5,block=True,aliases=set(["查询QQ","查询qq号","查询QQ号","查询q","查询Q"]))

async def query_qq(qq:str):
    if qq.isdigit() and 5 <= len(qq) <= 11:
        
        url = r"https://zy.xywlapi.cc/qqapi"

        async with httpx.AsyncClient() as httpx_client:
            try:
                res = await httpx_client.get(url=url,params={"qq":qq},timeout=10)
            except TimeoutError:
                return "查询失败，请求超时"
        
        if res.status_code != 200:
            return "查询失败，服务器错误"
                
        res = res.json()
        status = res.get("status")
        if status == 200:
            return f'查询结果：\nQQ号：{res["qq"]}\n手机号：{res["phone"]}\n归属地：{res["phonediqu"]}'
        elif status == 500:
            return "查询失败，信息不存在"
        else:
            return "查询失败，未知错误"
            
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
    
    