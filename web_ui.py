# flask --app web_ui run

from flask import Flask, request, render_template

app = Flask(__name__)

## TODO:
# add status of remote download directory (red error if no access)
# add form to update credentials
## maybe a health check to see if they are valid
# add output from processing
## make it live?


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == "GET":
        return render_template('index.html')
    else:  # request.method == "POST"
        text = request.form['text']
        processed_text = text.upper()
        return processed_text
