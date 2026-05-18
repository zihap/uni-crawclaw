import os

import httpx

from utils.logger import log_info, log_error


WECHAT_API_URL = "https://api.weixin.qq.com/sns/jscode2session"


async def exchange_code_for_openid(code: str) -> dict:
    """通过微信登录code换取openid"""
    appid = os.environ.get("WECHAT_APPID", "")
    secret = os.environ.get("WECHAT_APPSECRET", "")

    if not appid or not secret:
        log_error("微信配置缺失: WECHAT_APPID 或 WECHAT_APPSECRET 未设置")
        raise ValueError("服务器配置错误")

    params = {
        "appid": appid,
        "secret": secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(WECHAT_API_URL, params=params, timeout=10.0)
            data = response.json()
    except httpx.RequestError as e:
        log_error(f"请求微信API网络异常: {e}")
        raise ValueError("网络请求失败")

    errcode = data.get("errcode")
    if errcode:
        errmsg = data.get("errmsg", "未知错误")
        error_map = {
            40029: "code无效",
            45011: "接口调用频率超限",
            -1: "微信系统繁忙",
        }
        user_msg = error_map.get(errcode, f"微信登录失败: {errmsg}")
        log_error(f"微信API返回错误: errcode={errcode}, errmsg={errmsg}")
        raise ValueError(user_msg)

    openid = data.get("openid")
    if not openid:
        log_error("微信API返回数据缺少openid字段")
        raise ValueError("登录数据异常")

    session_key = data.get("session_key", "")
    unionid = data.get("unionid", "")

    log_info(f"微信登录成功: openid={openid[:6]}***")

    result = {"openid": openid}
    if unionid:
        result["unionid"] = unionid

    return result
