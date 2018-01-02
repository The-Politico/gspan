from parser import TranscriptParser

with open('test.html', 'r') as f:
    html = f.read()
    parsed = TranscriptParser(html)