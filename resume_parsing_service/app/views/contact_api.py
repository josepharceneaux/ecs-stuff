# Standard Library
import base64
from cStringIO import StringIO
from os.path import basename
from os.path import splitext
import re
from time import time
# Third Party
from flask import Blueprint
from flask import jsonify
from flask import request
from flask.ext.cors import CORS
from PIL import Image
from bs4 import BeautifulSoup as bs4
import magic
import nltk
from nltk.corpus import stopwords
# Module Specific
from resume_parsing_service.app import logger
from resume_parsing_service.app.modules.ocr_lib import ocr_image
from resume_parsing_service.app.modules.parse_lib import is_resume_image
from resume_parsing_service.app.modules.parse_lib import validate_content_len
from resume_parsing_service.app.modules.pdf_utils import decrypt_pdf
from resume_parsing_service.app.modules.utils import resume_file_from_params
from resume_parsing_service.app.modules.param_builders import build_params_from_form
from resume_parsing_service.common.error_handling import InvalidUsage
from resume_parsing_service.app.constants import error_constants
from resume_parsing_service.app.modules.optic_parse_lib import fetch_optic_response

CONTACT_MOD = Blueprint('contact_only', __name__)
NON_DEFAULT_JSON_KEYS = ('filepicker_key', 'source_id', 'talent_pool_ids', 'source_product_id')
EMAIL_REGEX = re.compile("[^@]+@[^@]+\.[^@]+")
PHONE_REGEX = re.compile("(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})")
stop = stopwords.words('english')

CORS(
    CONTACT_MOD,
    resources={
        r'/v1/contact_only': {
            'origins': [r"*.gettalent.com", "http://localhost"],
            'allow_headers': ['Content-Type', 'Authorization']
        }
    })


@CONTACT_MOD.route('/contact_only', methods=['POST'])
def get_contact_info():
    # oauth = request.oauth_token
    params = build_params_from_form(request)
    contact_info = parse_contact_info(params)
    return jsonify({'contact_info': contact_info})


def parse_contact_info(params):
    file_obj = resume_file_from_params(params)
    filename_str = params['filename']
    file_ext = basename(splitext(filename_str.lower())[-1]) if filename_str else ""
    if file_ext == '.pdf':
        file_obj = decrypt_pdf(file_obj)
    is_image = is_resume_image(file_ext, file_obj)
    if is_image:
        start_time = time()
        is_not_pdf = file_ext != '.pdf' and not ('pdf' in magic.from_buffer(file_obj.read()).lower())
        file_obj.seek(0)

        if is_not_pdf:
            with Image.open(file_obj) as im:
                width, height = im.size
                if width > 2500 or height > 2500:
                    file_obj = StringIO()
                    im.thumbnail((2500, 2500), Image.ANTIALIAS)
                    im.save(file_obj, format='PNG')

                doc_content = ocr_image(file_obj, filename_str)
                """
                Due to StringIO processing we need to validate the content on the open file object
                before it is closed with im.save
                """
                validate_content_len(doc_content, file_obj, filename_str)
        else:
            if file_ext != '.pdf':
                filename_str += '.pdf'
            doc_content = ocr_image(file_obj, filename_str)

        logger.info("ResumeParsingService::Benchmark: OCR for {}: took {}s to process".format(filename_str,
                                                                                              time() - start_time))

    else:
        doc_content = file_obj.read()

    try:
        encoded_resume = base64.b64encode(doc_content)

    except Exception:
        logger.exception('Error encoding resume before sending to BG Optic.')
        raise InvalidUsage(
            error_message=error_constants.ERROR_ENCODING_TEXT['message'],
            error_code=error_constants.ERROR_ENCODING_TEXT['code'])

    optic_response = fetch_optic_response(encoded_resume, filename_str)
    resume_soup = bs4(optic_response, 'lxml')
    resume_text = resume_soup.get_text()
    contact_details = {
        'emails': EMAIL_REGEX.findall(resume_text),
        'phones': PHONE_REGEX.findall(resume_text),
        'name': get_human_names(resume_text)
    }
    print contact_details
    return resume_text

def get_human_names(text):
    tokens = nltk.tokenize.word_tokenize(text)
    filtered_words = [word for word in tokens if word not in stopwords.words('english')]
    pos = nltk.pos_tag(filtered_words)
    sentt = nltk.ne_chunk(pos, binary = False)
    person_list = []
    person = []
    name = ""
    for subtree in sentt.subtrees(filter=lambda t: t.label() == 'PERSON'):
        for leaf in subtree.leaves():
            person.append(leaf[0])
        if len(person) > 1: #avoid grabbing lone surnames
            for part in person:
                name += part + ' '
            if name[:-1] not in person_list:
                person_list.append(name[:-1])
            name = ''
        person = []
    return (person_list)
