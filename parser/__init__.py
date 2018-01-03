#!/usr/bin/env python

import html2text
import re

from copydoc import CopyDoc


class TranscriptParser:
    """
    Cleans Google Doc HTML, then converts into JSON
    """
    def __init__(self, html_string):
        self.regexes = {
            'end_transcript': re.compile(
                r'.*LIVE\sTRANSCRIPT\sHAS\sENDED.*'),
            'do_not_write': re.compile(
                r'.*DO\s*NOT\s*WRITE\s*BELOW\s*THIS\s*LINE.*'),
            'end_fact_check': re.compile(r'^\s*[Ee][Nn][Dd]\s*$'),
            'anno_start_marker': re.compile(r'^\s*\+{50,}\s*$'),
            'anno_end_marker': re.compile(r'^\s*-{50,}\s*$'),
            'frontmatter_marker': re.compile(r'^\s*-{3}\s*$'),
            'extract_metadata': re.compile(r'^(.*?):(.*)$'),
            'speaker': re.compile(r'^[A-Z\s.-]+(\s\[.*\])?:'),
            'soundbite': re.compile(r'^\s*:'),
            'extract_speaker_metadata': re.compile(
                r'^\s*(<.*?>)?([A-Z0-9\s.-]+)\s*(?:\[(.*)\]\s*)?:\s*(.*)'),
            'extract_soundbite_metadata': re.compile(
                r'^\s*(?:<.*?>)?\s*:\[\((.*)\)\]'),
            'extract_author_metadata': re.compile(r'^.*\((.+)\)\s*$')
        }

        self.doc = CopyDoc(html_string)
        self.transcript = self.parse()

    def parse(self):
        """
        Parse all the annotation-specific content
        """
        self.remove_administrivia(self.doc.soup)
        raw = self.separate_components(self.doc.soup)
        contents = self.parse_raw_contents(raw)
        return contents

    def remove_administrivia(self, soup):
        hr = soup.hr

        if hr:
            if hr.find('p', text=self.regexes['end_fact_check']):
                hr.extract()
            elif hr.find('p', text=self.regexes['end_transcript']):
                hr.extract()
            else:
                for child in hr.children:
                    if (child.string):
                        after_hr_text = child.string
                    else:
                        after_hr_text = child.get_text()
                    m = self.regexes['do_not_write'].match(after_hr_text)
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
                    m = self.regexes['frontmatter_marker'].match(text)
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
            m = self.regexes['extract_metadata'].match(text)
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
        if self.regexes['speaker'].match(text):
            typ = 'speaker'
            context = self.process_speaker_transcript(tag)
        elif self.regexes['soundbite'].match(text):
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
        m = self.regexes['extract_speaker_metadata'].match(contents)
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
        m = self.regexes['extract_soundbite_metadata'].match(contents)
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
        m = self.regexes['anno_start_marker'].match(text)
        if m:
            return True
        else:
            return False

    def is_anno_end_marker(self, tag):
        """
        Checks for the beginning of a new post
        """
        text = tag.get_text()
        m = self.regexes['anno_end_marker'].match(text)
        if m:
            return True
        else:
            return False
