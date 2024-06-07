USERNAME = "Your username"
PASSWORD = "Your password"
PROJECTID = "Your project ID"

#Pasted from https://github.com/PolyPenguinDev/GPTSimple
import requests
import json
base_urls = {'deepinfra':"https://api.deepinfra.com/v1/openai/chat/completions", "openai":"https://api.openai.com/v1/chat/completions"}
def print_token(token):
    if token.token == None:
        print()
    else:
        print(token.token, end="", flush=True)
def get_direct_output(history, model, api_key, stream = False, base_url="openai"):
    if base_url in base_urls:
        url = base_urls[base_url]
    else:
        url = base_url
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": model,
        "stream":stream,
        "messages": history
    }

    response = requests.post(url, json=data, headers=headers, stream=stream)
    if stream:
        return response
    return response.json()
class conversation:
    class token:
        def __init__(self, line):
            if line['choices'][0]['finish_reason'] == "stop":
                self.token = None
                self.model = line["model"]
                self.message = {'role':'assistant','content':None}
                self.response = line
            else:
                self.token = line["choices"][0]['delta']['content']
                self.model = line["model"]
                self.message = line["choices"][0]['delta']
                self.response = line
    def streamingResponse(self, lines, invis):
        message = ""
        iters = lines.iter_lines(decode_unicode=True)
        for line in iters:
            if 'data: ' not in line:
                continue
            line_js = json.loads(line.split('data: ')[1])
            if line_js['choices'][0]['finish_reason'] == "stop":
                if not invis:
                    self.history.append({'role':'assistant', 'content':message})
                yield self.token(line_js)
                break
            token = self.token(line_js)
            message += token.token
            yield token
    class response:
        def __init__(self, json):
            self.response = json
            self.model = json['model']
            self.id = json['id']
            self.choices = json['choices']
            self.text = json['choices'][0]['message']['content']
            self.message = json['choices'][0]['message']
            self.usage = json['usage']
            self.prompt_tokens = json['usage']['prompt_tokens']
            self.output_tokens = json['usage']['completion_tokens']
            self.total_tokens = json['usage']['total_tokens']
    def __init__(self, api_key='', model='gpt-3.5-turbo', history=None, system_prompt="You are a helpful assistant", base_url="openai"):
        if base_url.lower() == "deepinfra" and model == "gpt-3.5-turbo":
            model = "meta-llama/Llama-2-70b-chat-hf"
        self.base_url = base_url.lower()
        self.api_key = api_key
        self.model = model
        self.history = [{'role':'system',"content":system_prompt}]
        if history is not None:
            self.history = history
    def generate(self, invisible=False, stream=False):
        if stream:
            res = self.streamingResponse(get_direct_output(self.history, self.model, self.api_key, stream=True, base_url=self.base_url), invisible)
        else:
            res = self.response(get_direct_output(self.history, self.model, self.api_key, base_url=self.base_url))
            if not invisible:
                self.history.append(res.message)
        return res
    def ask(self, message, invisible=False, stream=False):

        if invisible:
            out = self.history.copy()
            out.append({"role":"user", "content":message})
        else:
            self.history.append({"role":"user", "content":message})
            out = self.history
        if stream:
            res = self.streamingResponse(get_direct_output(out, self.model, self.api_key, stream=True, base_url=self.base_url), invisible)
        else:
            res = self.response(get_direct_output(out, self.model, self.api_key, base_url=self.base_url))
            if not invisible:
                self.history.append(res.message)
        return res


#Scratch interface
import scratchattach as scratch3
from scratchattach import Encoding
import threading
import time
import random
sessions = []
chats = {}
def makesession():
    s = random.randrange(11111, 99999)
    if s in sessions:
        return makesession()
    else:
        return s
# Login and connect
session = scratch3.login(USERNAME, PASSWORD)
conn = session.connect_cloud(PROJECTID)

def get_channel(c):
    return scratch3.get_var(PROJECTID, "channel " + str(c))

def set_channel(c, v):
    if v!= "":
        conn.set_var("channel " + str(c), int(v))

def channel(c):
    while True:
        try:
            time.sleep(0.2)
            content = get_channel(c)
            if str(content) != "0" and content is not None:
                if str(content).startswith("00000"):
                    print("new user logged in SYSTEM: "+Encoding.decode(int(str(content)[5:]))+"\n")
                    s = makesession()
                    sessions.append(s)
                    set_channel(c, s)
                    chat = conversation(base_url="deepinfra", model="meta-llama/Meta-Llama-3-70B-Instruct", system_prompt=Encoding.decode(int(str(content)[5:])))
                    chats[str(s)] = chat
                else:
                    
                    chat = chats[str(content)[:5]]
                    t = time.time()
                    set_channel(c, "2")
                    while get_channel(c) != "1":
                        time.sleep(0.2)
                        if time.time()-t > 1:
                            t=time.time()
                            set_channel(c, "2")
                    print("User: "+Encoding.decode(int(str(content)[5:])),"\n\nAI: ",end="")
                    answer = chat.ask(Encoding.decode(int(str(content)[5:])), stream=True)

                    t = time.time()
                    sins = ""
                    for token in answer:
                        if token.token != None:
                            sins += token.token.replace("/", "//").replace("\n", "/n")
                            if time.time() - t > 0.2:
                                    set_channel(c, Encoding.encode(sins))
                                    print(sins, end="", flush=True)
                                    sins = ""
                                    t=time.time()
                    time.sleep(max(0, 0.2-(time.time()-t)))
                    print(sins, end="", flush=True)
                    set_channel(c, Encoding.encode(sins))
                    print("\n")
                    set_channel(c, "0")
        except:
            set_channel(c, Encoding.encode("... AN ERROR OCCURED, PLEASE RESTART THE PROJECT"))
            time.sleep(0.2)
            set_channel(c, 0)


def start_channel(c):
    thread = threading.Thread(target=channel, args=(c,))
    thread.start()
    return thread
for i in range(10):
    set_channel(i+1, 0)
# Start multiple channels if needed
threads = [start_channel(i+1) for i in range(10)]
print("server started")
# Keep the main thread alive to allow the threads to run
for thread in threads:
    thread.join()
