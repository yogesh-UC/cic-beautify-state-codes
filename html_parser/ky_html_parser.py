from bs4 import BeautifulSoup
import re

class KyHtmlOperations:
    def chapter_header_id(self):
        all_chapter_header = soup.findAll("p", class_="p3")
        for chap_head in all_chapter_header:
            chap_nums = re.findall(r'\d', chap_head.text)
            chap_id = "".join(chap_nums)
            chap_head['id'] = f"t01c0{chap_id}."


with open("gov.ky.krs.title.01.html") as fp:
    soup = BeautifulSoup(fp, "lxml")

KyHtmlOperations_obj = KyHtmlOperations()  # create a class object

with open("ky.html", "w") as file:
    file.write(str(soup))
