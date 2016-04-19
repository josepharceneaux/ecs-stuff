import email

from resume_parsing_service.emailReceiver.email_process import validate_email_file

EMAIL_FILES_ROOT = 'emailFiles/'
EMAIL_FILE_PATHS = [
    EMAIL_FILES_ROOT + 'email2',
    EMAIL_FILES_ROOT + 'email3',
    EMAIL_FILES_ROOT + 'email4',
    EMAIL_FILES_ROOT + 'email5',
    EMAIL_FILES_ROOT + 'emailNoAttachment',
]

def test_validate_email_files():
    with open(EMAIL_FILE_PATHS[0], 'r') as infile:
        email_file = email.message_from_file(infile)
    sender, hash = validate_email_file(email_file, EMAIL_FILE_PATHS[0])
    pass
