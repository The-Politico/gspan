![POLITICO](https://rawgithub.com/The-Politico/src/master/images/logo/badge.png)

# politico-transcript-parser

### Quickstart

```
$ pip install politico-transcript-parser
```

Then, use in your project:

```
from transcript_parser import TranscriptParser

authors = {
    'authorname@email.com': 'Author Name',
    'anotherhuman@email.com': 'Another Human'
}

with open('my_html_file.html') as f:
    html = f.read()
    parsed = TranscriptParser(html, authors=authors)
    print(parsed.transcript)
```

### Testing

```
$ pytest
```
