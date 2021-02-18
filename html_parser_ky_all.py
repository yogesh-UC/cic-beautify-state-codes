from bs4 import BeautifulSoup
import re


# KY 2
class KyHtmlOperations:

    def __init__(self):
        self.class_regex = {'ul': '^CHAPTER', 'head2': '^CHAPTER', 'title': '^(TITLE)', 'sec_head': r'^([^\s]+[^\D]+)',
                            'junk': '^(Text)', 'ol': r'^(\d+)|^([(]\d+[)]|^[(]\D[)])'}
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
            b_tag["class"] = "boldspan"

    # replace title tag to "h1" and wrap it with "nav" tag
    def set_appropriate_tag_name(self):
        for header_tag in self.soup.body.find_all():
            if header_tag.get("class") == [self.class_regex["title"]]:
                header_tag.name = "h1"
                self.title_id = re.search(r'([^\s]+)', header_tag.text).group(1)
                print(self.title_id)

            elif header_tag.get("class") == [self.class_regex["head2"]]:
                if re.match("(CHAPTER)", header_tag.text):
                    header_tag.name = "h2"
                    chap_nums = re.search(r'^(?:[^ ]*\ ){1}([^ ]*)', header_tag.text).group(1).zfill(2)
                    header_tag['id'] = f"t{self.title_id}c{chap_nums}"
                else:
                    header_tag.name = "h3"
                    header_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                    header_tag["id"] = f"t{self.title_id}{header_id}"

            elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                header_tag.name = "h3"

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


    # wrap the main content

    def main_tag(self):
        section_nav_tag = self.soup.new_tag("main")
        for tags in self.soup.find_all(['p', 'h2', 'h3', 'li']):
            if tags.attrs["class"] == [self.class_regex["ul"]] and re.match(r'^(CHAPTER)', tags.text):
                continue
            else:
                tags.wrap(section_nav_tag)

    # wrap list items with ul tag
    def ul_tag(self):
        ul_tag = self.soup.new_tag("ul")
        for list_item in self.soup.find_all("li"):
            if list_item.find_previous().name == "li":
                ul_tag.append(list_item)
            else:
                ul_tag = self.soup.new_tag("ul")
                list_item.wrap(ul_tag)

    # link reference to sec nav
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
                        prev_tag = tag.find_previous("a")
                        if prev_tag and current in prev_tag.get_text():
                            print(tag)
                            count = 0
                            new_list = []
                            new_link = self.soup.new_tag('a')
                            new_link.string = tag.get_text()
                            new_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}-{count + 2}"
                            new_list.append(new_link)
                            tag.contents = new_list
                            tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}.snav{chap_num}-{count + 2}"

                            new_list = []
                            new_link = self.soup.new_tag('a')
                            new_link.string = tag.get_text()
                            new_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}-{count + 1}"
                            new_list.append(new_link)
                            tag.contents = new_list
                            tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}.snav{chap_num}-{count + 1}"

                        else:
                            new_list = []
                            new_link = self.soup.new_tag('a')
                            new_link.string = tag.get_text()
                            new_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                            new_list.append(new_link)
                            tag.contents = new_list
                            tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}.snav{chap_num}"
                    else:
                        count = 0
                        new_list = []
                        new_link = self.soup.new_tag('a')
                        new_link.string = tag.get_text()
                        new_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}-{count + 1}"
                        new_list.append(new_link)
                        tag.contents = new_list
                        tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}.snav{chap_num}-{count + 1}"

            else:
                sec_id = re.sub(r'\s+', '', tag.get_text()).lower()
                new_list = []
                new_link = self.soup.new_tag('a')
                new_link.string = tag.text
                new_link["href"] = f"#t{self.title_id}{sec_id}"
                new_list.append(new_link)
                tag.contents = new_list

    # wrap a content with ol tag
    def wrap_with_ordered_tag(self):
        pattern = re.compile(r'^(\d+)|^([(]\d+[)]|^[(]\D[)])')

        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\(\D+\)')
        # alp_pattern = re.compile(r'\(\D+\)')
        num_pattern = re.compile(r'^\d+')
        num_pattern1 = re.compile(r'^1')
        numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D+\)')
        alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')

        ol_tag2 = self.soup.new_tag("ol", type="a")
        ol_tag = self.soup.new_tag("ol")
        ol_tag3 = self.soup.new_tag("ol")

        for tag in self.soup.findAll("p", class_=self.class_regex["ol"]):
            if re.match(pattern, tag.text.strip()):
                tag.name = "li"

        for tag in self.soup.findAll("li", class_=self.class_regex["ol"]):

            # (1)......
            if re.match(Num_bracket_pattern, tag.text.strip()):
                pattern1 = re.findall(r'^\(\d+\)', tag.text.strip())
                index = re.findall(r'\d+', str(pattern1))
                strings = [str(integer) for integer in index]
                a_string = "".join(strings)
                a_int = int(a_string)

                if a_int > 1:
                    ol_tag.append(tag)
                elif a_int == 1:
                    ol_tag = self.soup.new_tag("ol")
                    tag.wrap(ol_tag)

            # 1.......
            if re.match(num_pattern, tag.text.strip()) and tag.find_previous().name == "span":
                ol_tag = self.soup.new_tag("ol")
                tag.wrap(ol_tag)
            else:
                ol_tag.append(tag)

            # (a).......
            pattern_new = re.compile(r'^\(a+\)')
            if re.match(alpha_pattern, tag.text.strip()):
                if re.match(pattern_new, tag.text.strip()):

                    ol_tag2 = self.soup.new_tag("ol", type="a")
                    tag.wrap(ol_tag2)
                    ol_tag.append(ol_tag2)
                    tag.find_previous("li").append(ol_tag2)

                else:
                    ol_tag2.append(tag)

            # (1)(a)............
            if re.match(numAlpha_pattern, tag.text.strip()):
                ol_tag2 = self.soup.new_tag("ol", type="a")

                li_tag = self.soup.new_tag("li")
                li_tag.append(tag.text.strip())
                ol_tag2.append(li_tag)
                tag.contents = []
                tag.append(ol_tag2)

            elif re.match(alpha_pattern, tag.text.strip()):
                if re.match(Num_bracket_pattern, tag.find_previous().text.strip()):
                    ol_tag2.append(tag)
                elif re.match(alpha_pattern, tag.find_previous().text.strip()):
                    ol_tag2.append(tag)
                elif re.match(num_pattern, tag.find_previous().text.strip()):
                    ol_tag2.append(tag)

            # (a)1. .............
            if re.match(alphanum_pattern, tag.text.strip()):

                ol_tag3 = self.soup.new_tag("ol")
                li_tag = self.soup.new_tag("li")
                li_tag.append(tag.text.strip())
                ol_tag3.append(li_tag)
                ol_tag2.append(ol_tag3)
                tag.contents = []
                tag.append(ol_tag3)

            elif re.match(num_pattern, tag.text.strip()) and re.match(alphanum_pattern, tag.find_previous().text.strip()):
                ol_tag3.append(tag)

    # main method
    def start(self):
        self.create_soup()
        self.Css_file()
        self.get_class_names()  # assign id to the li
        self.clear_junk()
        self.set_appropriate_tag_name()
        self.convert_li()
        self.sec_headers()
        self.main_tag()
        self.ul_tag()
        self.chap_sec_nav()
        self.wrap_with_ordered_tag()
        # self.wrap_with_ordered_list2()

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

    # add css file
    def Css_file(self):
        head = self.soup.find("head")
        css_link = self.soup.new_tag("link")
        css_link.attrs[
            "href"] = "https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css"
        css_link.attrs["rel"] = "stylesheet"
        css_link.attrs["type"] = "text/css"
        head.append(css_link)


KyHtmlOperations_obj = KyHtmlOperations()  # create a class object
KyHtmlOperations_obj.start()
