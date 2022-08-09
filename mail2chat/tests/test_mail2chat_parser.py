"""Tests the mail2chat.parsers module."""
import unittest
import mail2chat


class ParserTestCase(unittest.TestCase):
    """Creates a test case for testing the mail2chat.framework.BaseParser class."""
    def setUp(self):
        """Sets up dependencies for Parser tests."""
        # Exclude this from pylint since it is only for testing purposes.
        # pylint: disable=too-few-public-methods

        class TestEnvelope:
            """Creates a mock Envelope object for testing."""
            content = b"TO: to@example.com\nFROM: from@example.com\nSUBJECT: Example Subject\n\nExample content body"

        self.test_email = mail2chat.framework.Email(None, None, TestEnvelope())

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


if __name__ == '__main__':
    unittest.main()
