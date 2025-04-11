from lxml import etree
from io import StringIO
import requests
import re
import datetime
from bs4 import BeautifulSoup


def get_pwonlyias_questions_by_date():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }
    target_date = datetime.date(2025, 4, 10)
    # target_date = datetime.date.today()

    def extract_questions_with_tags(html_content, target_date):
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(html_content), parser)
        soup = BeautifulSoup(html_content, "html.parser")

        questions = []
        blocks = tree.xpath("//div[contains(@class, 'mains-border-box')]")
        soup_blocks = soup.find_all("div", class_="mains-border-box")

        for block, soup_block in zip(blocks, soup_blocks):
            # 1. Extract date
            date_elem = block.xpath(".//span/a[contains(@href, 'main-answer-writing-by-date')]")
            question_elem = block.xpath(".//h4[contains(@class, 'mains_notice_h4')]")

            if not date_elem or not question_elem:
                continue

            date_text = ''.join(date_elem[0].itertext()).strip()
            try:
                block_date = datetime.datetime.strptime(date_text, "%B %d, %Y").date()
            except ValueError:
                continue

            if block_date == target_date:
                # 2. Extract question text
                question_text = ''.join(question_elem[0].itertext()).strip()

                if re.search("[a-zA-Z]", question_text) and not re.search("[\u0900-\u097F]", question_text):
                    # 3. Extract tags from the BeautifulSoup block
                    tag_div = soup_block.find("div", class_="vc_cat_div")
                    tags = [a.text.strip() for a in tag_div.find_all("a", class_="tab-1")] if tag_div else []
                    tag_str = " | Tags: " + ", ".join(tags) if tags else ""
                    questions.append(question_text + tag_str)
        return questions

    url = "https://pwonlyias.com/mains-answer-writing/page/0"
    response = session.get(url, headers=headers)
    html_content = response.content.decode("utf-8")

    questions = extract_questions_with_tags(html_content, target_date)
    # write in a file
    with open("pwonlyias_questions.txt", "w", encoding="utf-8") as file:
        for question in questions:
            file.write(question + "\n")
    return questions

get_pwonlyias_questions_by_date()