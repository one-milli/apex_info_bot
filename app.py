import json
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
import requests
import tweepy
from requests_oauthlib import OAuth1Session
import settings

# 和訳データ
map_list = {"Kings Canyon": {"name": "キングスキャニオン", "emoji": 127964},
            "World's Edge": {"name": "ワールズエッジ", "emoji": 127755},
            "Olympus": {"name": "オリンパス", "emoji": 127961},
            "Storm Point": {"name": "ストームポイント", "emoji": 127965},
            "Broken Moon": {"name": "ブロークンムーン", "emoji": 127768}}
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
                   "hammerpoint_rounds": "ハンマーポイント",
                   "boosted_loader": "ブーステッドローダー",
                   "turbocharger": "ターボチャージャー",
                   "double_tap_trigger": "ダブルタップ",
                   "skullpiercer_rifling": "スカルピアサー",
                   "laser_sight": "レーザーサイト Lv3",
                   "anvil_receiver": "ハンマーポイント"}
item_list_weekly = {"backpack": "バックパック Lv3",
                    "helmet": "ヘルメット Lv3",
                    "knockdown_shield": "ノックダウンシールド Lv3",
                    "mobile_respawn_beacon": "モバイルリスポーンビーコン"}

# Twitter APIキー
BEARER_TOKEN = settings.BEARER_TOKEN
API_KEY = settings.API_KEY
API_SECRET_KEY = settings.API_SECRET_KEY
ACCESS_TOKEN = settings.ACCESS_TOKEN
ACCESS_TOKEN_SECRET = settings.ACCESS_TOKEN_SECRET
# ALS APIキー
ALS_API_KEY = settings.ALS_API_KEY

# 認証
client = tweepy.Client(BEARER_TOKEN, API_KEY, API_SECRET_KEY,
                       ACCESS_TOKEN, ACCESS_TOKEN_SECRET)


# 送信から6時間以上経ったマップ情報ツイートを削除
def cleanUp(screen_name, api):
    head = "【現在のマップローテーション】"
    tweets = api.user_timeline(screen_name=screen_name, count=10)
    now = datetime.now(timezone.utc)
    for tweet in tweets:
        timestamp = tweet.created_at
        diff = now - timestamp
        diff_days = diff.days
        diff_hours = diff.seconds / 3600
        diff_hours = diff_hours + diff_days * 24
        if 6 < diff_hours and tweet.text.startswith(head):
            api.destroy_status(tweet.id)
            print("Tweet(ID:" + str(tweet.id) + ") has been deleted")


# そのスキンのキャラ/武器名をjsonに追加
def appendName(json_input):
    tgt_start = "_skin_"
    tgt_end = "_"
    for item in json_input:
        idx_start = item['content'][0]['ref'].find(tgt_start)
        buff = item['content'][0]['ref'][idx_start + 6:]
        idx_end = buff.find(tgt_end)
        item['whose'] = buff[:idx_end]


def map_rotation():
    time.sleep(5)

    # マップローテーションの取得
    url_map = "https://api.mozambiquehe.re/maprotation?auth="
    res_map = requests.get(url_map + ALS_API_KEY)
    json_map = json.loads(res_map.text)
    if res_map.status_code == 200:
        print("(ALS map)Request succeeded")
    else:
        print("(ALS map)Request failed with " + str(res_map.status_code))
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
    current_emoji = chr(map_list[current_map]['emoji'])
    current_map_name = map_list[current_map]['name']
    current_map_start_time = current_map_start_jst.strftime('%H:%M')
    current_map_end_time = current_map_end_jst.strftime('%H:%M')
    next_emoji = chr(map_list[next_map]['emoji'])
    next_map_name = map_list[next_map]['name']
    next_map_start_time = next_map_start_jst.strftime('%H:%M')
    next_map_end_time = next_map_end_jst.strftime('%H:%M')

    tweet_content = f"【現在のマップローテーション】\n"\
                    f"{current_emoji}{current_map_name}"\
                    f"({current_map_start_time}~{current_map_end_time})\n\n"\
                    f"【次のマップローテーション】\n"\
                    f"{next_emoji}{next_map_name}"\
                    f"({next_map_start_time}~{next_map_end_time})"

    # ツイート送信
    client.create_tweet(text=tweet_content)
    print("(Map)Tweet has been sent.")


