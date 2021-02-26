from bs4 import BeautifulSoup, Doctype, element
import re
from datetime import datetime
from parser_base import ParserBase


class KYParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^CHAPTER', 'head2': '^CHAPTER', 'title': '^(TITLE)', 'sec_head': r'^([^\s]+[^\D]+)',
                            'junk': '^(Text)', 'ol': r'^(\(1\))', 'head4': '^(NOTES TO DECISIONS)'}
        self.title_id = None
        self.soup = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
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
        for junk_tag in self.soup.find_all():
            if junk_tag.get("class") == ['Apple-converted-space'] or junk_tag.name == "i":
                junk_tag.unwrap()
            elif junk_tag.get("class") == [self.junk_tag_class]:
                junk_tag.decompose()

        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["junk"])]
        for b_tag in self.soup.findAll("b"):
            b_tag.name = "span"
            b_tag["class"] = "boldspan"

        print('junk removed')

    # replace title tag to "h1" and wrap it with "nav" tag
    def set_appropriate_tag_name_and_id(self):
        cnav = 0
        snav = 0
        for header_tag in self.soup.body.find_all():
            if header_tag.get("class") == [self.class_regex["title"]]:
                header_tag.name = "h1"
                header_tag.wrap(self.soup.new_tag("nav"))
                self.title_id = re.search(r'^(TITLE)\s(?P<title_id>\w+)', header_tag.text.strip()).group('title_id')


            elif header_tag.get("class") == [self.class_regex["head2"]]:
                if re.search("^(CHAPTER)|^(Chapter)", header_tag.text):
                    chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)', header_tag.text.strip()).group('chapter_id').zfill(2)
                    header_tag.name = "h2"
                    header_tag['id'] = f"t{self.title_id}c{chap_nums}"
                else:
                    header_tag.name = "h3"
                    header_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                    chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)', header_tag.find_previous("h2").text.strip()).group('chapter_id').zfill(2)
                    header_tag["id"] = f"t{self.title_id}c{chap_nums}{header_id}"

            elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                header_tag.name = "h3"

                # sec_pattern = re.compile(r'^(\d+\.\d+\.)')
                if re.match(r'^(\d+\.\d+\.)', header_tag.text.strip()):
                    chap_num = re.search(r'^(\d+)', header_tag.text.strip()).group().zfill(2)
                    sec_num = re.search(r'^(\d+\.\d+)', header_tag.text.strip()).group().zfill(2)
                    header_pattern = re.search(r'^(\d+\.\d+)', header_tag.text.strip()).group()
                    if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]):
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
                    if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]):
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
                    if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]):
                        prev_tag = header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"])
                        if header_pattern in prev_tag.text.split()[0]:
                            count = 0
                            prev_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}-{count + 1}"
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}-{count + 2}"
                        else:
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

            elif header_tag.get("class") == [self.class_regex["ul"]]:
                header_tag.name = "li"

                if re.search("^(CHAPTER)|^(Chapter)", header_tag.text):
                    chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)', header_tag.text.strip()).group(
                        'chapter_id').zfill(2)
                    header_tag['id'] = f"t{self.title_id}c{chap_nums}-cnav{chap_nums}"

                else:
                    prev_chapter_id = header_tag.find_previous("h2").get("id")
                    if re.match(r'^(\d+\D*\.\d+)', header_tag.text.strip()):
                        sec_id = re.search(r'^(\d+\D*\.\d+)', header_tag.text.strip()).group()
                        chapter_id = re.search(r'^([^\.]+)', header_tag.text).group().zfill(2)
                        if header_tag.find_previous_sibling().name != "li":
                            snav = 0
                        snav = snav + 1
                        header_tag["id"] = f"{prev_chapter_id}s{sec_id}-snav{snav}"

                    else:
                        previous_tag = header_tag.find_previous().get("id")
                        if re.match(r'^(\d+\D*\.\d+)', header_tag.find_previous().text.strip()):
                            sec_id = re.search("(snav)(?P<id>\d+)", previous_tag.strip()).group("id").zfill(2)
                            sec_id =int(sec_id) + 1
                            section_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                            header_tag["id"] = f"{prev_chapter_id}s{section_id}-snav{sec_id}"

                        elif header_tag.find_previous().get("id"):
                            previous_tag_id = header_tag.find_previous().get("id")
                            sec_id = re.search("(snav)(?P<id>\d+)", previous_tag_id.strip()).group("id").zfill(2)
                            sec_id = int(sec_id) + 1
                            section_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                            header_tag["id"] = f"{prev_chapter_id}s{section_id}-snav{sec_id}"

                        else:
                            chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)',
                                                  header_tag.find_previous("h2").text.strip()).group(
                                'chapter_id').zfill(2)
                            section_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                            if re.match(r'^CHAPTER', header_tag.find_previous().text):
                                snav = 0
                            snav = snav + 1
                            header_tag["id"] = f"t{self.title_id}c{chap_nums}s{section_id}-snav{snav}"

            elif header_tag.get('class') == [self.class_regex["head4"]]:
                header_tag.name = "h4"
                prev_tag = header_tag.find_previous("h3")
                if prev_tag:
                    prev_tag_id = prev_tag.get("id")
                    header_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                    header_tag["id"] = f"{prev_tag_id}-{header_id}"
        print("tags are replaced")

    # wrap list items with ul tag
    def create_ul_tag(self):
        ul_tag = self.soup.new_tag("ul", **{"class":"leaders"})
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
            elif re.match(r'^CHAPTER|^Chapter', main_tag.text.strip()) and main_tag.get("class") == [
                self.class_regex["ul"]]:
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
            if re.match(r'^(CHAPTER)|^(Chapter)', list_item.text.strip()):
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
                    chap_num = re.search(r'^([^\.]+)', list_item.text.strip()).group().zfill(2)
                    sec_num = re.search(r'^(\d+\.\d+)', list_item.text.strip()).group(1).zfill(2)
                    sec_pattern = re.search(r'^(\d+\.\d+)', list_item.text.strip()).group()
                    sec_next_tag = list_item.find_next('li')
                    sec_prev_tag = list_item.find_previous("li")
                    sec_prev_tag_text = sec_prev_tag.a
                    if sec_next_tag:
                        if sec_pattern in sec_next_tag.text:
                            list_link = self.soup.new_tag('a')
                            list_link.string = list_item.text
                            list_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}-{count + 1}"
                            list_item.contents = [list_link]

                        elif sec_prev_tag_text:
                            if sec_pattern in sec_prev_tag.a.text:
                                list_link = self.soup.new_tag('a')
                                list_link.string = list_item.text
                                list_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}-{count + 2}"
                                list_item.contents = [list_link]

                            else:
                                nav_link = self.soup.new_tag('a')
                                nav_link.string = list_item.text
                                nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                                list_item.contents = [nav_link]
                    else:
                        nav_link = self.soup.new_tag('a')
                        nav_link.string = list_item.text
                        nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                        list_item.contents = [nav_link]

                elif re.match(r'^(\d+\D\.\d+)', list_item.text.strip()):
                    chap_num = re.search(r'^([^\.]+)', list_item.text.strip()).group().zfill(2)
                    sec_num = re.search(r'^(\d+\D\.\d+)', list_item.text.strip()).group().zfill(2)
                    nav_link = self.soup.new_tag('a')
                    nav_link.string = list_item.text
                    nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                    list_item.contents = [nav_link]

                else:
                    chapter_header = list_item.find_previous("h2")
                    chap_nums = re.search(r'(\s+[^\s]+)', chapter_header.text.strip()).group(0)
                    chap_num = re.sub(r'\s+', '', chap_nums).zfill(2)
                    sec_id = re.sub(r'\s+', '', list_item.get_text()).lower()
                    new_link = self.soup.new_tag('a')
                    new_link.string = list_item.text
                    new_link["href"] = f"#t{self.title_id}c{chap_num}{sec_id}"
                    list_item.contents = [new_link]

    # create ol tag for note to decision nav
    def create_ol_tag(self):
        new_ol_tag = self.soup.new_tag("ul")
        new_nav_tag = self.soup.new_tag("nav")

        for ol_tag in self.soup.find_all(class_=self.class_regex["ol"]):
            if re.match(r'^(\d+\.)', ol_tag.text.strip()) and ol_tag.find_previous(
                    "h4") is not None and ol_tag.find_previous("h4").text.strip() == 'NOTES TO DECISIONS':
                ol_tag.name = "li"
                if re.match(r'^(1\.)', ol_tag.text.strip()):
                    new_ol_tag = self.soup.new_tag("ul")
                    ol_tag.wrap(new_ol_tag)
                    new_ol_tag.wrap(self.soup.new_tag("nav"))

                else:
                    new_ol_tag.append(ol_tag)

    # add links to notes to decision nav
    def create_link_to_notetodecision_nav(self):
        for p_tag in self.soup.find_all(class_=self.class_regex["ol"]):
            if re.match(r'^(\d+\.)', p_tag.text.strip()) and p_tag.find_previous(
                    "h4") is not None and p_tag.find_previous("h4").text.strip() == 'NOTES TO DECISIONS':
                chap_num = re.search(r'^([^\.]+)', p_tag.find_previous("h3").text.strip()).group().zfill(2)
                sec_num = re.search(r'^(\d+\D*\.\d+)', p_tag.find_previous("h3").text.strip()).group()
                sub_sec_id = re.sub(r'\s+', '', p_tag.get_text()).lower()
                nav_list = []
                nav_link = self.soup.new_tag('a')
                # p_tag_text = re.sub(r'^(\d+\.\s)', '', p_tag.get_text().strip())
                nav_link.string = p_tag.text
                nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}-{sub_sec_id}"
                nav_list.append(nav_link)
                p_tag.contents = nav_list


    # wrapping with ol tag
    def wrap_with_ordered_tag(self):
        pattern = re.compile(r'^(\d+)|^([(]\d+[)]|^[(]\D[)])|^(\D\.)')
        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\(\D+\)')
        alp_pattern = re.compile(r'\(\D+\)')
        num_pattern = re.compile(r'^\d+\.')
        num_pattern1 = re.compile(r'^1\.')
        numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D+\)')
        alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')

        ol_tag2 = self.soup.new_tag("ol", type="a")
        ol_tag = self.soup.new_tag("ol")
        ol_tag3 = self.soup.new_tag("ol")
        ol_tag1 = self.soup.new_tag("ol")
        ol_tag4 = self.soup.new_tag("ol", type="a")

        for tag in self.soup.findAll("p", class_=self.class_regex["ol"]):
            if re.match(pattern, tag.text.strip()):
                tag.name = "li"


            # (1)
            if re.match(Num_bracket_pattern, tag.text.strip()):
                pattern1 = re.findall(r'^\(\d+\)', tag.text.strip())
                index = re.findall(r'\d+', str(pattern1))
                tag_strings = [str(integer) for integer in index]
                tag_string = "".join(tag_strings)
                tag_int = int(tag_string)

                if tag_int > 1:
                    ol_tag.append(tag)
                elif tag_int == 1:
                    ol_tag = self.soup.new_tag("ol")
                    tag.wrap(ol_tag)

            # (1)(a)
            if re.match(numAlpha_pattern, tag.text.strip()):
                ol_tag2 = self.soup.new_tag("ol", type="a")
                li_tag = self.soup.new_tag("li")
                li_tag.append(tag.text.strip())
                ol_tag2.append(li_tag)
                tag.contents = []
                tag.append(ol_tag2)

            # (a)
            pattern_new = re.compile(r'^\(a+\)')
            if re.match(alpha_pattern, tag.text.strip()):
                if re.match(pattern_new, tag.text.strip()):
                    ol_tag2 = self.soup.new_tag("ol", type="a")
                    tag.wrap(ol_tag2)
                    ol_tag.append(ol_tag2)
                    tag.find_previous("li").append(ol_tag2)

                else:
                    ol_tag2.append(tag)

            # 1
            if re.match(num_pattern, tag.text.strip()):
                if re.match(numAlpha_pattern, tag.find_previous().text.strip()):
                    ol_tag3 = self.soup.new_tag("ol")
                    tag.wrap(ol_tag3)
                    ol_tag.append(ol_tag3)
                    tag.find_previous("li").append(ol_tag3)
                elif re.match(num_pattern, tag.find_previous().text.strip()):

                    tag.find_previous("li").append(tag)

            # a
            if re.match(r'\D\.', tag.text.strip()):
                if re.match(r'a\.', tag.text.strip()):
                    ol_tag3 = self.soup.new_tag("ol")
                    tag.wrap(ol_tag3)
                    ol_tag.append(ol_tag3)
                    tag.find_previous("li").append(ol_tag3)
                else:
                    tag.find_previous("li").append(tag)

            # (4)(a)1.
            if re.match(r'\(\d+\)\s*\(\D\)\s*\d\.', tag.text.strip()):
                ol_tag4 = self.soup.new_tag("ol")
                li_tag = self.soup.new_tag("li")
                li_tag.append(tag.text.strip())
                ol_tag4.append(li_tag)
                tag.contents = []
                tag.append(ol_tag4)



            # # (a) 1.
            # if re.match(alphanum_pattern, tag.text.strip()):
            #     # print(tag.text)
            #     ol_tag3 = self.soup.new_tag("ol")
            #     li_tag = self.soup.new_tag("li")
            #     li_tag.append(tag.text.strip())
            #     ol_tag3.append(li_tag)
            #     ol_tag2.append(ol_tag3)
            #     tag.contents = []
            #     tag.append(ol_tag3)
            #
            # elif re.match(alpha_pattern, tag.text.strip()):
            #     tag.find_previous("li").append(tag)


            # a.
            # if re.match(r'\d+\.', tag.text.strip()) and tag.name == "li":
            #     if re.match(r'1\.', tag.text.strip()):
            #         ol_tag4 = self.soup.new_tag("ol")
            #
            #         ol_tag3 = self.soup.new_tag("ol")
            #         li_tag = self.soup.new_tag("li")
            #         li_tag.append(tag.text.strip())
            #         ol_tag3.append(li_tag)
            #         ol_tag2.append(ol_tag3)
            #         tag.contents = []
            #         tag.append(ol_tag)

            # elif re.match(num_pattern, tag.text.strip()):
            #     tag.find_previous("li").append(tag)

            # # # (1)(a)............
            # if re.match(numAlpha_pattern, tag.text.strip()):
            #     ol_tag2 = self.soup.new_tag("ol", type="a")
            #
            #     li_tag = self.soup.new_tag("li")
            #     li_tag.append(tag.text.strip())
            #     ol_tag2.append(li_tag)
            #     tag.contents = []
            #     tag.append(ol_tag2)



        # for tag in self.soup.findAll("li", class_=self.class_regex["ol"]):
        #     # # (1)......
        #     if re.match(Num_bracket_pattern, tag.text.strip()) is not None:
        #         print(tag)
            #     pattern1 = re.findall(r'^\(\d+\)', tag.text.strip())
            #     index = re.findall(r'\d+', str(pattern1))
            #     strings = [str(integer) for integer in index]
            #     a_string = "".join(strings)
            #     a_int = int(a_string)
            #
            #     if a_int > 1:
            #         ol_tag.append(tag)
            #     elif a_int == 1:
            #         ol_tag = self.soup.new_tag("ol")
            #         tag.wrap(ol_tag)

            # # (a).......
            # pattern_new = re.compile(r'^\(a+\)')
            # if re.match(alpha_pattern, tag.text.strip()):
            #     if re.match(pattern_new, tag.text.strip()):
            #
            #         ol_tag2 = self.soup.new_tag("ol", type="a")
            #         tag.wrap(ol_tag2)
            #         ol_tag.append(ol_tag2)
            #         tag.find_previous("li").append(ol_tag2)
            #
            #     else:
            #         ol_tag2.append(tag)
            #
            # # (1)(a)............
            # if re.match(numAlpha_pattern, tag.text.strip()):
            #     ol_tag2 = self.soup.new_tag("ol", type="a")
            #
            #     li_tag = self.soup.new_tag("li")
            #     li_tag.append(tag.text.strip())
            #     ol_tag2.append(li_tag)
            #     tag.contents = []
            #     tag.append(ol_tag2)
            #
            # elif re.match(alpha_pattern, tag.text.strip()):
            #     if re.match(Num_bracket_pattern, tag.find_previous().text.strip()):
            #         ol_tag2.append(tag)
            #     elif re.match(alpha_pattern, tag.find_previous().text.strip()):
            #         ol_tag2.append(tag)
            #     elif re.match(num_pattern, tag.find_previous().text.strip()):
            #         ol_tag2.append(tag)
            #
            # # (a)1..............
            # if re.match(alphanum_pattern, tag.text.strip()):
            #     ol_tag3 = self.soup.new_tag("ol")
            #     li_tag = self.soup.new_tag("li")
            #     li_tag.append(tag.text.strip())
            #     ol_tag3.append(li_tag)
            #     ol_tag2.append(ol_tag3)
            #     tag.contents = []
            #     tag.append(ol_tag3)
            #
            # elif re.match(num_pattern, tag.text.strip()) and re.match(alphanum_pattern,
            #                                                           tag.find_previous().text.strip()):
            #     ol_tag3.append(tag)
            #
            # # # 1.......
            # if re.match(num_pattern, tag.text.strip()):
            #     if re.match(num_pattern1, tag.text.strip()):
            #         ol_tag1 = self.soup.new_tag("ol")
            #         tag.wrap(ol_tag1)
            #         tag.find_previous("li").append(ol_tag1)
            #     else:
            #
            #         ol_tag1.append(tag)
            #
            # # a.......
            # pattern_a = re.compile(r'^(\D\.)')
            # if re.match(pattern_a, tag.text.strip()):
            #
            #     if re.match(r'^(a\.)', tag.text.strip()):
            #         ol_tag4 = self.soup.new_tag("ol", type="a")
            #         tag.wrap(ol_tag4)
            #         tag.find_previous("li").append(ol_tag4)
            #
            #     else:
            #         ol_tag4.append(tag)

        print("ol tag is wrapped")

    def write_soup_to_file(self):
        soup_str = str(self.soup.prettify(formatter=None))
        with open(f"../cic-code-ky/transforms/ky/ocky/r{self.release_number}/{self.html_file_name}", "w") as file:
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

        self.create_ol_tag()
        self.create_link_to_notetodecision_nav()

        self.wrap_with_ordered_tag()
        self.write_soup_to_file()
        print(datetime.now() - start_time)
