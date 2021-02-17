from bs4 import BeautifulSoup
import re


# KY 2
class KyHtmlOperations:

    def __init__(self):
        self.class_regex = {'ul': '^CHAPTER', 'head2': '^CHAPTER', 'title': '^(TITLE)', 'sec_head': r'^([^\s]+[^\D]+)',
                            'junk': '^(Text)'}
        self.title_id = None
        self.soup = None

    # extract class names
    def get_class_names(self):
        for key, value in self.class_regex.items():
            tag_class = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.class_regex.get(key), tag.get_text().strip()) and
                            tag.attrs["class"][0] not in self.class_regex.values())
            self.class_regex[key] = tag_class.get('class')[0]
        # print(self.class_regex)

    # clear junk
    def clear_junk(self):
        [span.unwrap() if span["class"] == ['Apple-converted-space'] else span.decompose() for span in
         self.soup.findAll("span")]
        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["junk"])]
        for b_tag in self.soup.findAll("b"):
            b_tag.name = "span"
            b_tag["class"] = "Span.boldspan"

    # replace title tag to "h1" and wrap it with "nav" tag
    def set_appropriate_tag(self):
        for headers in self.soup.body.find_all():
            if headers.get("class") == [self.class_regex["title"]]:
                headers.name = "h1"
                self.title_id = re.search(r'^(?:[^ ]*\ ){1}([^ ]*)', headers.text).group(1)

            elif headers.get("class") == [self.class_regex["head2"]]:
                if re.match("(CHAPTER)", headers.text):
                    headers.name = "h2"
                    chap_nums = re.search(r'^(?:[^ ]*\ ){1}([^ ]*)', headers.text).group(1).zfill(2)
                    headers['id'] = f"t{self.title_id}c{chap_nums}"
                else:
                    headers.name = "h3"
                    headers["id"] = headers.text.replace(" ", "").lower()

            elif headers.get("class") == [self.class_regex["sec_head"]]:
                headers.name = "h3"

    # replace tags with li
    def convert_li(self):
        for section_item in self.soup.find_all("p", class_=self.class_regex["ul"]):
            section_item.name = "li"

    # assign id to section headers
    def sec_headers(self):
        for tag in self.soup.find_all(name="h3", class_=self.class_regex["sec_head"]):
            chap_num = re.search(r'^([^\.]+)', tag.text).group().zfill(2)
            sec_num = re.search(r'^([^\s]+[^\D]+)', tag.text).group(1).zfill(2)
            if tag.find_previous(name="h3", class_=self.class_regex["sec_head"]) is not None:
                current = re.search(r'^([^\s]+[^\D]+)', tag.text).group()
                prev_tag = tag.find_previous(name="h3", class_=self.class_regex["sec_head"])
                if current in prev_tag.text:
                    count = 0
                    prev_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}-{count + 1}"
                    tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}-{count + 2}"
                else:
                    tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

    def chap_sec_nav(self):
        pattern_sec = re.compile(r'^([^\s]+[^\D]+)')

        for tag in self.soup.find_all("li"):
            if re.match(r'^([^\s]+[^\D]+)|^(CHAPTER)', tag.get_text().strip()):
                if re.match(r'^(CHAPTER)', tag.text):
                    chap_nav_nums = re.findall(r'\d', tag.text)
                    chap_nums = re.search(r'\d', tag.text).group(0).zfill(2)
                    if chap_nav_nums:
                        new_list = []
                        new_link = self.soup.new_tag('a')
                        new_link.append(tag.text)
                        new_link["href"] = f"#t{self.title_id}c{chap_nums}"
                        new_list.append(new_link)
                        tag.contents = new_list
                else:
                    chap_num = re.search(r'^([^\.]+)', tag.text).group().zfill(2)
                    sec_num = re.search(r'^([^\s]+[^\D]+)', tag.text).group(1).zfill(2)
                    if tag.find_previous().name == "li":
                        current = re.search(r'^([^\s]+[^\D]+)', tag.text).group()

                        prev_tag = tag.find_previous()

                        if prev_tag.a and current in prev_tag.a.get_text():
                            print(tag)
                            count = 0
                            new_list = []
                            new_link = self.soup.new_tag('a')
                            new_link.string = tag.get_text()
                            new_link["href"] = f"#t{self.title_id}c0{chap_num}s{sec_num}-{count+2}"
                            new_list.append(new_link)
                            tag.contents = new_list
                            tag["id"] = f"t{self.title_id}c0{chap_num}s{sec_num}.snav0{chap_num[0]}-{count+2}"

                            new_list = []
                            new_link = self.soup.new_tag('a')
                            new_link.string = prev_tag.a.get_text()
                            new_link["href"] = f"#t{self.title_id}c0{chap_num}s{sec_num}-{count + 1}"
                            new_list.append(new_link)
                            tag.contents = new_list
                            tag["id"] = f"t{self.title_id}c0{chap_num}s{sec_num}.snav0{chap_num}-{count + 1}"

                        else:
                            new_list = []
                            new_link = self.soup.new_tag('a')
                            new_link.string = tag.get_text()
                            new_link["href"] = f"#t{self.title_id}c0{chap_num}s{sec_num}"
                            new_list.append(new_link)
                            tag.contents = new_list
                            tag["id"] = f"t{self.title_id}c0{chap_num}s{sec_num}.snav0{chap_num[0]}"
            else:
                sec_id = re.sub(r'\s+', '', tag.get_text()).lower()
                new_list = []
                new_link = self.soup.new_tag('a')
                new_link.string = tag.text
                new_link["href"] = f"#{sec_id}"
                new_list.append(new_link)
                tag.contents = new_list




            # else:
            #     print(tag)

        # pattern_sec = re.compile(r'^([^\s]+[^\D]+)')
        #
        # for tag in self.soup.find_all("li"):
        #     if re.match(r'^([^\s]+[^\D]+)|^(CHAPTER)', tag.get_text().strip()):
        #         if re.match(pattern_sec, tag.text):
        #             current = re.findall(r'^([^\s]+[^\D]+)', tag.text)
        #             next1 = re.findall(r'^([^\s]+[^\D]+)', tag.find_next().text)
        #
        #             chap_num = re.findall(r'^([^\.]+)', tag.text)
        #             sec_num = re.findall(r'^([^\s]+[^\D]+)', tag.text)
        #
        #             if current != [] and next1 != []:
        #                 if current[0] == next1[0]:
        #                     sub_sec = tag.text.replace(" ", "").lower()
        #                     new_list = []
        #                     new_link = self.soup.new_tag('a')
        #                     new_link.append(tag.text)
        #                     new_link["href"] = f"#t{self.title_id}c0{chap_num[0]}s{sub_sec}"
        #                     new_list.append(new_link)
        #                     tag.contents = new_list
        #                     tag["id"] = f"t{self.title_id}c0{chap_num[0]}s{sec_num[0]}.snav0{chap_num[0]}.{sub_sec}"
        #                 else:
        #                     new_list = []
        #                     new_link = self.soup.new_tag('a')
        #                     new_link.append(tag.text)
        #
        #                     new_link["href"] = f"#t{self.title_id}c0{chap_num[0]}s{sec_num[0]}"
        #                     new_list.append(new_link)
        #                     tag.contents = new_list
        #
        #                     # tag.attrs = {}
        #                     tag["id"] = f"t{self.title_id}c0{chap_num[0]}s{sec_num[0]}.snav0{chap_num[0]}"
        #             else:
        #                 new_list = []
        #                 new_link = self.soup.new_tag('a')
        #                 new_link.append(tag.text)
        #
        #                 new_link["href"] = f"#t{self.title_id}c0{chap_num[0]}s{sec_num[0]}"
        #                 new_list.append(new_link)
        #                 tag.contents = new_list
        #
        #                 # tag.attrs = {}
        #                 tag["id"] = f"t{self.title_id}c0{chap_num[0]}s{sec_num[0]}.snav0{chap_num[0]}"
        #
        #         else:
        #             chap_nav_nums = re.findall(r'\d', tag.text)
        #             chap_split = tag.text.split(' ')
        #             chap_nums = chap_split[1]
        #
        #             if chap_nav_nums:
        #                 new_list = []
        #                 new_link = self.soup.new_tag('a')
        #                 new_link.append(tag.text)
        #                 if chap_nums.isdigit():
        #                     if int(chap_nums) <= 9:
        #                         new_link["href"] = f"#t{self.title_id}c0{chap_nums}"
        #                     else:
        #                         new_link["href"] = f"#t{self.title_id}c{chap_nums}"
        #                 else:
        #                     new_link["href"] = f"#t{self.title_id}c{chap_nums}"
        #
        #                 new_list.append(new_link)
        #                 tag.contents = new_list
        #
        #     else:
        #         sec_id = tag.text.replace(" ", "").lower()
        #
        #         new_list = []
        #         new_link = self.soup.new_tag('a')
        #         new_link.append(tag.text)
        #         new_link["href"] = f"#{sec_id}"
        #         new_list.append(new_link)
        #         tag.contents = new_list

    # main method
    def start(self):
        self.create_soup()
        self.get_class_names()  # assign id to the li
        self.clear_junk()
        self.set_appropriate_tag()
        self.convert_li()
        self.sec_headers()
        self.chap_sec_nav()
        # self.new_section_head()
        self.write_into_soup()

    # create a soup
    def create_soup(self):
        with open("/home/mis/ky/gov.ky.krs.title.01.html") as fp:
            self.soup = BeautifulSoup(fp, "lxml")

    # write into a soup
    def write_into_soup(self):
        with open("ky1.html", "w") as file:
            file.write(str(self.soup))


KyHtmlOperations_obj = KyHtmlOperations()  # create a class object
KyHtmlOperations_obj.start()
