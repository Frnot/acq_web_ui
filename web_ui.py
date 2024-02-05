#from task_runner import process

import logging
import justpy as jp
from dotenv import dotenv_values, set_key
import queue
import asyncio


from qobuz_downloader import authenticate, download_url
from task_runner import Task_Runner



## TODO:
# add status of remote download directory (red error if no access)
# add form to update credentials
## maybe a health check to see if they are valid
# add output from processing
## make it live?

# add a queue or spawn a new thread for each job so rapid new links doesnt interfere with previous


# TODO: add these text input/validate fields to their own component

env = dotenv_values(".env")
email = env["email"]
password = env["password"]

input_classes = "m-2 bg-gray-200 border-2 border-gray-200 rounded w-64 py-2 px-4 text-gray-700 focus:outline-none focus:bg-white focus:border-purple-500 display:inline-block"
p_classes = 'm-2 p-2 h-32 text-xl border-2'


status_classes = "rounded"


def start_taskrunner():
    # JustPy event loop needs to exist before initializing Task_Runner
    msg_queue = queue.Queue()
    global taskrunner
    taskrunner = Task_Runner(msg_queue)

    jp.run_task(write_logs(msg_queue))


logs = jp.Div(classes='text-lg border m-2 p-2 overflow-auto h-64', delete_flag=False)

wp = ""
def web_ui(request):
    global wp
    wp = jp.WebPage()
    wp.default_email = email
    wp.default_password = password

    if auth_stat := authenticate(email, password):
        wp.status = jp.P(a=wp, text="Successfully logged into Qobuz", classes=status_classes+" bg-green-200")    
    else:
        wp.status = jp.P(a=wp, text="Could not log in to Qobuz. Please update credentials", classes=status_classes+" bg-red-300")
    
    # Email field
    un = jp.Div(a=wp, classes='display:inline-block')
    email_label = jp.Label(a=un, text="Email:         ")
    wp.un_input = jp.Input(a=un, classes=input_classes, placeholder=wp.default_email)
    email_label.for_component = wp.un_input

    # Password field
    pw = jp.Div(a=wp, classes='display:inline-block')
    password_label = jp.Label(a=pw, text="Password:")
    wp.pw_input = jp.Input(a=pw, classes=input_classes, placeholder=wp.default_password)
    password_label.for_component = wp.pw_input

    # Credential update button
    button_classes = 'w-64 mr-2 mb-2 bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-full'
    jp.Button(text=f'Update and log in', a=wp, classes=button_classes, click=login)

    #####

    # Qobuz URL Entry
    url_entry = jp.Div(a=wp, classes='display:inline-block')
    input_label = jp.Label(a=url_entry, text="Qobuz URL:")
    url_entry.input_field = jp.Input(a=url_entry, classes=input_classes)
    #input_label.for_component = url_entry.input_field
    jp.Button(a=url_entry, text="Download", click=process_url, classes="w-64 bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-full")

    # Logs
    wp.add(logs)
    logs.add_page(wp)

    return wp


async def process_url(self, msg):
    if not (url := self.a.input_field.value):
        return
    self.a.input_field.value = ""
    taskrunner.jobs.put(url)


def login(self, msg):
    lem = self.a.un_input.value if self.a.un_input.value else email
    lpwd = self.a.pw_input.value if self.a.pw_input.value else password
    if authenticate(lem, lpwd):
        self.a.status.text="Successfully logged into Qobuz"
        self.a.status.classes=status_classes+" bg-green-200"
        self.a.default_email = lem
        self.a.default_password = lpwd
        set_key(dotenv_path=".env", key_to_set="email", value_to_set=lem)
        set_key(dotenv_path=".env", key_to_set="password", value_to_set=lpwd)
    else:
        self.a.status.text="Could not log in to Qobuz. Please update credentials"
        self.a.status.classes=status_classes+" bg-red-300"
    # Update forms
    self.a.un_input.placeholder = self.a.default_email
    self.a.pw_input.placeholder = self.a.default_password
    self.a.un_input.value = ""
    self.a.pw_input.value = ""



async def write_logs(msg_queue):
    while True:
        if not msg_queue.empty():
            msg = msg_queue.get()
            print(f"\\\\\\\\\\Printing to webconsole: {msg}") # DEBUG
            logs.add_component(jp.P(text=msg))
            jp.run_task(logs.update())
        else:
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    jp.justpy(web_ui, startup=start_taskrunner)
