"""DocString"""
from itertools import izip_longest
from wand.image import Image
import base64
import zlib


def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks from an interable.
    Taken from https://docs.python.org/dev/library/itertools.html#itertools-recipes

    This is used to organize PDFs into manageable pictures. Three pages was the sweet spot in
    in testing before the image became to large to OCR accurately and efficiently.

    Usage example:
        grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    """
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


def convert_pdf_to_png(event, context):
    """
    Simple use of ImageMagick to convert a 1-n page PDF into images in groups of 3 pages.

    Takes in b64 encoded PDF files and turns them into b64 encoded PNG files to be sent to Google
    Vision OCR. Print statements are used for CloudWatch logging.
    :param event: JSON data POST'd to endpoint.
    :param context: Unused param in all lambda functions.
    :return: list of zlibcompressed/b64encoded PNG data.
    """
    GROUP_SIZE = 3
    img_data = []
    pdf_data = event.get('pdf_bin')

    if not pdf_data:
        return {'error': 'No PDF data passed'}

    decoded = base64.b64decode(pdf_data)
    print 'Decoded'

    #Creates a single large Image object from the PDF data.
    with Image(blob=decoded, resolution=300) as pdf:
        # pdf.sequence returns an iterable ie pictures of each page from the pdf.
        grouped = grouper(pdf.sequence, GROUP_SIZE)

        for group in grouped:
            # Creates a new 'blank' Image that is smaller than the above pdf context.
            image = Image(width=pdf.width, height=pdf.height * GROUP_SIZE)
            print "Base image created"

            if not group:
                continue

            for i, sequence in enumerate(group):
                image.composite(
                    sequence,
                    top=pdf.height * i,
                    left=0
                )
            print 'Image composed'

            blob = image.make_blob('png')
            print 'Blob made'

            compressed = zlib.compress(blob)
            print 'Compressed'

            encoded = base64.b64encode(compressed)
            print 'Encoded'

            img_data.append(encoded)

    return {'img_data': img_data}
