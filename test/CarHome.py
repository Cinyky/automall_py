import json
import os
import re
import time

import pymysql
import requests
import urllib3.exceptions
from lxml import etree

main_url = 'https://car.autohome.com.cn/javascript/NewSpecCompare.js'
photo_url = 'https://www.autohome.com.cn/grade/carhtml/'
type_type_url = "https://car.autohome.com.cn/duibi/ashx/specComparehandler.ashx?callback=jsonpCallback&type=1&seriesid="
http = urllib3.PoolManager()
html = requests.get(main_url).text
data = re.findall(r'=(.*?);', html, re.S)[0]
dir_string = '/file/'
folder = os.getcwd() + dir_string
if not os.path.exists(folder):
    res = os.makedirs(folder, mode=0o777)
with open(folder + "data.json", 'w', encoding='utf-8') as f:
    f.write(data)
with open(folder + "data.json", 'r', encoding='utf-8') as f:
    datas = json.loads(f.read())

for data in datas:
    brands = {}
    brands['name'] = data['N']
    brands['ini'] = data['L']
    # 获取图片链接
    url = photo_url + brands['ini'] + "_photo.html"
    html = requests.get(url).text
    selecter = etree.HTML(html)
    imgs = selecter.xpath('//dl/dt/a/img/@src')
    titles = selecter.xpath('//dl/dt/div/a/text()')
    for title, img in zip(titles, imgs):
        if title == data['N']:
            brands['img'] = img.strip('//')
    types = []
    for tss in data['List']:
        for t in tss['List']:
            ts = {}
            ts['name'] = t['N']
            ts['seriesid'] = t['I']
            print(t['N'])
            '''
            获取分类下的分类
            '''
            type_url = type_type_url + str(t['I'])
            type_json = requests.get(type_url).text
            type_json = re.findall(r'\({(.*?)}\)', type_json, re.S)[0]
            json_file = t['N'].replace('/', '')
            with open(folder + json_file + ".json", 'w+', encoding='utf-8') as f:
                f.write("{" + type_json + "}")
            with open(folder + json_file + ".json", 'r', encoding='utf-8') as f:
                datas = json.loads(f.read())
            sl = []
            for ty_j in datas['List']:
                for key, value in ty_j.items():
                    if type(value) == list:
                        for v in value:
                            sl.append(v['N'])
                    ts['sl'] = sl
            types.append(ts)
    brands['type'] = types
    """
    创建文件夹
    """
    dir_string = '/file/brand'
    folder1 = os.getcwd() + dir_string
    if not os.path.exists(folder1):
        res = os.makedirs(folder1, mode=0o777)
    """
    下载图片
    """
    heades = {
        "User-Agent": "Mozilla / 5.0(Windows NT 10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 71.0.3578.98Safari / 537.36"
    }
    try:
        try:
            req = http.request('GET', brands['img'], headers=heades)
            res = req.data
            file_name = folder1 + "/" + brands['name'] + ".png"
            with open(file_name, 'wb') as f:
                f.write(res)
                brands['img'] = file_name
            time.sleep(1)
        except urllib3.exceptions.LocationParseError as e:
            brands['img'] = ""
            print(e)
    except KeyError as e:
        brands['img'] = ''
    """
    数据入库
    """
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='weiqing', charset='utf8')
    cursor = conn.cursor()
    print((brands['name'], brands['ini'], brands['img']));
    cursor.execute("insert into brand(name,ini,img)values(%s,%s,%s)", (brands['name'], brands['ini'], brands['img']))
    b_pid = cursor.lastrowid
    for m_t in brands['type']:
        print((b_pid, m_t['name']))
        cursor.execute("insert into type(b_id,name)values(%s,%s)", (b_pid, m_t['name']))
        t_pid = cursor.lastrowid
        try:
            for m_s in m_t['sl']:
                print((t_pid, m_s))
                cursor.execute("insert into slis(t_id,name)values(%s,%s)", (t_pid, m_s))
        except KeyError as e:
            print(e)
            cursor.execute("insert into slis(t_id,name)values(%s,%s)", (t_pid, ""))
    conn.commit()
    cursor.close()
    conn.close()
    print(brands['name'] + "====" + brands['ini'] + "======" + brands['img'])
exit()
