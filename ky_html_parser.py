from bs4 import BeautifulSoup
import re

class KyHtmlOperations:
    # assign id to chapter header
    def chapter_header_id(self, soup):
        all_chapter_header = soup.findAll("p", class_="p3")
        for chap_head in all_chapter_header:
            chap_nums = re.findall(r'\d', chap_head.text)
            chap_id = "".join(chap_nums)
            chap_head['id'] = f"t01c0{chap_id}"

    # assign id to Section header
    def section_header_id(self, soup):
        all_section_header = soup.findAll("p", class_="p4")
        for sec_head in all_section_header:
            chap_num = re.findall(r'^([^\.]+)', sec_head.text)
            chap_id = "".join(chap_num)
            sec_num = re.findall(r'^([^\s]+)', sec_head.text)
            sec_id = "".join(sec_num)
            sec_head['id'] = f"t01c0{chap_id}s{sec_id}"

    # replace with appropriate tag
    def set_appropriate_tag(self, soup):
        title_header = soup.find(name="p", text=re.compile("^(TITLE)"))
        title_header.name = "h1"
        title_header.wrap(soup.new_tag("nav"))

    # add <a> tag
    def set_link(self, soup):
        chapter_nav = soup.findAll("p", class_="p2")
        count = 0
        ul_tag = soup.new_tag("ul", class_="leaders")
        while count < 3:
            chapter_nav_list = chapter_nav.pop(0)
            chapter_nav_list.wrap(ul_tag)
            chapter_nav.append(chapter_nav_list)
            count = count + 1

        head_list_item = soup.ul.find_all("p")
        for list_item in head_list_item:
            list_item.name = "li"

        nav_item = soup.find("nav")
        ul_item = soup.find("ul")
        nav_item.append(ul_item)

    # Assign id to chapter nav items
    def chapter_nav_id(self,soup):
        self.set_link(soup)
        chapter_nav_items = soup.findAll("li")
        for chapter_nav_item in chapter_nav_items:
            chap_nav_nums = re.findall(r'\d', chapter_nav_item.text)
            print(chap_nav_nums)
            chap_nav_id = "".join(chap_nav_nums)
            chapter_nav_item['id'] = f"t01c0{chap_nav_id}-cnav0{chap_nav_id}"



with open("/home/mis/gov.ky.krs.title.01.html") as fp:
    soup = BeautifulSoup(fp, "lxml")

KyHtmlOperations_obj = KyHtmlOperations()  # create a class object
KyHtmlOperations_obj.chapter_header_id(soup)
KyHtmlOperations_obj.section_header_id(soup)
KyHtmlOperations_obj.set_appropriate_tag(soup)
#KyHtmlOperations_obj. set_link(soup)
KyHtmlOperations_obj.chapter_nav_id(soup)

with open("ky.html", "w") as file:
    file.write(str(soup))
