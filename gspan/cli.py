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
            ))
        ]

    @expose(help="Parse document, output JSON")
    def parse(self):
        """
        gspan parse <Google doc id>

        Parses a document and returns an HTML string
        """
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
