import json
import string
import random
import pandas as pd
from slack import WebClient
from pytrends.request import TrendReq

from flask import Flask, request, make_response

from matplotlib import rc
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

font_location = "C:\Windows\Fonts\malgun.ttf"
font_name = fm.FontProperties(fname=font_location).get_name()
plt.rc('font', family=font_name)
plt.rcParams['axes.unicode_minus'] = False

client = WebClient(token=os.environ['SLACK_API_TOKEN'])

app = Flask(__name__)

def make_name(length_of_string):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length_of_string))

def get_trend(keywords, dtime='today 5-y'):
    pytrend = TrendReq()
    pytrend.build_payload(kw_list = keywords, timeframe = dtime)
    trend_df = pytrend.interest_over_time()
    return trend_df

def event_handler(event_type, slack_event):
    headers = request.headers

    # request header에서 X-Slack-Retry-Num 탐지 시 X-Slack-No-Retry를 1로 설정하여 timeout에 대한 예외처리
    try:
        if headers['X-Slack-Retry-Num'] and headers['X-Slack-Retry-Reason'] :
            response = make_response("", 201)
            response.headers['X-Slack-No-Retry'] = 1
            return response
    except Exception as e:
        pass

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        trend_keyword = slack_event["event"]["text"].split(" ")[1:]
       
        if len(trend_keyword) <= 5 and len(trend_keyword) > 0 :
            fig, ax = plt.subplots()
            get_trend(keywords=trend_keyword).plot(ax=ax)
            filename = make_name(10) + ".png"
            plt.savefig(filename)
            client.files_upload(channels=channel, file=filename)
            return make_response(None, 200)

    message = "[%s] not found event handler." % event_type
    return make_response(message, 200, headers={"X-Slack-No-Retry":1})

@app.route("/bot", methods=["POST"])
def bot():
    if request.method == "POST":

        slack_event = json.loads(request.data)
        if "challenge" in slack_event:
            return make_response(slack_event["challenge"], 200, {"content_type":"application/json"})

        if "event" in slack_event:
            event_type = slack_event["event"]["type"]
            return event_handler(event_type, slack_event)
        
        return make_response("[NO EVENT IN SLACK REQUEST]", 404, headers={"X-Slack-No-Retry":1})

if __name__ == "__main__":
    app.run('0.0.0.0', port=5000, debug=True)