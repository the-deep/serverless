import tempfile
import os
import uuid
from subprocess import call

from selenium import webdriver
from PIL import Image

DEFAULT_WIDTH = 412

MOBILE_SCREEN_WIDTH = 412
MOBILE_SCREEN_HEIGHT = 732

CHROME_DRIVER_LOCATION = '/tmp/chromedriver'
CHROME_BINARY_LOCATION = '/tmp/headless-chromium'

TEMP_DIR = '/tmp/'


def resize_image(file_name, width=None, height=None):
    if not (height or width):
        return

    img = Image.open(file_name)
    _width, _height = img.size

    if not height:
        height = int(_height * width / _width)

    if not width:
        width = int(_width * height / _height)

    img = img.resize((width, height), Image.ANTIALIAS)
    img.save(file_name, optimize=True, quality=75)


class Thumbnailer:
    def __init__(self, doc, type):
        self.doc = doc
        self.type = type

    def get_thumbnail(self):
        pass


class DocThumbnailer(Thumbnailer):
    def get_thumbnail(self):
        """
        Convert files to  image using libreoffice headless
        """
        # Create copy of the doc
        # libreoffice command requires local file
        temp_doc = tempfile.NamedTemporaryFile(
            dir=TEMP_DIR,
            suffix='.{}'.format(self.type),
        )
        self.doc.seek(0)
        temp_doc.write(self.doc.read())
        temp_doc.flush()
        # libreoffice doesn't provide custom filename and generates file of
        # same name as source file with converted extension
        call(['libreoffice', '--headless', '--convert-to',
              'png', temp_doc.name, '--outdir', TEMP_DIR])
        fileprefix = os.path.splitext(os.path.basename(temp_doc.name))[0]
        thumbnail = os.path.join(
            TEMP_DIR,
            '{}.png'.format(fileprefix)
        )
        temp_doc.close()

        # libreoffice silently fails to generate thumbnails for some files
        if os.path.exists(thumbnail):
            resize_image(thumbnail, DEFAULT_WIDTH)
            return open(thumbnail, 'rb')
        return None


class WebThumbnailer(Thumbnailer):
    """
    Generate thumbnail of the lead using selenium
    and headless chrome, window size is same as Pixel 2
    to make thumbnail smaller and compact
    """

    def get_thumbnail(self):
        if self.doc:
            file_name = os.path.join(
                TEMP_DIR,
                'thumbnail_{}.png'.format(str(uuid.uuid4())),
            )
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=412x732')
            options.add_argument('--hide-scrollbars')
            options.add_argument('--single-process')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')  # noqa: E501
            options.binary_location = CHROME_BINARY_LOCATION
            options.add_experimental_option('mobileEmulation', {
                'deviceMetrics': {
                    'width': MOBILE_SCREEN_WIDTH,
                    'height': MOBILE_SCREEN_HEIGHT,
                    'pixelRatio': 3.0,
                },
            })

            browser = webdriver.Chrome(options=options, executable_path=CHROME_DRIVER_LOCATION)
            browser.get(self.doc)
            browser.implicitly_wait(2)  # wait 2 sec to settle things up
            browser.get_screenshot_as_file(file_name)
            resize_image(file_name, MOBILE_SCREEN_WIDTH, MOBILE_SCREEN_HEIGHT)  # optimize the image
            return open(file_name, 'rb')
        return None
