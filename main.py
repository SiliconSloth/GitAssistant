import hashlib
import hmac
import requests, json, sys, subprocess

import datetime
import time
from email import utils


KEY = "dde08cd6-3e4e-4f6c-9335-4eadfe9ed699"
bot_name = "Metro-Bot"
integration_id = "1kwsdrk27z0rzu"


exit_on_complete = False

def run_command(*args):
    message = "Running"
    for arg in args:
        if " " in arg:
            message += ' "' + arg + '"'
        else:
            message += " " + arg
    print(message)
    subprocess.run(args)


def commit(message):
    run_command("metro", "commit", message)


def delete():
    run_command("metro", "delete", "commit")


def merge(branch):
    run_command("metro","absorb", branch)

def patch(message):
    if message is None:
        run_command("metro", "patch")
    else:
        run_command("metro", "patch", message)

def switch(branch):
    run_command("metro", "switch", branch)

def sync():
    run_command("git", "pull")
    run_command("git", "push")

def create(branch):
    run_command("metro", "branch", branch)
    run_command("metro", "switch", branch)


def make_digest(key, message):
    key = bytes(key, 'UTF-8')
    message = bytes(message, 'UTF-8')

    digester = hmac.new(key, message, hashlib.sha1)
    signature1 = digester.hexdigest()
    return signature1


def send(user_id, payload, create_user=False):
    nowdt = datetime.datetime.now()
    nowtuple = nowdt.timetuple()
    nowtimestamp = time.mktime(nowtuple)
    rfc_2822 = utils.formatdate(nowtimestamp)

    string_to_sign = '{}|{}|{}'.format(bot_name, integration_id, rfc_2822)
    dig = make_digest(KEY, string_to_sign)

    if create_user:
        response = requests.get(
            "https://runtime.hack.accelerator.bjss.ai/bots/Metro-Bot/integrations/http/"+integration_id+"/session_id",
            headers={"X-Request": rfc_2822, "Authorization": bot_name+' '+dig, "Content-Type": "application/json"}
        )
    else:
        response = requests.post(
            "https://runtime.hack.accelerator.bjss.ai/bots/Metro-Bot/integrations/http/"+integration_id,
            headers={"X-Request": rfc_2822, "Authorization": bot_name+' '+dig, "Content-Type": "application/json"},
            json={'userId': user_id, 'payload': payload}
        )

    if response.status_code == 200:
        content = json.loads(response.content)
        if create_user:
            return content['sessionId']
        else:
            content = content['response']
            if content:
                content = content[0]
                body = content['text']
                answer_type = content.get('__slotDetails', {}).get('entity', None)

                deliminator_index = body.find("}: ")
                data = json.loads(body[:deliminator_index+1])
                message = body[deliminator_index+3:]
                return message, data, answer_type
            else:
                return "", {}, None
    else:
        raise RuntimeError(response.content)


def exec_order(order, session_id):
    global exit_on_complete
    reply, data, answer_type = send(session_id, {"text": order})
    print(reply)
    action = data.get("type", None)

    if action == "commit":
        commit(data["message"])
    elif action == "delete":
        delete()
    elif action == "merge":
        merge(data["branch"])
    elif action == "patch":
        patch(data.get("message", None))
    elif action == "switch":
        switch(data["branch"])
    elif action == "sync":
        sync()
    elif action == "create":
        create(data["branch"])
    else:
        return

    if exit_on_complete:
        exit(0)


session_id = send("", "", True)
order = " ".join(sys.argv[1:])
if order:
    exit_on_complete = True
    exec_order(order, session_id)
else:
    ezit_on_complete = False
    print("Hello, I'm the Git assistant. What do you want to do?")

while True:
    order = input("> ")
    if order == "exit":
        print("Goodbye!")
        exit(0)
    exec_order(order, session_id)
