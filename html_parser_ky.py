from bs4 import BeautifulSoup
import re


# KY 2
class KyHtmlOperations:
    # assign id to chapter header
    def chapter_header_id(self):
        for chap_head in self.soup.findAll("p", class_="p3"):
            chap_nums = re.findall(r'\d', chap_head.text)
            if chap_nums:
                chap_head['id'] = f"t01c0{chap_nums[0]}"
                chap_head.name = "h2"

    # # assign id to Section header
    def section_header_id(self):
        for sec_head in self.soup.findAll("p", class_="p4"):
            chap_num = re.findall(r'^([^\.]+)', sec_head.text)
            sec_num = re.findall(r'^([^\s]+)', sec_head.text)
            sec_head['id'] = f"t01c0{chap_num[0]}s{sec_num[0]}"
            sec_head.name = "h3"

    # assign id to Section header
    def section_header_id(self):
        [span.decompose() for span in self.soup.findAll() if span.name == "span"]
        [tag.unwrap() for tag in self.soup.findAll("b")]
        [junk.decompose() for junk in self.soup.findAll("p", class_="p5")]
        for sec_head in self.soup.findAll("p", class_="p4"):
            current = re.findall(r'^([^\s]+[^\D]+)', sec_head.text)
            next1 = re.findall(r'^([^\s]+[^\D]+)', sec_head.find_next("p", class_="p4").text)

            print("current: " + current[0])
            print("next:    " + next1[0])

        chap_num = re.findall(r'^([^\.]+)', sec_head.text)
        sec_num = re.findall(r'^([^\s]+[^\D]+)', sec_head.text)

        if current != [] and next1 != []:

            if current[0] == next1[0]:
                sec_head['id'] = f"t01c0{chap_num[0]}s{sec_num[0]}"
                sec_head.name = "h3"
            else:
                sec_head['id'] = f"t01c0{chap_num[0]}s{sec_num[0]}1"
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
                break  # break from all p after p3

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

    # wrap section   with li tag
    def section_nav(self):
        for tag in self.soup.findAll("p", class_="p2"):
            tag.name = "li"

    # clear junk
    # def clear_junk(self):
    #     [span.decompose() for span in self.soup.main.findAll() if span.name == "span"]
    #     [junk.decompose() for junk in self.soup.main.findAll("p", class_="p5")]
    #     [tag.unwrap() for tag in self.soup.findAll("b")]

    # wrap section nav with ul
    def div_tag(self):
        [ch.wrap(self.soup.new_tag("div")) for ch in self.soup.main.findAll() if ch.name == "h2"]
        nav_tag = self.soup.new_tag("nav")
        ul_tag = self.soup.new_tag("ul", class_="leaders")
        for ch in self.soup.main.findAll():
            if ch.name == "li":
                if ch.find_previous().name == "li":
                    nav_tag.append(ch)
                    ul_tag.append(ch)

                else:
                    nav_tag = self.soup.new_tag("nav")
                    ul_tag = self.soup.new_tag("ul", class_="leaders")
                    ch.wrap(nav_tag)
                    ch.wrap(ul_tag)

    # wrap the contents with ordered list
    def wrap_with_ordered_list1(self):
        for tag in self.soup.findAll("p", class_="p8"):
            tag.name = "h4"

        pattern2 = re.compile(r'^[(]\D[)]')
        pattern = re.compile(r'^(\d+)|^([(]\d+[)])')
        ol_tag = self.soup.new_tag("ol")
        ol_tag2 = self.soup.new_tag("ol", type="a")
        for tag in self.soup.findAll("p", class_="p6"):
            if re.match(pattern, tag.text):
                tag.name = "li"

        for tag in self.soup.findAll(["li", "p"], class_="p6"):
            if re.match(pattern, tag.text):
                if tag.name == "li":
                    if tag.find_previous().name == "li" or tag.find_previous().name == "p":
                        ol_tag.append(tag)
                    else:
                        ol_tag = self.soup.new_tag("ol")
                        tag.wrap(ol_tag)

            elif re.match(pattern2, tag.text):
                if tag.name == "p":
                    if tag.find_previous().name == "p":
                        ol_tag2.append(tag)
                    elif tag.find_previous().name == "li":
                        ol_tag2 = self.soup.new_tag("ol", type="a")
                        tag.wrap(ol_tag2)
                        ol_tag.append(ol_tag2)

        for ol in self.soup.findAll("p", class_="p6"):
            if re.match(pattern2, ol.text):
                ol.name = "li"

    # wrap the contents with ordered list(2)
    def wrap_with_ordered_list2(self):
        [br.decompose() for br in self.soup.findAll("p", class_="p7")]
        for tag in self.soup.findAll("p", class_="p8"):
            tag.name = "h4"

        pattern4 = re.compile(r'^([(]\d+[)])')  # (1)
        pattern3 = re.compile(r'^(\d+)')  # 1.
        pattern2 = re.compile(r'^[(]\D[)]')  # (a)
        pattern1 = re.compile(r'^(\d+)|^([(]\d+[)])')  # (1) 1.
        pattern = re.compile(r'^(\d+)|^([(]\d+[)]|^[(]\D[)])')
        pattern5 = re.compile(r'^([(]\d+[)]) [(]\D[)]')

        ol_tag = self.soup.new_tag("ol")
        ol_tag2 = self.soup.new_tag("ol")
        for tag in self.soup.findAll("p", class_="p6"):
            if re.match(pattern, tag.text):
                tag.name = "li"
            else:
                tag.name = "h5"

        ol_tag2 = self.soup.new_tag("ol")
        ol_tag = self.soup.new_tag("ol")
        for tag in self.soup.findAll("li", class_="p6"):
            if tag.find_previous().name == "li":
                if re.match(pattern4, tag.text):
                    if re.match(pattern4, tag.find_previous().text):
                        ol_tag.append(tag)

                    else:
                        ol_tag = self.soup.new_tag("ol")
                        tag.wrap(ol_tag)

                # elif re.match(pattern5, tag.text):
                #     ol_tag2 = self.soup.new_tag("ol")
                #     tag.wrap(ol_tag2)
                #     #ol_tag.append(ol_tag2)
                # elif re.match(pattern2, tag.text):
                #     ol_tag2.append(tag)






            elif tag.find_previous().name == "h3" or tag.find_previous().name == "h5" or tag.find_previous().name == "h4":
                ol_tag = self.soup.new_tag("ol")
                tag.wrap(ol_tag)

        # i=0
        # for tag in self.soup.findAll("li", class_="p6"):
        #     current =
        #     if re.match(f"^([(]{i+1}[)])", tag.text):
        #         print(tag)

        # title_header = soup.find(name="p", text=re.compile("^(TITLE)"))

    # # wrap section nav with a tag
    # def section_nav1(self):
    #     pattern = re.compile(r'^([^\s]+[^\D]+)')
    #
    #     for ch in self.soup.main.findAll():
    #         if ch.name == "li":
    #             if re.match(pattern, ch.text):
    #                 chap_num = re.findall(r'^([^\.]+)', ch.text)
    #                 sec_num = re.findall(r'^([^\s]+[^\D]+)', ch.text)
    #
    #                 new_list = []
    #                 new_link = self.soup.new_tag('a')
    #                 new_link.append(ch.text)
    #
    #                 new_link["href"] = f"#t01c0{chap_num[0]}s{sec_num[0]}."
    #                 new_list.append(new_link)
    #                 ch.contents = new_list
    #
    #                 ch.attrs = {}
    #                 ch["id"] = f"t01c0{chap_num[0]}s{sec_num[0]}.snav0{chap_num[0]}"

    # wrap section nav with a tag

    def section_nav2(self):
        pattern = re.compile(r'^([^\s]+[^\D]+)')

        for ch in self.soup.main.findAll():
            if ch.name == "li":
                if re.match(pattern, ch.text):
                    # print(ch.find_next().text)

                    current_text = ch.text
                    next_text = ch.find_next().text

                    current = re.findall(r'^([^\s]+[^\D]+)', ch.text)
                    next1 = re.findall(r'^([^\s]+[^\D]+)', ch.find_next().text)

                    chap_num = re.findall(r'^([^\.]+)', ch.text)
                    sec_num = re.findall(r'^([^\s]+[^\D]+)', ch.text)

                    if current != [] and next1 != []:

                        if current[0] == next1[0]:

                            new_list = []
                            new_link = self.soup.new_tag('a')
                            new_link.append(ch.text)

                            new_link["href"] = f"#t01c0{chap_num[0]}s{sec_num[0]}.1"
                            new_list.append(new_link)
                            ch.contents = new_list

                            ch.attrs = {}
                            ch["id"] = f"t01c0{chap_num[0]}s{sec_num[0]}.snav0{chap_num[0]}.1"

                        else:
                            new_list = []
                            new_link = self.soup.new_tag('a')
                            new_link.append(ch.text)

                            new_link["href"] = f"#t01c0{chap_num[0]}s{sec_num[0]}"
                            new_list.append(new_link)
                            ch.contents = new_list

                            ch.attrs = {}
                            ch["id"] = f"t01c0{chap_num[0]}s{sec_num[0]}.snav0{chap_num[0]}"

    # assign id
    def assign_id(self):
        [span.decompose() for span in self.soup.findAll() if span.name == "span"]
        [tag.unwrap() for tag in self.soup.findAll("b")]
        [junk.decompose() for junk in self.soup.findAll("p", class_="p5")]

        pattern = re.compile(r'^([^\s]+[^\D]+)')
        pattern1 = re.compile(r'\D')

        # for sec_head in self.soup.findAll("p", class_="p4"):
        #     print(sec_head)
        # chap_num = re.findall(r'^([^\.]+)', sec_head.text)
        # sec_num = re.findall(r'^([^\s]+)', sec_head.text)
        # sec_head['id'] = f"t01c0{chap_num[0]}s{sec_num[0]}"
        # sec_head.name = "h3"

    # main method
    def start(self):
        self.create_soup()

        # self.assign_id()
        self.set_ul_tag()
        self.chapter_header_id()
        self.section_header_id()
        self.set_appropriate_tag()
        self.chapter_nav_id()
        self.chapter_nav()
        self.main_tag()
        self.section_nav()
        # self.clear_junk()
        self.div_tag()
        # self.section_nav1()
        self.section_nav2()
        self.wrap_with_ordered_list2()

        self.write_into_soup()

    # create a soup
    def create_soup(self):
        with open("/home/mis/gov.ky.krs.title.02.html") as fp:
            self.soup = BeautifulSoup(fp, "lxml")

    # write into a soup
    def write_into_soup(self):
        with open("ky2.html", "w") as file:
            file.write(str(self.soup))


KyHtmlOperations_obj = KyHtmlOperations()  # create a class object
KyHtmlOperations_obj.start()
