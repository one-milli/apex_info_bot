import json
import requests
import settings
import sys
import time
import tweepy
import urllib.request
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta, timezone
from requests_oauthlib import OAuth1Session
from urllib import response

# APSchedulerの変数を作成
scheduler = BlockingScheduler()


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


# そのスキンのキャラ/武器名をjsonに追加
def appendName(json_input):
    tgt_start = "_skin_"
    tgt_end = "_"
    for item in json_input:
        idx_start = item['content'][0]['ref'].find(tgt_start)
        buff = item['content'][0]['ref'][idx_start+6:]
        idx_end = buff.find(tgt_end)
        item['whose'] = buff[:idx_end]


@scheduler.scheduled_job('interval', minute=10)
def map_rotation(api):
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
    tweet_segment = ["【現在のマップローテーション】\n",
                     chr(map_list[current_map]['emoji']),
                     map_list[current_map]['name'],
                     "("+current_map_start_jst.strftime('%H:%M')+"~",
                     current_map_end_jst.strftime('%H:%M')+")\n\n",
                     "【次のマップローテーション】\n",
                     chr(map_list[next_map]['emoji']),
                     map_list[next_map]['name'],
                     "("+next_map_start_jst.strftime('%H:%M')+"~",
                     next_map_end_jst.strftime('%H:%M') + ")"]
    tweet_content = ""
    for i in range(len(tweet_segment)):
        tweet_content = tweet_content + tweet_segment[i]

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


@scheduler.scheduled_job('cron', hour=18)
def craft_rotation(api):
    time.sleep(10)
    item_list_daily = {"extended_light_mag": "拡張ライトマガジン Lv3",
                       "extended_heavy_mag": "拡張ヘビーマガジン Lv3",
                       "extended_energy_mag": "拡張エネルギーマガジン Lv3",
                       "extended_sniper_mag": "拡張スナイパーマガジン Lv3",
                       "shotgun_bolt": "ショットガンボルト Lv3",
                       "barrel_stabilizer": "バレルスタビライザー Lv3",
                       "standard_stock": "標準ストック Lv3",
                       "sniper_stock": "スナイパーストック Lv3",
                       "optic_hcog_bruiser": "2倍HCOG'ブルーザー'",
                       "optic_hcog_ranger": "3倍HCOG'レンジャー'",
                       "optic_variable_aog": "2~4倍可変式AOG",
                       "optic_digital_threat": "1倍デジタルスレット",
                       "optic_variable_sniper": "4~8倍可変式スナイパー",
                       "shatter_caps": "シャッターキャップ",
                       "kinetic_loader": "キネティックフィーダー",
                       "hammerpoiont_rounds": "ハンマーポイント",
                       "boosted_loader": "ブーステッドローダー",
                       "turbocharger": "ターボチャージャー"}
    item_list_weekly = {"backpack": "バックパック Lv3",
                        "helmet": "ヘルメット Lv3",
                        "knockdown_shield": "ノックダウンシールド Lv3",
                        "mobile_respawn_beacon": "モバイルリスポーンビーコン"}

    # クラフトローテーションの取得
    url_craft = "https://api.mozambiquehe.re/crafting?auth="
    als_api_key = settings.ALS_API_KEY
    res_craft = requests.get(url_craft + als_api_key)
    json_craft = json.loads(res_craft.text)
    if res_craft.status_code == 200:
        print("(ALS)Request succeeded")
    else:
        print("(ALS)Request failed with " + str(res_craft.status_code))
        sys.exit()

    daily_item_1 = json_craft[0]['bundleContent'][0]
    daily_item_2 = json_craft[0]['bundleContent'][1]
    weekly_item_1 = json_craft[1]['bundleContent'][0]
    weekly_item_2 = json_craft[1]['bundleContent'][1]

    JST = timezone(timedelta(hours=+9), 'JST')
    today = datetime.now(JST)

    # ツイート内容
    tweet_segment = ["【"+str(today.month)+"月"+str(today.day)+"日のクラフトローテーション】\n",
                     "デイリー:\n",
                     "["+chr(128313)+str(daily_item_1['cost'])+"] "+item_list_daily.get(
                         daily_item_1['itemType']['name'], daily_item_1['itemType']['name'])+"\n",
                     "["+chr(128313)+str(daily_item_2['cost'])+"] "+item_list_daily.get(
                         daily_item_2['itemType']['name'], daily_item_2['itemType']['name'])+"\n",
                     "ウィークリー:\n",
                     "["+chr(128313)+str(weekly_item_1['cost'])+"] " +
                     item_list_weekly[weekly_item_1['itemType']['name']]+"\n",
                     "["+chr(128313)+str(weekly_item_2['cost'])+"] "+item_list_weekly[weekly_item_2['itemType']['name']]]
    tweet_content = ""
    for i in range(len(tweet_segment)):
        tweet_content = tweet_content + tweet_segment[i]

    # ツイート送信
    api.update_status(tweet_content)
    print("Tweet(craft rotation) has been sent.")


@scheduler.scheduled_job('cron', day_of_week='tue', hour=18, minute=30)
def store_info():
    time.sleep(10)
    json_op = open('names_jp.json', encoding='utf-8')
    names_jp = json.load(json_op)

    # ストア情報の取得
    url_shop = "https://api.mozambiquehe.re/store?auth="
    als_api_key = settings.ALS_API_KEY
    res_shop = requests.get(url_shop + als_api_key)
    json_shop = json.loads(res_shop.text)
    if res_shop.status_code == 200:
        print("(ALS)Request succeeded")
    else:
        print("(ALS)Request failed with " + str(res_shop.status_code))
        sys.exit()

    appendName(json_shop)
    recolor_skins_json = []
    # リカラースキンのみ取り出し
    for item in json_shop:
        if len(item['pricing']) == 2:
            recolor_skins_json.append(item)

    # ツイート内容
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


# APIインスタンスを作成
auth = tweepy.OAuthHandler(settings.API_KEY, settings.API_SECRET_KEY)
auth.set_access_token(settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# APSchedulerを開始
scheduler.start()
