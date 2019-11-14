import os
import re
import json
import sys
from datetime import datetime
from pymongo import MongoClient

MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
Page = client["scrap-directory"].pages
Project = client["scrap-directory"].projects

# lineからlinkを抜き出す簡易的な処理
def extract_link(lines):
    links = []
    for line in lines:
        # $から始まらない行
        if not re.match(r"\$", line):
            ls = re.findall(r"\[[^\].+]+\]", line)
            for l in ls:
                # * と.iconとリンクになっているものは含めない
                if not ( "* " in l or ".icon" in l or "http://" in l or "https://" in l):
                    # [[]]]で囲われてる場合は強調とみなす
                    # しかし上記の正規表現の抽出の場合末端の]は一つしか抜き出されないので[[]にマッチするかをみる
                    if not re.match(r"^\[\[.+\]",l):
                        l = l.lstrip("[").rstrip("]")
                        # 前後にspaceやtabが含まれる場合があるのでtrip
                        l = l.strip()
                        # MercariGuide対策 and 数式対策
                        if not re.match(r"^#b.+",l) and not re.match(r"^\$ .+",l):
                            l = l.replace(" ","_")
                            if not l == "" and not l in links:
                                links.append(l)
            
            # #付きリンク記法対応
            splits = line.split()
            for split in splits:
                if re.match(r"^#.+",split):
                    # #付きのリンク記法はiconやhttpは自動で補完されないのでそのまま使う
                    s = split.lstrip("#")
                    s = s.replace(" ","_")
                    if not s in links:
                        links.append(s)

    return links


# linesを一つのtextにまとめる
def lines_to_text(lines):
    text = ""
    for line in lines:
        text += line + "\n" 
    return text

# 以下はベタ書きのtask
args = sys.argv
if len(args) <= 1:
    print("変換したいscrapbox-projectのjsonを指定してください")
    sys.exit()

target_file = args[1]
# /data以下に変換したいscrapboxのjsonを展開しておくこと
f = open(f'./data/{target_file}', 'r')
data = json.load(f)

project = data["name"]
pages = data["pages"]

# プロジェクト名を保存
if not Project.find_one({"name": project}):
    Project.insert_one({"name": project})

for page in pages:
    title = page["title"]
    lines = page["lines"]
    olinks = extract_link(lines)
    text = lines_to_text(lines)
    # spaceを_に置換
    # spaceは検索クエリのsplitで使うため
    _title = title.replace(" ","_")
    _olinks = []
    for ol in olinks:
        if not ol:
            continue
        if ol == _title:
            continue
        ol = ol.replace(" ","_")
        _olinks.append(ol)

    url = "https://scrapbox.io/" + project + "/" + title
    
    _page = {
        "project": project,
        "url": url,
        "title": _title,
        "olinks": _olinks,
        "text": text,
        "created": datetime.fromtimestamp(page['created']).isoformat(),
        "updated": datetime.fromtimestamp(page['updated']).isoformat()
    }
    Page.insert_one(_page)
