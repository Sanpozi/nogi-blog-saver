import os
import requests
from time import sleep
from bs4 import BeautifulSoup

def extract(url: str) -> (str, str, str, str):
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")

    title = soup.title.text
    if not title: # タイトルがないことがある。。
        title = " （※無題）"
    date = soup.find("p", class_="bd--hd__date").text
    header = str(soup.find("header", class_="bd--hd"))
    content = str(soup.find("div", class_="bd--edit"))
    if title and date and content:
        return title, date, header, content
    else:
        raise Exception("Can't fetch contents url: " + url)

def save_post(post_date: str, header: str, body: str):
    _date, time = post_date.split() # ex) "2021.12.31 20:18" スペースで分割
    year, month, date = _date.split('.')
    path ="./blog/" + year + '-' + month + '-' + date + 'T' + time
    os.makedirs(path, exist_ok=True)

    # 画像表示のためhtmlを編集する
    body_soup = BeautifulSoup(body, features="html.parser")
    # 含まれる画像を取得
    imgs = body_soup.find_all("img")
    for i, img in enumerate(imgs):
        # 画像ファイルはhtmlと同階層に、{画像のインデックス}.jpegで保存
        # TODO gif対応
        file_name = str(i) + ".jpeg"
        if img.parent.name == "div": # dcimgを利用していない
            # 画像保存
            relative_img_src = img.get("src")
            if relative_img_src and relative_img_src.startswith("/files"):
                img_src = "https://www.nogizaka46.com" + relative_img_src
                response = requests.get(img_src)
                with open(path + '/' + file_name, 'wb') as file:
                    file.write(response.content)
                # html 書き換え
                img.attrs["src"] = file_name
            else: # 不明なパスの画像が混じっている
                print("missing img src")
        elif img.parent.name == "a": # dcimgで圧縮されている場合
            img_parent_a_tag = img.parent
            # sessionで通信する必要がある
            session = requests.Session()
            dcimg_response = session.get(img_parent_a_tag.attrs["href"]) # dcimgサイトのビュー画面にアクセス
            dcimg_soup = BeautifulSoup(dcimg_response.text, features="html.parser")
            original_image_tag = dcimg_soup.find("img", class_="original_image")
            if original_image_tag: # 圧縮前の画像が削除されていない
                _img_src = "http://dcimg.awalker.jp" + original_image_tag.attrs["src"]
                response = session.get(_img_src) # ビュー画面にアクセスしたのと同じセッションで画像ソースにアクセス
                with open(path + '/' + file_name, 'wb') as file:
                    file.write(response.content)
            else: # 圧縮前の画像が削除済みの場合
                # 圧縮後の画像を保存
                img_src = "https://www.nogizaka46.com" + img.attrs["src"]
                response = requests.get(img_src)
                with open(path + '/' + file_name, 'wb') as file:
                    file.write(response.content)
            # html書き換え
            new_tag = body_soup.new_tag("img", src=file_name)
            img_parent_a_tag.replace_with(new_tag)

    # 変換済みのhtmlを保存
    formatted_html = header + str(body_soup)
    with open(path + '/index.html', mode='w') as f:
        f.write(formatted_html)

def get_previous_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features="html.parser")
    a_tags = soup.select("a.bd--hn__a.hv--op")
    for a_tag in a_tags:
        link_text = a_tag.p.text
        if("前の記事" == link_text):
            previous_url = "https://www.nogizaka46.com" + a_tag["href"]
            return previous_url
    raise Exception("Can't find previous url of: " + url)

def main():
    url = "https://www.nogizaka46.com/s/n46/diary/detail/100221?ima=2816&cd=MEMBER"
    while True:
        print("Saving blog post: " + url)
        title, date, header, body = extract(url)
        print("    title: " + title + ", date: " + date)
        save_post(date, header, body)
        print("Saved!")
        url = get_previous_url(url)
        sleep(3)

if __name__ == "__main__":
    main()
