"""DocString"""
from itertools import izip_longest
from wand.image import Image
from base64 import b64encode, b64decode
from zlib import compress
# from guppy import hpy
import boto3
import random


lambda_client = boto3.client('lambda')


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
    # hp = hpy()
    # heapyheap = hp.heap()
    # starting = heapyheap.size
    # print 'Starting - {}'.format(starting)
    # hp.setrelheap()
    # before = hp.heap().size
    GROUP_SIZE = 3
    img_data = []
    pdf_data = event.get('pdf_bin')

    if not pdf_data:
        return {'error': 'No PDF data passed'}

    decoded = b64decode(pdf_data)
    del pdf_data
    print 'Decoded'

    #Creates a single large Image object from the PDF data.
    with Image(blob=decoded, resolution=300) as pdf:
        """
        pdf.sequence returns an iterable ie pictures of each page from the pdf.
        When the iterable is 3 or less:
            ((<wand.sequence.SingleImage: dc1d561 (2470x3281)>, None, None))
        When the iterable is more than 3:
            (
                (<wand.sequence>, (<wand.sequence>, (<wand.sequence>),
                (<wand.sequence>, None, None)
            )
        """
        # after = hp.heap().size
        # print 'After pdf {}'.format(after - before)
        # print after
        del decoded
        grouped = grouper(pdf.sequence, GROUP_SIZE)

        # before, after = after, hp.heap().size
        # print 'After grouper {}'.format(after - before)
        # print after

        for group in grouped:
            # Creates a new 'blank' Image that is smaller than the above pdf context.
            trimmed = [item for item in group if item]
            with Image(width=pdf.width, height=pdf.height * len(trimmed)) as image:
                # before, after = after, hp.heap().size
                # print 'After sub Image {}'.format(after - before)
                # print after

                for i, sequence in enumerate(trimmed):
                    image.composite(
                        sequence,
                        top=pdf.height * i,
                        left=0
                    )
                # before, after = after, hp.heap().size
                # print 'After compsite {}'.format(after - before)
                # print after
                del trimmed
                print 'Image composed'

                blob = image.make_blob('png')
                # before, after = after, hp.heap().size
                # print 'After blobbed {}'.format(after - before)
                # print after
                del image
                print 'Blob made'

                compressed = compress(blob)
                # before, after = after, hp.heap().size
                # print 'After compressed {}'.format(after - before)
                # print after
                del blob
                print 'Compressed'

                encoded = b64encode(compressed)
                # before, after = after, hp.heap().size
                # print 'After encoded {}'.format(after - before)
                # print after
                del compressed
                print 'Encoded'

                img_data.append(encoded)
                del encoded
                # before, after = after, hp.heap().size
                # print 'After loop {}'.format(after - before)
                # print after

    # before, after = after, hp.heap().size
    # print '~~Fin~~ {}'.format(after - before)
    # print after
    timeouts = xrange(45, 75)
    new_timeout = random.choice(timeouts)
    config_response = lambda_client.update_function_configuration(
        FunctionName = 'imageMagick',
        Timeout=new_timeout
    )
    return {'img_data': img_data}
