import json
from urllib import response
import requests
import sys
import time
import twitter
import urllib.request
import settings
from requests_oauthlib import OAuth1Session

# Heroku schedulerで毎週午前3時半に実行
# 情報更新まで少し待つ
time.sleep(10)


def appendName(json_input):
    tgt_start = "_skin_"
    tgt_end = "_"
    for item in json_input:
        idx_start = item['content'][0]['ref'].find(tgt_start)
        buff = item['content'][0]['ref'][idx_start+6:]
        idx_end = buff.find(tgt_end)
        item['whose'] = buff[:idx_end]


url_shop = "https://api.mozambiquehe.re/store?auth="
als_api_key = settings.ALS_API_KEY
res_shop = requests.get(url_shop + als_api_key)
json_shop = json.loads(res_shop.text)
if res_shop.status_code == 200:
    print("(ALS)Request succeeded")
else:
    print("(ALS)Request failed with " + str(res_shop.status_code))
    sys.exit()
json_op = open('names_jp.json', encoding='utf-8')
names_jp = json.load(json_op)

# そのスキンのキャラ/武器名をjsonに追加
appendName(json_shop)

recolor_skins_json = []
# リカラースキンのみ取り出し
for item in json_shop:
    if len(item['pricing']) == 2:
        recolor_skins_json.append(item)

tweet_segment = ["【色違いスキン ストア情報】\n",
                 "1."+recolor_skins_json[0]['content'][0]['name']+"\n",
                 "("+names_jp.get(recolor_skins_json[0]['whose'],
                                  recolor_skins_json[0]['whose'])+"のスキン)\n\n",
                 "2."+recolor_skins_json[1]['content'][0]['name']+"\n",
                 "("+names_jp.get(recolor_skins_json[1]['whose'],
                                  recolor_skins_json[1]['whose'])+"のスキン)"]

tweet_content = ""
for i in range(len(tweet_segment)):
    tweet_content = tweet_content + tweet_segment[i]

twitter = OAuth1Session(settings.API_KEY, settings.API_SECRET_KEY,
                        settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)
url_media = "https://upload.twitter.com/1.1/media/upload.json"
url_text = "https://api.twitter.com/1.1/statuses/update.json"

media_id = []
for i in range(2):
    headers = {"User-Agent": "Mozilla/5.0"}
    request = urllib.request.Request(
        url=recolor_skins_json[i]['asset'], headers=headers)
    response = urllib.request.urlopen(request)
    data = response.read()
    files = {"media": data}
    req_media = twitter.post(url_media, files=files)
    media_id.append(json.loads(req_media.text)['media_id_string'])
    print("Image uploaded "+str(i+1))
media_id = ','.join(media_id)

params = {"status": tweet_content, "media_ids": media_id}

# ツイート送信
twitter.post(url_text, params=params)
print("Tweet(recolor store info) has been sent.")
