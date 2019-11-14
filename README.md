## ScrapDirectory: リンク構造によるファセット型階層ナビゲーション

## Setup

```
$ docker-compose up
# /data以下にimportしたいscrapbox-projectのjsonファイルを配置し以下を実行
$ docker-compose exec web python importer/scrapbox-importer.py (your-scrapbox-project).json

# open http://localhost:5000/
```

## Tips
```
# contaier内のmongodbにアクセスしたい場合
$ docker-compose exec -it mongo mongo
$ > use scrap-directory
$ > db.pages.find() ..etc
```