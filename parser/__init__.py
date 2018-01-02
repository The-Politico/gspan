#!/usr/bin/env python

import html2text
import re

from copydoc import CopyDoc


class TranscriptParser:
    """
    Cleans Google Doc HTML, then converts into JSON
    """

    def __init__(self, html_string):
        self.end_transcript_regex = re.compile(
            r'.*LIVE\sTRANSCRIPT\sHAS\sENDED.*',
            re.UNICODE
        )
        self.do_not_write_regex = re.compile(
            r'.*DO\s*NOT\s*WRITE\s*BELOW\s*THIS\s*LINE.*',
            re.UNICODE
        )
        self.end_fact_check_regex = re.compile(
            r'^\s*[Ee][Nn][Dd]\s*$',
            re.UNICODE
        )
        self.anno_start_marker_regex = re.compile(
            r'^\s*\+{50,}\s*$',
            re.UNICODE
        )
        self.anno_end_marker_regex = re.compile(
            r'^\s*-{50,}\s*$',
            re.UNICODE
        )
        self.frontmatter_marker_regex = re.compile(
            r'^\s*-{3}\s*$',
            re.UNICODE
        )
        self.extract_metadata_regex = re.compile(
            r'^(.*?):(.*)$',
            re.UNICODE
        )

        self.speaker_regex = re.compile(
            r'^[A-Z\s.-]+(\s\[.*\])?:',
            re.UNICODE
        )
        self.soundbite_regex = re.compile(
            r'^\s*:',
            re.UNICODE
        )
        self.extract_speaker_metadata_regex = re.compile(
            r'^\s*(<.*?>)?([A-Z0-9\s.-]+)\s*(?:\[(.*)\]\s*)?:\s*(.*)',
            re.UNICODE
        )
        self.extract_soundbite_metadata_regex = re.compile(
            r'^\s*(?:<.*?>)?\s*:\[\((.*)\)\]',
            re.UNICODE
        )
        self.extract_author_metadata_regex = re.compile(
            r'^.*\((.+)\)\s*$',
            re.UNICODE
        )

        self.doc = CopyDoc(html_string)
        self.parse()

    def parse(self):
        """
        Parse all the annotation-specific content
        """
        self.remove_administrivia(self.doc.soup)
        raw = self.separate_components(self.doc.soup)
        contents = self.parse_raw_contents(raw)
        print(contents)

    def remove_administrivia(self, soup):
        hr = soup.hr

        if hr:
            if hr.find('p', text=self.end_fact_check_regex):
                hr.extract()
            elif hr.find('p', text=self.end_transcript_regex):
                hr.extract()
            else:
                for child in hr.children:
                    if (child.string):
                        after_hr_text = child.string
                    else:
                        after_hr_text = child.get_text()
                    m = self.do_not_write_regex.match(after_hr_text)
                    if m:
                        child.extract()
                hr.unwrap()

    def separate_components(self, soup):
        result = []
        body = soup.body
        inside_annotation = False
        annotation_contents = []
        for child in body.children:
            if self.is_anno_start_marker(child):
                inside_annotation = True
                annotation_contents = []
            elif self.is_anno_end_marker(child):
                inside_annotation = False
                result.append({
                    'type': 'annotation',
                    'contents': annotation_contents
                })
            else:
                if inside_annotation:
                    annotation_contents.append(child)
                else:
                    result.append({
                        'type': 'transcript',
                        'content': child
                    })

        return result

    def parse_raw_contents(self, data):
        """
        parse transcript and annotation objects
        """
        contents = []
        for p in data:
            if p['type'] == 'annotation':
                annotation = {}
                marker_counter = 0
                raw_metadata = []
                raw_contents = []
                for tag in p['contents']:
                    text = tag.get_text()
                    m = self.frontmatter_marker_regex.match(text)
                    if m:
                        marker_counter += 1
                    else:
                        if not marker_counter:
                            continue
                        if marker_counter == 1:
                            raw_metadata.append(tag)
                        else:
                            raw_contents.append(tag)
                metadata = self.process_metadata(raw_metadata)

                for k, v in metadata.items():
                    annotation[k] = v

                annotation['contents'] = self.process_annotation_contents(
                    raw_contents
                )
                annotation['type'] = 'annotation'
                contents.append(annotation)
            else:
                transcript = {}
                typ, context = self.process_transcript_content(
                    p['content']
                )
                transcript['type'] = typ
                transcript['context'] = context
                transcript['published'] = True
                contents.append(transcript)

        return contents

    def process_annotation_contents(self, contents):
        """
        Process post copy content
        In particular parse and generate HTML from shortcodes
        """
        parsed = [str(tag) for tag in contents]
        post_contents = ''.join(parsed)
        markdown = self.convert_to_markdown(post_contents)

        return markdown

    def process_metadata(self, contents):
        metadata = {}
        for tag in contents:
            text = tag.get_text()
            m = self.extract_metadata_regex.match(text)
            if m:
                key = m.group(1).strip().lower()
                value = m.group(2).strip()
                if key == 'published':
                    value = True if value == 'Yes' else False
                metadata[key] = value
            else:
                print('Could not parse metadata. Text: %s' % text)
        return metadata

    def process_transcript_content(self, tag):
        """
        TODO
        """
        text = tag.get_text()
        if self.speaker_regex.match(text):
            typ = 'speaker'
            context = self.process_speaker_transcript(tag)
        elif self.soundbite_regex.match(text):
            typ = 'soundbite'
            context = self.process_soundbite_transcript(tag)
        else:
            typ = 'other'
            context = self.process_other_transcript(tag)
        return typ, context

    def process_speaker_transcript(self, contents):
        """
        parses speaker paragraphs.
        transforming into the desired output markup
        """
        m = self.extract_speaker_metadata_regex.match(contents)
        if m:
            speaker = m.group(2).strip()
            try:
                speaker_class = self.SPEAKERS[speaker]
            except KeyError:
                speaker_class = 'speaker'
            timestamp = m.group(3)
            if m.group(1):
                clean_text = m.group(1) + m.group(4)
            else:
                clean_text = m.group(4)
        else:
            return contents

        markdown = self.convert_to_markdown(clean_text)

        context = {
            'speaker_class': speaker_class,
            'speaker': speaker,
            'timestamp': timestamp,
            'transcript_text': markdown
        }

        return context

    def process_soundbite_transcript(self, contents):
        """
        parses speaker paragraphs.
        transforming into the desired output markup
        """
        m = self.extract_soundbite_metadata_regex.match(contents)
        if m:
            clean_text = '(%s)' % m.group(1)
        else:
            return contents

        markdown = self.convert_to_markdown(clean_text)

        context = {'soundbite': markdown}
        return context

    def process_other_transcript(self, contents):
        """
        process all other transcript output
        """

        markdown = self.convert_to_markdown(contents)
        context = {'text': markdown}
        return context

    def convert_to_markdown(self, text):
        markdown = html2text.html2text(str(text))
        cleaned = markdown.replace('\n', ' ').replace('\r', '')

        return cleaned

    def is_anno_start_marker(self, tag):
        """
        Checks for the beginning of a new post
        """
        text = tag.get_text()
        m = self.anno_start_marker_regex.match(text)
        if m:
            return True
        else:
            return False

    def is_anno_end_marker(self, tag):
        """
        Checks for the beginning of a new post
        """
        text = tag.get_text()
        m = self.anno_end_marker_regex.match(text)
        if m:
            return True
        else:
            return False
