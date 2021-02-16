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
    # def section_header_id(self):
    #     [span.decompose() for span in self.soup.findAll() if span.name == "span"]
    #     [tag.unwrap() for tag in self.soup.findAll("b")]
    #     [junk.decompose() for junk in self.soup.findAll("p", class_="p5")]
    #     for sec_head in self.soup.findAll("p", class_="p4"):
    #         current = re.findall(r'^([^\s]+[^\D]+)', sec_head.text)
    #         next1 = re.findall(r'^([^\s]+[^\D]+)', sec_head.find_next("p", class_="p4").text)
    #
    #         print("current: " + current[0])
    #         print("next:    " + next1[0])

    # chap_num = re.findall(r'^([^\.]+)', sec_head.text)
    # sec_num = re.findall(r'^([^\s]+[^\D]+)', sec_head.text)
    #
    # if current != [] and next1 != []:
    #
    #     if current[0] == next1[0]:
    #         sec_head['id'] = f"t01c0{chap_num[0]}s{sec_num[0]}"
    #         sec_head.name = "h3"
    #     else:
    #         sec_head['id'] = f"t01c0{chap_num[0]}s{sec_num[0]}1"
    #         sec_head.name = "h3"

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
    def clear_junk(self):
        [span.decompose() for span in self.soup.main.findAll() if span.name == "span"]
        [junk.decompose() for junk in self.soup.main.findAll("p", class_="p5")]
        [tag.unwrap() for tag in self.soup.findAll("b")]

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

    # wrap the contents with ordered list(2)
    def wrap_with_ordered_list2(self):
        [br.decompose() for br in self.soup.findAll("p", class_="p7")]
        for tag in self.soup.findAll("p", class_="p8"):
            tag.name = "h4"

        pattern = re.compile(r'^(\d+)|^([(]\d+[)]|^[(]\D[)])')

        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\(\D+\)')
        # alp_pattern = re.compile(r'\(\D+\)')
        num_pattern = re.compile(r'^\d+')
        numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D+\)')
        alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')

        ol_tag2 = self.soup.new_tag("ol", type="a")
        ol_tag = self.soup.new_tag("ol")
        ol_tag3 = self.soup.new_tag("ol")

        for tag in self.soup.findAll("p", class_="p6"):
            if re.match(pattern, tag.text):
                tag.name = "li"
            else:
                tag.name = "h5"

        for tag in self.soup.findAll("li", class_="p6"):

            if re.match(Num_bracket_pattern, tag.text):

                pattern1 = re.findall(r'^\(\d+\)', tag.text)
                index = re.findall(r'\d+', str(pattern1))
                strings = [str(integer) for integer in index]
                a_string = "".join(strings)
                a_int = int(a_string)

                if a_int > 1:
                    #
                    # content = re.sub(r'^\(\d+\)', "", string=tag.text)
                    # tag.contents = []
                    # tag.append(content)

                    ol_tag.append(tag)
                elif a_int == 1:

                    # content = re.sub(r'^\(\d+\)', "", string=tag.text)
                    # tag.contents = []
                    # tag.append(content)

                    ol_tag = self.soup.new_tag("ol")
                    tag.wrap(ol_tag)

            if re.match(num_pattern, tag.text) and tag.find_previous().name == "h4":
                ol_tag = self.soup.new_tag("ol")
                tag.wrap(ol_tag)

                # content = re.sub(r'^\d+\.', "", string=tag.text)
                # tag.contents = []
                # tag.append(content)


            else:

                # content = re.sub(r'^\d+\.', "", string=tag.text)
                # tag.contents = []
                # tag.append(content)

                ol_tag.append(tag)

            pattern_new = re.compile(r'^\(a+\)')
            if re.match(alpha_pattern, tag.text):
                if re.match(pattern_new, tag.text):

                    ol_tag2 = self.soup.new_tag("ol", type="a")
                    tag.wrap(ol_tag2)
                    ol_tag.append(ol_tag2)
                    tag.find_previous("li").append(ol_tag2)

                    # content = re.sub(r'^\(\D+\)', "", string=tag.text)
                    # tag.contents = []
                    # tag.append(content)

                else:
                    # content = re.sub(r'^\(\D+\)', "", string=tag.text)
                    # tag.contents = []
                    # tag.append(content)

                    ol_tag2.append(tag)

            if re.match(numAlpha_pattern, tag.text):

                # print(tag)
                # print(re.sub(r'^\(\d+\)\s\(\D+\)', "", string=tag.text))
                # content = re.sub(r'^\(\d+\)\s\(\D+\)', "", string=tag.text)
                # tag.contents = []
                # tag.append(content)

                ol_tag2 = self.soup.new_tag("ol", type="a")

                li_tag = self.soup.new_tag("li")
                li_tag.append(tag.text)
                ol_tag2.append(li_tag)
                tag.contents = []
                tag.append(ol_tag2)

                # content = re.sub(r'^\(\d+\)\s\(\D+\)', "", string=tag.text)
                # tag.contents = []
                # tag.append(content)



            elif re.match(alpha_pattern, tag.text):

                # content = re.sub(r'^\(\d+\)\s\(\D+\)', "", string=tag.text)
                # tag.contents = []
                # tag.append(content)

                if re.match(Num_bracket_pattern, tag.find_previous().text):
                    ol_tag2.append(tag)
                elif re.match(alpha_pattern, tag.find_previous().text):
                    ol_tag2.append(tag)
                elif re.match(num_pattern, tag.find_previous().text):
                    ol_tag2.append(tag)

            if re.match(alphanum_pattern, tag.text):
                content = re.sub(r'^\(\D+\)\s(\d)+', "", string=tag.text)
                tag.contents = []
                tag.append(content)

                ol_tag3 = self.soup.new_tag("ol")
                li_tag = self.soup.new_tag("li")
                li_tag.append(tag.text)
                ol_tag3.append(li_tag)
                ol_tag2.append(ol_tag3)
                tag.contents = []
                tag.append(ol_tag3)


            elif re.match(num_pattern, tag.text) and re.match(alphanum_pattern, tag.find_previous().text):
                # content = re.sub(r'^\(\D+\)\s(\d)+', "", string=tag.text)
                # tag.contents = []
                # tag.append(content)

                ol_tag3.append(tag)

    # wrap section nav with a tag

    def section_nav2(self):
        pattern = re.compile(r'^([^\s]+[^\D]+)')

        for ch in self.soup.main.findAll():
            if ch.name == "li":
                if re.match(pattern, ch.text):

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
        self.clear_junk()
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
