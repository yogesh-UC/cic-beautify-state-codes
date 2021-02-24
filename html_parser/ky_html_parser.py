from bs4 import BeautifulSoup, Doctype, element
import re
from datetime import datetime
from parser_base import ParserBase


class KYParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^CHAPTER', 'head2': '^CHAPTER', 'title': '^(TITLE)', 'sec_head': r'^([^\s]+[^\D]+)',
                            'junk': '^(Text)', 'ol': r'^(\d+)|^([(]\d+[)]|^[(]\D[)])', 'head4': '^(NOTES TO DECISIONS)',
                            }
        self.title_id = None
        self.soup = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        # self.junk_space_tag_class = ['Apple-converted-space']
        # self.junk_tab_tag_class = ['Apple-tab-span']
        self.html_file_name = input_file_name
        self.start_parse()

    def create_page_soup(self):

        with open(f'transforms/ky/ocky/r{self.release_number}/raw/{self.html_file_name}') as open_file:
            html_data = open_file.read()
        self.soup = BeautifulSoup(html_data, features="lxml")
        self.soup.contents[0].replace_with(Doctype("html"))
        self.soup.html.attrs['lang'] = 'en'
        print('created soup')

    def get_class_name(self):
        for key, value in self.class_regex.items():
            tag_class = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.class_regex.get(key), tag.get_text().strip()) and
                            tag.attrs["class"][0] not in self.class_regex.values())
            if tag_class:
                self.class_regex[key] = tag_class.get('class')[0]
        # print(self.class_regex)
        print('updated class dict')

    def remove_junk(self):
        junk_p_tags = self.soup.find_all(class_=self.junk_tag_class)
        for junk_tag in junk_p_tags:
            if junk_tag.get("class") == ['Apple-converted-space']:
                junk_tag.unwrap()
            else:
                junk_tag.decompose()

        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["junk"])]
        for b_tag in self.soup.findAll("b"):
            b_tag.name = "span"
            b_tag["class"] = "boldspan"
        print('junk removed')

    # replace title tag to "h1" and wrap it with "nav" tag
    def set_appropriate_tag_name_and_id(self):
        for header_tag in self.soup.body.find_all():
            if header_tag.get("class") == [self.class_regex["title"]]:
                header_tag.name = "h1"
                header_tag.wrap(self.soup.new_tag("nav"))
                title_id1 = re.search(r'(\s+[^\s]+)', header_tag.text.strip()).group(1)
                self.title_id = re.sub(r'\s+', '', title_id1)

            elif header_tag.get("class") == [self.class_regex["head2"]]:
                if re.search("^(CHAPTER)", header_tag.text):
                    chap_num = re.search(r'(\s+[^\s]+)', header_tag.text.strip()).group(1)
                    chap_nums = re.sub(r'\s+', '', chap_num).zfill(2)
                    header_tag.name = "h2"
                    header_tag['id'] = f"t{self.title_id}c{chap_nums}"
                else:
                    header_tag.name = "h3"
                    header_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                    header_tag["id"] = f"t{self.title_id}c{chap_nums}{header_id}"

            elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                header_tag.name = "h3"

                sec_pattern = re.compile(r'^(\d+\.\d+\.)')
                if re.match(sec_pattern, header_tag.text.strip()):
                    chap_num = re.search(r'^(\s*\d+)', header_tag.text).group().zfill(2)
                    sec_num = re.search(r'^(\s*\d+\.\d+)', header_tag.text).group().zfill(2)
                    header_pattern = re.search(r'^(\d+\.\d+)', header_tag.text.strip()).group()
                    if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]) is not None:
                        prev_tag = header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"])
                        if header_pattern not in prev_tag.text.split()[0]:
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"
                        else:
                            count = 0
                            prev_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}-{count + 1}"
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}-{count + 2}"

                    else:
                        header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

                elif re.match(r'^(\d+\D\.\d+)', header_tag.text):
                    chap_num = re.search(r'^([^\.]+)', header_tag.text).group().zfill(2)
                    sec_num = re.search(r'^(\d+\D\.\d+)', header_tag.text).group().zfill(2)
                    header_pattern = re.search(r'^(\d+\D\.\d+)', header_tag.text.strip()).group()
                    if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]) is not None:
                        prev_tag = header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"])
                        if header_pattern in prev_tag.text.split()[0]:
                            count = 0
                            prev_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}-{count + 1}"
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}-{count + 2}"
                        else:
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

                elif re.match(r'^(\d+\D\.\d+\-\d+)|^((\d+\.\d+\-\d+))', header_tag.text):
                    chap_num = re.search(r'^([^\.]+)', header_tag.text).group().zfill(2)
                    sec_num = re.search(r'^(\d+\D\.\d+\-\d+)|^((\d+\.\d+\-\d+))', header_tag.text).group().zfill(2)
                    header_pattern = re.search(r'^(\d+\D\.\d+\-\d+)|^((\d+\.\d+\-\d+))',
                                               header_tag.text.strip()).group()
                    if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]) is not None:
                        prev_tag = header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"])
                        if header_pattern in prev_tag.text.split()[0]:
                            count = 0
                            prev_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}-{count + 1}"
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}-{count + 2}"
                        else:
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

            elif header_tag.get("class") == [self.class_regex["ul"]]:
                header_tag.name = "li"

            elif header_tag.get('class') == [self.class_regex["head4"]]:
                header_tag.name = "h4"
                prev_tag = header_tag.find_previous("h3")
                if prev_tag is not None:
                    prev_tag_id = prev_tag.get("id")
                    header_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                    header_tag["id"] = f"{prev_tag_id}-{header_id}"
        print("tags are replaced")

    # wrap list items with ul tag
    def create_ul_tag(self):
        ul_tag = self.soup.new_tag("ul", class_="leaders")
        for list_item in self.soup.find_all("li"):
            if list_item.find_previous().name == "li":
                ul_tag.append(list_item)
            else:
                ul_tag = self.soup.new_tag("ul", class_="leaders")
                list_item.wrap(ul_tag)

        print("ul tag is created")

    # wrap the main content
    def create_main_tag(self):
        section_nav_tag = self.soup.new_tag("main")
        first_chapter_header = self.soup.find(class_=self.class_regex["head2"])
        for main_tag in self.soup.find_all("p"):
            if re.match(r'^(TITLE)', main_tag.text.strip()):
                continue
            elif re.match(r'^CHAPTER', main_tag.text.strip()) and main_tag.get("class") == [self.class_regex["ul"]]:
                continue
            elif main_tag == first_chapter_header:
                main_tag.wrap(section_nav_tag)
            else:
                section_nav_tag.append(main_tag)

        print("main tag is created")

    # create a reference
    def create_chap_sec_nav(self):
        count = 0
        for list_item in self.soup.find_all("li"):
            if re.match(r'^(CHAPTER)', list_item.text.strip()):
                chap_nav_nums = re.search(r'(\s+[^\s]+)', list_item.text.strip())
                chap_nums = re.search(r'(\s+[^\s]+)', list_item.text).group(0)
                chap_num = re.sub(r'\s+', '', chap_nums).zfill(2)
                if chap_nav_nums:
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(list_item.text)
                    nav_link["href"] = f"#t{self.title_id}c{chap_num}"
                    nav_list.append(nav_link)
                    list_item.contents = nav_list
            else:
                if re.match(r'^(\d+\.\d+)', list_item.text.strip()):
                    chap_num = re.search(r'^([^\.]+)', list_item.text).group().zfill(2)
                    sec_num = re.search(r'^(\d+\.\d+)', list_item.text).group(1).zfill(2)
                    sec_pattern = re.search(r'^(\d+\.\d+)', list_item.text.strip()).group()
                    sec_next_tag = list_item.find_next('li')
                    sec_prev_tag = list_item.find_previous("li")
                    sec_prev_tag_text = sec_prev_tag.a
                    if sec_next_tag is not None:
                        if sec_pattern in sec_next_tag.text:
                            new_list = []
                            list_link = self.soup.new_tag('a')
                            list_link.string = list_item.text
                            list_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}-{count + 1}"
                            new_list.append(list_link)
                            list_item.contents = new_list

                        elif sec_prev_tag_text is not None:
                            if sec_pattern in sec_prev_tag.a.text:
                                new_list = []
                                list_link = self.soup.new_tag('a')
                                list_link.string = list_item.text
                                list_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}-{count + 2}"
                                new_list.append(list_link)
                                list_item.contents = new_list

                            else:
                                nav_list = []
                                nav_link = self.soup.new_tag('a')
                                nav_link.string = list_item.text
                                nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                                nav_list.append(nav_link)
                                list_item.contents = nav_list
                    else:
                        nav_list = []
                        nav_link = self.soup.new_tag('a')
                        nav_link.string = list_item.text
                        nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                        nav_list.append(nav_link)
                        list_item.contents = nav_list

                elif re.match(r'^(\d+\D\.\d+)', list_item.text.strip()):
                    chap_num = re.search(r'^([^\.]+)', list_item.text).group().zfill(2)
                    sec_num = re.search(r'^(\d+\D\.\d+)', list_item.text).group(1).zfill(2)
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.string = list_item.text
                    nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                    nav_list.append(nav_link)
                    list_item.contents = nav_list

                else:
                    chapter_header = list_item.find_previous("h2")
                    chap_nums = re.search(r'(\s+[^\s]+)', chapter_header.text).group(0)
                    chap_num = re.sub(r'\s+', '', chap_nums).zfill(2)
                    sec_id = re.sub(r'\s+', '', list_item.get_text()).lower()
                    new_list = []
                    new_link = self.soup.new_tag('a')
                    new_link.string = list_item.text
                    new_link["href"] = f"#t{self.title_id}c{chap_num}{sec_id}"
                    new_list.append(new_link)
                    list_item.contents = new_list

    def write_soup_to_file(self):
        soup_str = str(self.soup.prettify(formatter=None))
        with open(f"transforms/ky/ocky/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str)

    # add css file
    def css_file(self):
        head = self.soup.find("head")
        style = self.soup.head.find("style")
        style.decompose()
        css_link = self.soup.new_tag("link")
        css_link.attrs[
            "href"] = "https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css"
        css_link.attrs["rel"] = "stylesheet"
        css_link.attrs["type"] = "text/css"
        head.append(css_link)

    def start_parse(self):
        self.release_label = f'Release-{self.release_number}'
        print(self.html_file_name)
        start_time = datetime.now()
        print(start_time)
        self.create_page_soup()
        self.css_file()
        self.get_class_name()
        self.remove_junk()
        self.create_main_tag()
        self.set_appropriate_tag_name_and_id()
        self.create_ul_tag()
        self.create_chap_sec_nav()
        self.write_soup_to_file()
        print(datetime.now() - start_time)
