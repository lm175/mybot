import time
import json

from fake_useragent import UserAgent

from . import qianwen


def cli():
    cookies_file_content = []
    sessionId = ""
    with open("cookies.json", encoding="utf-8") as f:
        cookies_file_content = json.load(f)

    cookies_dict = {}
    for it in cookies_file_content:
        cookies_dict[it['name']] = it['value']

    question = input("You > ")

    session = qianwen.Chatbot(
        cookies=cookies_dict
    )

    lastId = "0"
    while True:

        reply_iter = session.ask(
            prompt=question,
            parentId=lastId,
            sessionId=sessionId,
            stream=True
        )

        last_out = ""

        print("AI  > ", end="")

        for resp in reply_iter:
            lastId = resp.msgId
            if resp.contents:
                resp_text = resp.contents[-1].content
                print(resp_text.replace(last_out, ""), end="", flush=True)
                time.sleep(0.1)
                last_out = resp_text
                sessionId = resp.sessionId
        
        question = input("\nYou > ")


if __name__ == "__main__":
    cli()
