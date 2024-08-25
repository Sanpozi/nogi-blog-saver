import os
import sys
import requests
import logging
from logging import INFO
from time import sleep
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(INFO)
stream_handler = logging.StreamHandler(sys.stdout)
fmt = logging.Formatter("%(levelname)s: %(message)s")
stream_handler.setFormatter(fmt)
logger.addHandler(stream_handler)

LATEST_TAMAMIBLOG_POST_URL = "https://www.nogizaka46.com/s/n46/diary/detail/102622?ima=3849&cd=MEMBER"
DEFAULT_START_POST_URL = LATEST_TAMAMIBLOG_POST_URL

FOLDER = "./blog"

def extract_post(url: str) -> tuple:
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")

    title = soup.title.text
    if not title: # タイトルがないことがある
        logger.warning("No title")
        title = "NO TITLE"
    date = soup.find("p", class_="bd--hd__date").text
    body = str(soup.find("div", class_="bd--edit"))
    if title and date and body:
        return title, date, body
    else:
        raise Exception("Can't fetch contents url: " + url)

def save_post(post_date: str, title: str, body: str):
    body_soup = BeautifulSoup(body, features="html.parser")

    # フォルダを準備
    _date, _ = post_date.split() # ex) "2021.12.31 20:18" スペースで分割
    year, month, date = _date.split('.')
    parent_path = FOLDER + "/" + year + "-" + month + "-" + date
    os.makedirs(parent_path, exist_ok=True)
    post_path = parent_path + "/" + title
    os.makedirs(post_path, exist_ok=True)

    # 画像を取得&置換 
    gather_and_replace_img(body_soup, post_path)

    # htmlを保存
    title_element = f"<h1>{title}</h1>\n"
    formatted_html = title_element + str(body_soup)
    with open(post_path + '/index.html', mode='w') as f:
        f.write(formatted_html)

def gather_and_replace_img(body_soup: BeautifulSoup, post_path:str):
    # 含まれる画像を取得
    imgs = body_soup.find_all("img")
    for i, img in enumerate(imgs):
        # 画像ファイルはhtmlと同階層に、{画像のインデックス}.jpegで保存
        file_name = str(i) + ".jpeg"
        # 画像保存
        # NOTE dcimgで保存されている場合はサムネのみ。
        relative_img_src = img.get("src")
        if relative_img_src and relative_img_src.startswith("/files"):
            img_src = "https://www.nogizaka46.com" + relative_img_src
            response = requests.get(img_src)
            with open(post_path + '/' + file_name, 'wb') as file:
                file.write(response.content)
            # html 書き換え
            img.attrs["src"] = file_name
        else: # 不明なパスの画像は無視。
            logger.warning("missing img src")


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

def main(url :str):
    while True:
        try :
            logger.info("Saving blog post: " + url)
            title, date, body = extract_post(url)
            logger.info("\ttitle: " + title)
            logger.info("\tdate: " + date)
            save_post(date, title, body)
            logger.debug("Saved!")
            url = get_previous_url(url)
            sleep(3)
        except Exception as e:
            logger.error(e)
            logger.info(f"Last successful URL : {url}")
            break

if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:
        url = DEFAULT_START_POST_URL
    else:
        url = args[1]
    main(url)
