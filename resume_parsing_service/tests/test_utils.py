from resume_parsing_service.app.views.utils import string_scrubber
import phonenumbers


def test_string_scrubber_scrubs_strings():
    VALID_PAIRS = (
        (" Basic String ", "Basic String"),
        (u" Basic unicode ", u"Basic unicode"),
        ("\tLeading tab", "Leading tab"),
        ("Trailing tab\t", "Trailing tab"),
        ("\tLeading new line", "Leading new line"),
        ("Trailing new line\t", "Trailing new line"),
        ("(408) - 386 - 4720", "(408) - 386 - 4720"),
        ("(408) 386 - 4720", "(408) 386 - 4720"),
        ("   (408) - 386 - 4720", "(408) - 386 - 4720"),
        ("(408)\t386 - 4720", "(408) 386 - 4720"),
        ("(408)\t386\t4720", "(408) 386 4720"),
        ("\t(408)\n386 - 4720", "(408) 386 - 4720"),
    )

    for pair in VALID_PAIRS:
        assert string_scrubber(pair[0]) == pair[1]


def test_scrubbed_phone_numbers_can_be():
    VALID_PHONES = (
        ("(408) - 386 - 4720", "(408) - 386 - 4720"),
        ("(408) 386 - 4720", "(408) 386 - 4720"),
        ("   (408) - 386 - 4720", "(408) - 386 - 4720"),
        ("(408)\t386 - 4720", "(408) 386 - 4720"),
        ("(408)\t386\t4720", "(408) 386 4720"),
        ("\t(408)\n386 - 4720", "(408) 386 - 4720"),
    )
    for phone in VALID_PHONES:
        scrubbed = string_scrubber(phone[0])
        assert phonenumbers.parse(scrubbed, region='US')
