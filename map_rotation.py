import json
import requests
import sys
import time
import tweepy
import settings
from datetime import datetime, timedelta, timezone


# 送信から15時間以上経ったマップ情報ツイートを削除
def cleanUp(screen_name, api):
    head = "【現在のマップローテーション】"
    tweets = api.user_timeline(screen_name=screen_name, count=15)
    now = datetime.now(timezone.utc)
    for tweet in tweets:
        timestamp = tweet.created_at
        diff = now - timestamp
        diff_days = diff.days
        diff_hours = diff.seconds/3600
        diff_hours = diff_hours+diff_days*24
        if 6 < diff_hours and diff_hours < 30 and tweet.text.startswith(head):
            api.destroy_status(tweet.id)
            print("Tweet(ID:"+str(tweet.id)+") has been deleted")


# Heroku schedulerで10分ごとに実行
# 情報更新まで少し待つ
time.sleep(5)

screen_name = "ApexMapBot"
map_list = {"Kings Canyon": {"name": "キングスキャニオン", "emoji": 127964}, "World's Edge": {"name": "ワールズエッジ", "emoji": 127755},
            "Olympus": {"name": "オリンパス", "emoji": 127961}, "Storm Point": {"name": "ストームポイント", "emoji": 127965}}

# マップローテーションの取得
url_map = "https://api.mozambiquehe.re/maprotation?auth="
als_api_key = settings.ALS_API_KEY
res_map = requests.get(url_map + als_api_key)
json_map = json.loads(res_map.text)
if res_map.status_code == 200:
    print("(ALS)Request succeeded")
else:
    print("(ALS)Request failed with " + str(res_map.status_code))
    sys.exit()

current_map = json_map['current']['map']
current_map_start = json_map['current']['readableDate_start']
current_map_end = json_map['current']['readableDate_end']
next_map = json_map['next']['map']
next_map_start = json_map['next']['readableDate_start']
next_map_end = json_map['next']['readableDate_end']

# JSTに変換
current_map_start_jst = datetime.strptime(
    current_map_start, '%Y-%m-%d %H:%M:%S')
current_map_start_jst = current_map_start_jst + timedelta(hours=9)
current_map_end_jst = datetime.strptime(
    current_map_end, '%Y-%m-%d %H:%M:%S')
current_map_end_jst = current_map_end_jst + timedelta(hours=9)
next_map_start_jst = datetime.strptime(
    next_map_start, '%Y-%m-%d %H:%M:%S')
next_map_start_jst = next_map_start_jst + timedelta(hours=9)
next_map_end_jst = datetime.strptime(
    next_map_end, '%Y-%m-%d %H:%M:%S')
next_map_end_jst = next_map_end_jst + timedelta(hours=9)

# ツイート内容
tweet_content = "【現在のマップローテーション】\n" + chr(map_list[current_map]['emoji']) + map_list[current_map]['name'] + "("+current_map_start_jst.strftime('%H:%M') + "~" + current_map_end_jst.strftime(
    '%H:%M') + ")\n\n" + "【次のマップローテーション】\n" + chr(map_list[next_map]['emoji']) + map_list[next_map]['name'] + "("+next_map_start_jst.strftime('%H:%M') + "~" + next_map_end_jst.strftime('%H:%M') + ")"

# APIインスタンスを作成
auth = tweepy.OAuthHandler(settings.API_KEY, settings.API_SECRET_KEY)
auth.set_access_token(settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# 自身の直近10ツイートを取得し，まだtweet_contentをツイートしていないことを確認
isnt_tweeted = True
tweets = api.user_timeline(screen_name=screen_name, count=10)
for tweet in tweets:
    if tweet.text == tweet_content:
        isnt_tweeted = False
        print("This tweet was already sent")
        break

# ツイート送信(まだtweet_contentをツイートしていないとき)
if isnt_tweeted:
    api.update_status(tweet_content)
    print("Tweet(map rotation) has been sent")
    cleanUp(screen_name, api)
