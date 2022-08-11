"""Tests the mail2chat.parsers module."""
import unittest
import mail2chat


class TestEnvelope:
    """Creates a mock Envelope object for testing. This object is usually created by aiosmtpd's handle_DATA method."""
    # Exclude this from pylint since it is only for testing purposes.
    # pylint: disable=too-few-public-methods
    def __init__(self, content_type="text/plain"):
        self.content = f"TO: to@example.com\n" \
              f"FROM: from@example.com\n" \
              f"SUBJECT: Example Subject\n" \
              f"CONTENT-TYPE: {content_type}\n" \
              f"\n" \
              f"Example content body."
        self.content = self.content.encode()


def get_test_email(content_type="text/plain"):
    """Creates a mock mail2chat.framework.Email object for testing."""
    return mail2chat.framework.Email(None, None, TestEnvelope(content_type))


class ParserTestCase(unittest.TestCase):
    """Creates a test case for testing the mail2chat.framework.BaseParser class."""
    def setUp(self):
        """Sets up dependencies for Parser tests."""
        self.test_email = get_test_email()

    def test_mail(self):
        """Tests the 'parser' property validation."""
        # Ensure the parser accepts the Email object
        mail2chat.framework.BaseParser(self.test_email)

        # Ensure error is thrown if not Email object
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.framework.BaseParser(False)

    def test_config(self):
        """Tests the 'config' property validation."""
        # Ensure 'content' accepts string kwargs dict.
        parser = mail2chat.framework.BaseParser(self.test_email, config_val=True, another_config_val=False)
        self.assertEqual(parser.config.get("config_val"), True)
        self.assertEqual(parser.config.get("another_config_val"), False)

        # Ensure an error is raised if not dict
        with self.assertRaises(mail2chat.framework.Error):
            parser.config = False

    def test_parse(self):
        """Tests the Parser's parse_content() method."""
        # Ensure the parser() method returns the content property by default.
        parser = mail2chat.framework.BaseParser(self.test_email)
        self.assertEqual(parser.parse_content(), self.test_email.content)

    def test_get_parser_by_content_type(self):
        """Tests the 'auto' Parser's ability to detect parser by content-type."""
        # Create mock Email objects with each content type to test
        html_type_mail = get_test_email(content_type="text/html")
        plain_type_mail = get_test_email(content_type="text/plain")
        unknown_type_mail = get_test_email(content_type="unknown")

        # Ensure mail with HTML content returns the html parser
        self.assertIsInstance(
            mail2chat.parsers.auto.Parser(html_type_mail).get_parser_by_content_type(),
            mail2chat.parsers.html.Parser
        )

        # Ensure mail with plain content returns the plain parser
        self.assertIsInstance(
            mail2chat.parsers.auto.Parser(plain_type_mail).get_parser_by_content_type(),
            mail2chat.parsers.plain.Parser
        )

        # Ensure mail with unknown content returns the default plain parser
        self.assertIsInstance(
            mail2chat.parsers.auto.Parser(unknown_type_mail).get_parser_by_content_type(),
            mail2chat.parsers.plain.Parser
        )


if __name__ == '__main__':
    unittest.main()
