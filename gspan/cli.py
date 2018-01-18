import json

from cement.core.controller import CementBaseController, expose
from cement.core.foundation import CementApp
from cement.ext.ext_logging import LoggingLogHandler
from . import TranscriptParser


LOG_FORMAT = '%(asctime)s (%(levelname)s) %(name)s : %(message)s'


class GspanBaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = 'Get and parse Google Doc transcript'
        arguments = [
            (['key'], dict(
                action='store',
                help='Google Doc key'
            )),
            (['-a, --authors'], dict(
                action='store',
                help='Supply author data',
                dest='authors'
            ))
        ]

    @expose(help="Parse document, output JSON")
    def parse(self):
        """
        gspan parse <Google doc id>

        Parses a document and returns an HTML string
        """
        if self.app.pargs.authors:
            author_file = self.app.pargs.authors

            with open(author_file) as f:
                authors = json.load(f)

            parsed = TranscriptParser(self.app.pargs.key, author_data=authors)
        else:
            parsed = TranscriptParser(self.app.pargs.key)

        self.app.render(parsed.to_json())

    @expose(help="Downloads a Google Doc HTML file")
    def download(self):
        """
        gspan download <Google doc id>

        Downloads a Google Doc as HTML and pipes it to stdout
        """
        parsed = TranscriptParser(self.app.pargs.key)
        print(parsed.html)

    @expose(help="Prints output from copydoc")
    def copydoc(self):
        """
        gspan download <Google doc id>

        Downloads a Google Doc as HTML and pipes it to stdout
        """
        parsed = TranscriptParser(self.app.pargs.key)
        print(parsed.doc)


class GspanApp(CementApp):
    class Meta:
        label = 'gspan'
        base_controller = GspanBaseController
        exit_on_close = True
        log_handler = LoggingLogHandler(
            console_format=LOG_FORMAT,
            file_format=LOG_FORMAT
        )


def main():
    with GspanApp() as app:
        app.run()
