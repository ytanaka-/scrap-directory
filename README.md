## ScrapDirectory: リンク構造によるファセット型階層ナビゲーション

Scrapboxのリンク構造を用いて階層ナビゲーションを実現するシステムです。

一般的な階層型検索と異なり、ファセット型検索になっているのが特徴です。

### Setup

```
$ git clone git@github.com:ytanaka-/scrap-directory.git
$ cd scrap-directory
$ docker-compose up
# /data以下にimportしたいscrapbox-projectのjsonファイルを配置し以下を実行
$ docker-compose exec web python importer/scrapbox-importer.py (your-scrapbox-project).json
# open http://localhost:5000/
```

### Tips

#### contaier内のmongodbにアクセスしたい場合
```
$ docker-compose exec -it mongo mongo
$ > use scrap-directory
$ > db.pages.find() ..etc
```

### Development
Docker以外で開発したい場合、MongoDBとNode.js, Pythonの実行環境が必要になります。

```
$ npm run watch
# 別タブで以下を実行
$ python server.py
```