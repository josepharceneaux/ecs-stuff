from ..email_process import validate_email_file

EMAIL_FILES_ROOT = '/emailFiles/'
EMAIL_FILE_PATHS = [
    EMAIL_FILES_ROOT + 'email2',
    EMAIL_FILES_ROOT + 'email3',
    EMAIL_FILES_ROOT + 'email4',
    EMAIL_FILES_ROOT + 'email5',
    EMAIL_FILES_ROOT + 'emailNoAttachment',
]

def validate_email_files():
    sender, hash = validate_email_file(EMAIL_FILE_PATHS[0], EMAIL_FILE_PATHS[0])
