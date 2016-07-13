from resume_parsing_service.app.views.parse_lib import unencrypt_pdf
from cStringIO import StringIO
#
from wand.image import Image
import base64,requests, json

GOOGLE_API_KEY="AIzaSyD4i4j-8C5jLvQJeJnLmoFW6boGkUhxSuw"
GOOGLE_CLOUD_VISION_URL="https://vision.googleapis.com/v1/images:annotate"

def ocr_with_google(string_io_obj):
    unencd = unencrypt_pdf(string_io_obj)
    unencd.seek(0)
    outfile = StringIO()
    # im = Image(file=unencd, resolution=200)
    im = convert_pdf_to_png(unencd)
    outfile = StringIO(im)
    gData = google_vision_ocr(outfile)
    return gData


def convert_pdf_to_png(blob):
    pdf = Image(blob=blob)
    Image.save()

    pages = len(pdf.sequence)

    image = Image(
        width=pdf.width,
        height=pdf.height * pages,
        resolution=200
    )

    for i in xrange(pages):
        image.composite(
            pdf.sequence[i],
            top=pdf.height * i,
            left=0
        )

    return image.make_blob('jpeg')


def google_vision_ocr(file_string_io):
    """
    Utilizes Google Vision API to OCR image with Abbyy as a fallback.
    Root Docs: https://cloud.google.com/vision/docs/
    Specific JSON responses:
        https://cloud.google.com/vision/reference/rest/v1/images/annotate#annotateimageresponse
        https://cloud.google.com/vision/reference/rest/v1/images/annotate#entityannotation
    :param cStringIO.StringIO file_string_io:
    :return unicode:
    """
    file_string_io.seek(0)
    b64_string = base64.b64encode(file_string_io.getvalue())
    req_data = {
        "requests": [
            {
                "image": {
                    "content": b64_string
                },
                "features": [
                    {
                        "type": "TEXT_DETECTION",
                        "maxResults": 1
                    }
                ]
            }
        ]
    }

    google_response = requests.post("{}?key={}".format(GOOGLE_CLOUD_VISION_URL,
                                                       GOOGLE_API_KEY),
                                    json.dumps(req_data),
                                    timeout=20,
                                    headers={'content-type': 'application/json'})
    return google_response