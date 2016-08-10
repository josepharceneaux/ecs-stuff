"""DocString"""
import base64
import zlib
from wand.image import Image


def convert_pdf_to_png(event, context):
    """
    Simple use of ImageMagick. Takes in b64 encoded PDF files and turns them into b64 encoded
    PNG files to be sent to Google Vision OCR. Print statements are used for CloudWatch logging.
    :param event: JSON data POST'd to endpoint.
    :param context: Unused param in all lambda functions.
    :return: b64 PNG data.
    :rtype: dict
    """
    pdf_data = event.get('pdf_bin')

    if not pdf_data:
        return {'error': 'No PDF data passed'}

    decoded = base64.b64decode(pdf_data)
    print 'decoded'

    with Image(blob=decoded, resolution=300) as pdf:
        pages = len(pdf.sequence)
        image = Image(width=pdf.width, height=pdf.height * pages)
        print 'base image made'

        for i in xrange(pages):
            image.composite(
                pdf.sequence[i],
                top=pdf.height * i,
                left=0
            )
        print 'image composed'

        blob = image.make_blob('png')
        print 'blob made'

        compressed = zlib.compress(blob)
        print 'compressed'

        encoded = base64.b64encode(compressed)
        print 'encoded'

        return {'img_data': encoded}
