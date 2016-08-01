"""DocString"""
import base64
from wand.image import Image


def convert_pdf_to_png(event, context):
    """
    Simple use of ImageMagick. Takes in b64 encoded PDF files and turns them into b64 encoded
    PNG files to be sent to Google Vision OCR. Print statements are used for CloudWatch logging.
    :param event: JSON data POST'd to endpoint. With regard to the resolution, 250 generated the
    best passable image quality that could be OCR'd and the increase to 300 is for buffer.
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

        png = base64.b64encode(blob)
        print 'encoded'

        return {'img_data': png}
