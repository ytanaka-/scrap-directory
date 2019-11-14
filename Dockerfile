# 個人プロジェクトなので https://github.com/nikolaik/docker-python-nodejs をベースイメージに使う
FROM nikolaik/python-nodejs:python3.7-nodejs10

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#RUN apt-get update
#RUN apt-get install -yqq nodejs npm
#RUN npm install n -g 
#RUN n 6

RUN npm install
RUN npm run build