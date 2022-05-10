import json
import requests
import sys
import time
import tweepy
import settings
from datetime import datetime, timedelta, timezone

# Heroku schedulerで毎日午前3時に実行
# 情報更新まで少し待つ
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

# Auth情報を取得，APIインスタンス作成
auth = tweepy.OAuthHandler(settings.API_KEY, settings.API_SECRET_KEY)
auth.set_access_token(settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# ツイート送信
api.update_status(tweet_content)
print("Tweet(craft rotation) has been sent.")
