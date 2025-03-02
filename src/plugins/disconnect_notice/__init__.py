from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="Bot掉线通知",
    description="Bot掉线通知",
    usage="Bot协议端掉线时发送邮件通知"
)


from .config import config
# 配置信息
mail_host = config.notice_mail_host  # QQ邮箱的SMTP服务器
mail_user = config.notice_mail_user  # QQ邮箱地址
mail_pass = config.notice_mail_pass  # QQ邮箱授权码


import smtplib, os
from email.mime.text import MIMEText
from email.utils import formataddr

from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Bot
from nonebot import on_command


async def send_mail(
        sender_name: str = "",
        receiver_name: str = "",
        content: str = "",
        subject: str = ""
) -> None:
    try:
        # 邮件内容
        message = MIMEText(content, "plain", "utf-8")
        message['From'] = formataddr((sender_name, mail_user))  # 发件人信息
        message['To'] = formataddr((receiver_name, mail_user))  # 收件人信息
        message['Subject'] = subject  # 邮件主题
        
        smtpObj = smtplib.SMTP_SSL(mail_host, 465)  # 使用SSL加密连接
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(mail_user, mail_user, message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException as e:
        print(f"邮件发送失败: {e}")
    finally:
        smtpObj.quit()



driver = get_driver()


@driver.on_bot_disconnect
async def _(bot: Bot):
    print("bot断开连接，尝试发送邮件通知")
    await send_mail(
        content=f"Bot: {bot.self_id}断开连接",
        subject="Bot掉线通知"
    )
    os.system(f"napcat start {bot.self_id}")

@driver.on_bot_connect
async def _(bot: Bot):
    print("bot已连接，尝试发送邮件通知")
    await send_mail(
        content=f"Bot: {bot.self_id}已连接",
        subject="Bot上线通知"
    )



disconnect_test = on_command("掉线测试", block=True)

@disconnect_test.handle()
async def _():
    await send_mail(
        content="这是一条测试信息，你的bot没有真正掉线",
        subject="nonebot掉线通知测试"
    )