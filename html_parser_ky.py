from bs4 import BeautifulSoup
import re


class KyHtmlOperations:
    # assign id to chapter header
    def chapter_header_id(self):
        for chap_head in self.soup.findAll("p", class_="p3"):
            chap_nums = re.findall(r'\d', chap_head.text)
            if chap_nums:
                chap_head['id'] = f"t01c0{chap_nums[0]}"
                chap_head.name = "h2"

    # assign id to Section header
    def section_header_id(self):
        for sec_head in self.soup.findAll("p", class_="p4"):
            chap_num = re.findall(r'^([^\.]+)', sec_head.text)
            sec_num = re.findall(r'^([^\s]+)', sec_head.text)
            sec_head['id'] = f"t01c0{chap_num[0]}s{sec_num[0]}"
            sec_head.name = "h3"

    # replace with appropriate tag
    def set_appropriate_tag(self):
        title_header = self.soup.find(name="p", text=re.compile("^(TITLE)"))
        title_header.name = "h1"
        title_header.wrap(self.soup.new_tag("nav"))

    # set as  list items  and wrap it with ul tag
    def set_ul_tag(self):
        ul_tag = self.soup.new_tag("ul", **{'class': 'leaders'})
        for nav in self.soup.findAll("p"):
            if nav != self.soup.find("p", class_="p3"):
                if nav["class"] != ['p1']:
                    nav.wrap(ul_tag)
                    nav.name = "li"
            else:
                break  # break from all p after n

    # Assign id to chapter nav items
    def chapter_nav_id(self):
        for chapter_nav_item in self.soup.findAll("li"):
            chapter_nav_item.attrs = {}
            chap_nav_nums = re.findall(r'\d', chapter_nav_item.text)
            if chap_nav_nums:
                chapter_nav_item['id'] = f"t01c0{chap_nav_nums[0]}-cnav0{chap_nav_nums[0]}"
            self.soup.find("nav").append(self.soup.find("ul", class_="leaders"))

    # wrap chapter nav items with anchor tag
    def chapter_nav(self):
        for nav_head in self.soup.find_all("li"):
            chap_nav_nums = re.findall(r'\d', nav_head.text)
            if chap_nav_nums:
                new_list = []
                new_link = self.soup.new_tag('a')
                new_link.append(nav_head.text)
                new_link["href"] = f"#t01c0{chap_nav_nums[0]}"
                new_list.append(new_link)
                nav_head.contents = new_list

    # wrap the main content
    def main_tag(self):
        section_nav_tag = self.soup.new_tag("main")
        [tags.wrap(section_nav_tag) for tags in self.soup.find_all(['p', 'h2', 'h3'])]

    # wrap section   with nav tag
    def section_nav(self):
        for tag in self.soup.findAll("p", class_="p2"):
            tag.name = "li"

    # wrap div
    def div_tag(self):
        [span.decompose() for span in self.soup.main.findAll() if span.name == "span"]
        [ch.wrap(self.soup.new_tag("div")) for ch in self.soup.main.findAll() if ch.name == "h2"]
        ul_tag = self.soup.new_tag("ul")
        for ch in self.soup.main.findAll():
            if ch.name == "li":
                if ch.find_previous().name == "li":
                    print(ch)
                    ul_tag.append(ch)
                else:
                    ul_tag = self.soup.new_tag("ul")
                    ch.wrap(ul_tag)



    # main class
    def start(self):
        self.create_soup()
        self.set_ul_tag()
        self.chapter_header_id()
        self.section_header_id()
        self.set_appropriate_tag()
        self.chapter_nav_id()
        self.chapter_nav()
        self.main_tag()
        self.section_nav()
        self.div_tag()

        self.write_into_soup()

    # create a soup
    def create_soup(self):
        with open("/home/mis/gov.ky.krs.title.01.html") as fp:
            self.soup = BeautifulSoup(fp, "lxml")

    # write into a soup
    def write_into_soup(self):
        with open("ky.html", "w") as file:
            file.write(str(self.soup))


KyHtmlOperations_obj = KyHtmlOperations()  # create a class object
KyHtmlOperations_obj.start()
