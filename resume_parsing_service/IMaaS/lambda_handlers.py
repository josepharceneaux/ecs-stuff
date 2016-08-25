"""DocString"""
from itertools import izip_longest
from wand.image import Image
from base64 import b64encode, b64decode
from zlib import compress


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
        del decoded
        grouped = grouper(pdf.sequence, GROUP_SIZE)

        for group in grouped:
            # Creates a new 'blank' Image that is smaller than the above pdf context.
            trimmed = [item for item in group if item]
            with Image(width=pdf.width, height=pdf.height * len(trimmed)) as image:
                print "Base image created"

                for i, sequence in enumerate(trimmed):
                    image.composite(
                        sequence,
                        top=pdf.height * i,
                        left=0
                    )
                del trimmed
                print 'Image composed'

                blob = image.make_blob('png')
                del image
                print 'Blob made'

                compressed = compress(blob)
                del blob
                print 'Compressed'

                encoded = b64encode(compressed)
                del compressed
                print 'Encoded'

                img_data.append(encoded)
                del encoded

    return {'img_data': img_data}
