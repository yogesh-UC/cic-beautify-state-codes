from bs4 import BeautifulSoup
import re


# KY 2
class KyHtmlOperations:
    # extract soup element
    def extract_soup_element(self, string):
            a = {'', 'head2': '^CHAPTER'}
            chap_element = self.soup.find(lambda tag: tag.name == 'p' and re.search('^CHAPTER', tag.get_text().strip()) and tag.attrs["class"][0] != "p2")
            print(chap_element)




    # replace title tag to "h1" and wrap it with "nav" tag
    def set_appropriate_tag(self):
        title_header = self.extract_soup_element("^(TITLE)")
        title_header.name = "h1"
        title_header.wrap(self.soup.new_tag("nav"))
        split_title = title_header.text.split(' ')
        self.title_id = split_title[1]

    # assign id to chapter header
    def chapter_header_id(self):
        chapter_header = self.soup.find(name="p", text=re.compile("^(CHAPTER)"))
        self.chapter_header_class = chapter_header["class"]

        for chap_head in self.soup.findAll("p", class_=self.chapter_header_class, text=re.compile("(CHAPTER)")):

            chap_head.name = "h2"
            chap_split = chap_head.text.split(' ')
            chap_nums = chap_split[1]

            if chap_nums.isdigit():
                if int(chap_nums) <= 9:
                    chap_head['id'] = f"t{self.title_id}c0{chap_nums}"

                else:
                    chap_head['id'] = f"t{self.title_id}c{chap_nums}"

            else:
                chap_head['id'] = f"t{self.title_id}c{chap_nums}"

    # replace tags with li
    def convert_li(self):
        [span.decompose() for span in self.soup.findAll() if span.name == "span"]
        section_header = self.soup.find(name="p", text=re.compile("^(CHAPTER)"))
        section_header_class = section_header["class"]

        for section_item in self.soup.find_all("p", class_=section_header_class):
            section_item.name = "li"

    # wrap section nav with a tag
    def section_nav2(self):
        pattern_sec = re.compile(r'^([^\s]+[^\D]+)')
        pattern_chap = re.compile(r'^(CHAPTER)')

        for ch in self.soup.findAll():
            if ch.name == "li":
                if re.match(pattern_sec, ch.text):
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
                    else:
                        new_list = []
                        new_link = self.soup.new_tag('a')
                        new_link.append(ch.text)

                        new_link["href"] = f"#t01c0{chap_num[0]}s{sec_num[0]}"
                        new_list.append(new_link)
                        ch.contents = new_list

                        ch.attrs = {}
                        ch["id"] = f"t01c0{chap_num[0]}s{sec_num[0]}.snav0{chap_num[0]}"

                elif re.match(pattern_chap, ch.text):
                    chap_nav_nums = re.findall(r'\d', ch.text)
                    if chap_nav_nums:
                        new_list = []
                        new_link = self.soup.new_tag('a')
                        new_link.append(ch.text)
                        new_link["href"] = f"#t01c0{chap_nav_nums[0]}"
                        new_list.append(new_link)
                        ch.contents = new_list

                elif ch.find_previous().name == "li":
                    new_list = []
                    new_link = self.soup.new_tag('a')
                    new_link.append(ch.text)
                    # new_link["href"] = f"#t01c0{chap_nav_nums[0]}"
                    new_list.append(new_link)
                    ch.contents = new_list

    # main method
    def start(self):
        self.create_soup()

        self.extract_soup_element("^(CHAPTER)")
        # self.set_appropriate_tag()
        # self.chapter_header_id()
        #
        # self.convert_li()

        # self.assign_id()
        # self.set_ul_tag()

        # self.section_header_id()

        # self.chapter_nav_id()
        # self.chapter_nav()
        # self.main_tag()
        # self.section_nav()
        # self.clear_junk()
        # self.div_tag()
        # # self.section_nav1()
        # self.section_nav2()
        # self.wrap_with_ordered_list2()

        self.write_into_soup()

    # create a soup
    def create_soup(self):
        with open("/home/mis/ky/gov.ky.krs.title.03.html") as fp:
            self.soup = BeautifulSoup(fp, "lxml")

    # write into a soup
    def write_into_soup(self):
        with open("ky3.html", "w") as file:
            file.write(str(self.soup))


KyHtmlOperations_obj = KyHtmlOperations()  # create a class object
KyHtmlOperations_obj.start()
