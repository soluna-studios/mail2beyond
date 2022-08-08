import unittest
from mail2chat import framework
from mail2chat import connectors


class MappingTestCase(unittest.TestCase):
    def setUp(self):
        """Setup the test environment."""
        self.test_connector = connectors.void.Connector()
        self.test_mapping = framework.Mapping(pattern="TEST_PATTERN", connector=self.test_connector)

    def test_pattern(self):
        """Tests validation of the Mapping object's 'pattern' attribute."""
        # Ensure this value can only be set to a string
        self.test_mapping.pattern = "TEST_PATTERN"

        # Ensure Type error is raised when not a string
        with self.assertRaises(TypeError):
            self.test_mapping.pattern = False

    def test_connector(self):
        """Tests validation of the Mapping object's 'connector' attribute."""
        # Ensure this value can only be set to a BaseConnector child class
        self.test_mapping.connector = self.test_connector

        # Ensure Type error is raised when not a BaseConnector child class
        with self.assertRaises(TypeError):
            self.test_mapping.connector = False

        # Ensure the parent BaseConnector class is also not accepted
        with self.assertRaises(TypeError):
            self.test_mapping.connector = framework.BaseConnector()

    def test_field(self):
        """Tests validation of the Mapping object's 'field' attribute."""
        # Ensure this value can only be set to a valid option
        self.test_mapping.field = "recipients"
        self.test_mapping.field = "sender"
        self.test_mapping.field = "ip"
        self.test_mapping.field = "subject"
        self.test_mapping.field = "body"

        # Ensure Value error is raised when not a BaseConnector child class
        with self.assertRaises(ValueError):
            self.test_mapping.field = False

    def test_is_match(self):
        """Tests the Mapping object's is_match() method."""
        # Ensure bad pattern matches fail.
        self.assertFalse(self.test_mapping.is_match("NO_MATCH"))

        # Ensure exact pattern matches are successful.
        self.assertTrue(
            self.test_mapping.is_match(
                value=self.test_mapping.pattern
            )
        )


if __name__ == '__main__':
    unittest.main()