def craft_rotation():
    time.sleep(5)

    # クラフトローテーションの取得
    url_craft = "https://api.mozambiquehe.re/crafting?auth="
    res_craft = requests.get(url_craft + ALS_API_KEY)
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
    tweet_segment = ["【" + str(today.month) + "月" + str(today.day) + "日のクラフトローテーション】\n",
                     "デイリー:\n",
                     "[" + chr(128313) + str(daily_item_1['cost']) + "] " + item_list_daily.get(
                         daily_item_1['itemType']['name'], daily_item_1['itemType']['name']) + "\n",
                     "[" + chr(128313) + str(daily_item_2['cost']) + "] " + item_list_daily.get(
                         daily_item_2['itemType']['name'], daily_item_2['itemType']['name']) + "\n",
                     "ウィークリー:\n",
                     "[" + chr(128313) + str(weekly_item_1['cost']) + "] " +
                     item_list_weekly[weekly_item_1['itemType']['name']] + "\n",
                     "[" + chr(128313) + str(weekly_item_2['cost']) + "] " + item_list_weekly[weekly_item_2['itemType']['name']]]
    tweet_content = ""
    for i in range(len(tweet_segment)):
        tweet_content = tweet_content + tweet_segment[i]

    # Authenticate Twitter API
    twitter = OAuth1Session(API_KEY, API_SECRET_KEY,
                            ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    url_media = "https://upload.twitter.com/1.1/media/upload.json"

    media_id = []

    headers = {"User-Agent": "Mozilla/5.0"}
    request = urllib.request.Request(
        url=daily_item_1['itemType']['asset'], headers=headers)
    response = urllib.request.urlopen(request)
    data = response.read()
    files = {"media": data}
    req_media = twitter.post(url_media, files=files)
    media_id.append(json.loads(req_media.text)['media_id_string'])
    print("Image uploaded (1)")

    request = urllib.request.Request(
        url=daily_item_2['itemType']['asset'], headers=headers)
    response = urllib.request.urlopen(request)
    data = response.read()
    files = {"media": data}
    req_media = twitter.post(url_media, files=files)
    media_id.append(json.loads(req_media.text)['media_id_string'])
    print("Image uploaded (2)")

    request = urllib.request.Request(
        url=weekly_item_1['itemType']['asset'], headers=headers)
    response = urllib.request.urlopen(request)
    data = response.read()
    files = {"media": data}
    req_media = twitter.post(url_media, files=files)
    media_id.append(json.loads(req_media.text)['media_id_string'])
    print("Image uploaded (3)")

    request = urllib.request.Request(
        url=weekly_item_2['itemType']['asset'], headers=headers)
    response = urllib.request.urlopen(request)
    data = response.read()
    files = {"media": data}
    req_media = twitter.post(url_media, files=files)
    media_id.append(json.loads(req_media.text)['media_id_string'])
    print("Image uploaded (4)")

    media_id = ','.join(media_id)

    # ツイート送信
    client.create_tweet(text=tweet_content, media_ids=media_id)
    print("(Craft)Tweet has been sent.")


def craft_rotation2():
    time.sleep(5)

    # クラフトローテーションの取得
    url_craft = "https://api.mozambiquehe.re/crafting?auth="
    res_craft = requests.get(url_craft + ALS_API_KEY)
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
    tweet_segment = ["【" + str(today.month) + "月" + str(today.day) + "日のクラフトローテーション】\n",
                     "デイリー:\n",
                     "[" + chr(128313) + str(daily_item_1['cost']) + "] " + item_list_daily.get(
                         daily_item_1['itemType']['name'], daily_item_1['itemType']['name']) + "\n",
                     "[" + chr(128313) + str(daily_item_2['cost']) + "] " + item_list_daily.get(
                         daily_item_2['itemType']['name'], daily_item_2['itemType']['name']) + "\n",
                     "ウィークリー:\n",
                     "[" + chr(128313) + str(weekly_item_1['cost']) + "] " +
                     item_list_weekly[weekly_item_1['itemType']['name']] + "\n",
                     "[" + chr(128313) + str(weekly_item_2['cost']) + "] " + item_list_weekly[weekly_item_2['itemType']['name']]]
    tweet_content = ""
    for i in range(len(tweet_segment)):
        tweet_content = tweet_content + tweet_segment[i]

    # ツイート送信
    client.create_tweet(text=tweet_content)
    print("(Craft)Tweet has been sent.")


def predator():
    time.sleep(5)
    # プレデターボーダーの情報取得
    ALS_API_KEY = settings.ALS_API_KEY
    url_map = "https://api.mozambiquehe.re/maprotation?version=2&auth="
    res_map = requests.get(url_map + ALS_API_KEY)
    json_map = json.loads(res_map.text)
    if res_map.status_code == 200:
        print("(ALS map)Request succeeded")
    else:
        print("(ALS map)Request failed with " + str(res_map.status_code))
        sys.exit()

    time.sleep(5)
    url_pred = "https://api.mozambiquehe.re/predator?auth="
    res_pred = requests.get(url_pred + ALS_API_KEY)
    json_pred = json.loads(res_pred.text)
    if res_pred.status_code == 200:
        print("(ALS predator)Request succeeded")
    else:
        print("(ALS predator)Request failed with " + str(res_pred.status_code))
        sys.exit()

    current_map = json_map['ranked']['current']['map']
    br_pred_cap = json_pred['RP']

    # ツイート内容
    emoji = chr(map_list[current_map]['emoji'])
    ranked_map = map_list[current_map]['name']
    pc_rp = str(br_pred_cap['PC']['val'])
    ps_rp = str(br_pred_cap['PS4']['val'])
    sw_rp = str(br_pred_cap['SWITCH']['val'])
    pc_masters = str(br_pred_cap['PC']['totalMastersAndPreds'])
    ps_masters = str(br_pred_cap['PS4']['totalMastersAndPreds'])
    sw_masters = str(br_pred_cap['SWITCH']['totalMastersAndPreds'])

    tweet_content = f"【本日のランクマップ】\n"\
                    f"{emoji}{ranked_map}\n\n"\
                    f"【現在のプレデターボーダー】\n"\
                    f"PC      :{pc_rp}RP\n" if int(pc_rp) > 15000 else f"PC      :{pc_rp}RP(現在{pc_masters}人)\n"\
                    f"PS4/5 :{ps_rp}RP\n" if int(ps_rp) > 15000 else f"PS4/5 :{ps_rp}RP(現在{ps_masters}人)\n"\
                    f"Switch:{sw_rp}RP\n" if int(sw_rp) > 15000 else f"Switch:{sw_rp}RP(現在{sw_masters}人)"

    # ツイート送信
    client.create_tweet(text=tweet_content)
    print("(Predator)Tweet has been sent.")


def store_info():
    time.sleep(10)
    screen_name = "ApexMapBot"
    json_op1 = open('names_jp.json', encoding='utf-8')
    names_jp = json.load(json_op1)
    json_op2 = open('skins_jp.json', encoding='utf-8')
    skins_jp = json.load(json_op2)

    # ストア情報の取得
    url_shop = "https://api.mozambiquehe.re/store?auth="
    ALS_API_KEY = settings.ALS_API_KEY
    res_shop = requests.get(url_shop + ALS_API_KEY)
    json_shop = json.loads(res_shop.text)
    if res_shop.status_code == 200:
        print("(ALS)Request succeeded")
    else:
        print("(ALS)Request failed with " + str(res_shop.status_code))
        sys.exit()

    appendName(json_shop)
    recolor_skins_json = []
    now = int(time.time())
    # リカラースキンのみ取り出し
    sum = 0
    for item in json_shop:
        if len(item['pricing']) > 1 and item['expireTimestamp'] > now:
            if item['pricing'][0]['ref'] == 'Legend Tokens':
                recolor_skins_json.append(item)
                sum += 1
    if len(recolor_skins_json) == 0:
        sys.exit()
    recolor_skins_json_sorted = sorted(
        recolor_skins_json, key=lambda x: x['content'][0]['name'])

    # ツイート内容
    skin_key = []
    tweet_segment = ["【色違いスキン ストア情報】\n"]
    for i in range(sum):
        name_key = recolor_skins_json_sorted[i]['whose']
        skin_key = recolor_skins_json_sorted[i]['content'][0]['name']
        skin_jp = skins_jp.get(skin_key, skin_key)
        name_jp = names_jp.get(name_key, name_key)
        tweet_segment.append("・" + skin_jp + "\n(" + name_jp + ")")
        if i != sum:
            tweet_segment.append("\n\n")
    tweet_content = ""
    for i in range(len(tweet_segment)):
        tweet_content = tweet_content + tweet_segment[i]

    twitter = OAuth1Session(API_KEY, API_SECRET_KEY,
                            ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    url_media = "https://upload.twitter.com/1.1/media/upload.json"
    url_text = "https://api.twitter.com/1.1/statuses/update.json"

    media_id = []
    m = min(sum, 4)
    for i in range(m):
        headers = {"User-Agent": "Mozilla/5.0"}
        request = urllib.request.Request(
            url=recolor_skins_json_sorted[i]['asset'], headers=headers)
        response = urllib.request.urlopen(request)
        data = response.read()
        files = {"media": data}
        req_media = twitter.post(url_media, files=files)
        media_id.append(json.loads(req_media.text)['media_id_string'])
        print("Image uploaded " + str(i + 1))
    media_id = ','.join(media_id)
    params = {"status": tweet_content, "media_ids": media_id}

    # APIインスタンスを作成
    auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    # 自身の直近15ツイートを取得し，まだtweet_contentをツイートしていないことを確認
    isnt_tweeted = True
    tweets = api.user_timeline(screen_name=screen_name, count=15)
    for tweet in tweets:
        if tweet_content in tweet.text:
            isnt_tweeted = False
            print("(Store)This tweet was already sent")
            break

    # ツイート送信
    if isnt_tweeted:
        twitter.post(url_text, params=params)
        print("(Store)Tweet has been sent.")


def tweet(event, context):
    time.sleep(3)
    JST = timezone(timedelta(hours=+9), 'JST')
    dt_now = datetime.now(JST)
    if dt_now.hour == 3:
        map_rotation()
        predator()
    else:
        map_rotation()
