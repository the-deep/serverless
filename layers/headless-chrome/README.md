# Headless-chrome layer
Contains Binary (compressed by brotli) used to generate thumbnail through chrome.
https://github.com/adieuadieu/serverless-chrome/issues/133#issuecomment-629529054

```bash
# Doesn't work with python3.8 right now
docker run -v `pwd`:/var/task --rm -it lambci/lambda:build-python3.7 bash
```

Dependencies required
```bash
#!/bin/bash

yum install -y libjpeg-devel

pip install Pillow==5.4.1
pip install selenium==3.14
pip install brotli
```


Python script to test
```python
import os
import time
import uuid
import stat
import logging
import brotli
from io import BytesIO

from selenium import webdriver
from PIL import Image

DEFAULT_WIDTH = 412

MOBILE_SCREEN_WIDTH = 412
MOBILE_SCREEN_HEIGHT = 732

logger = logging.getLogger(__name__)


TEMP_DIR = './tmp/'
CHROME_DRIVER_LOCATION = './chromedriver'
CHROME_BINARY_LOCATION = './headless-chromium'


def unpack_binary(input_file, output_file, make_executable=True):
    start_time = time.time()
    if os.path.exists(output_file):
        logger.info(f'We have a cached copy of {input_file}, skipping extraction')
        return output_file
    logger.info(f'No cached copy of {input_file} exists, extracting Brotli file...')
    buffer = BytesIO()
    with open(input_file, 'rb') as brotli_file:
        decompressor = brotli.Decompressor()
        while True:
            chunk = brotli_file.read(1024)
            buffer.write(decompressor.process(chunk))
            if len(chunk) < 1024:
                break
        buffer.seek(0)
    with open(output_file, 'wb') as out:
        out.write(buffer.read())
    if make_executable:
        os.chmod(output_file, stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    logger.info(f'Took {time.time() - start_time} seconds to unpack {input_file}')
    return output_file


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


def generate(url):
    if url:
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
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

        options.binary_location = CHROME_BINARY_LOCATION
        mobile_emulation = {
            'deviceMetrics': {
                'width': MOBILE_SCREEN_WIDTH,
                'height': MOBILE_SCREEN_HEIGHT,
                'pixelRatio': 3.0,
            },
        }
        options.add_experimental_option('mobileEmulation', mobile_emulation)
        browser = webdriver.Chrome(options=options, executable_path=CHROME_DRIVER_LOCATION)
        browser.get(url)
        # wait 2 sec to settle things up
        browser.implicitly_wait(2)
        browser.get_screenshot_as_file(file_name)
        # optimize the image
        resize_image(file_name, MOBILE_SCREEN_WIDTH, MOBILE_SCREEN_HEIGHT)


unpack_binary(f'{CHROME_DRIVER_LOCATION}.br', CHROME_DRIVER_LOCATION)
unpack_binary(f'{CHROME_BINARY_LOCATION}.br', CHROME_BINARY_LOCATION)
generate(
    'https://reliefweb.int/report/venezuela-bolivarian-republic/us144-billion-needed-support-refugees-and-migrants-venezuela'
)
```
