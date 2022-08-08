"""Contains tests that test the mail2chat.framework.Mapping class."""

import unittest
from mail2chat import framework
from mail2chat import connectors


class MappingTestCase(unittest.TestCase):
    """Creates a test case for testing the mail2chat.framework.Mapping class."""
    def setUp(self):
        """Setup the test environment."""
        self.test_connector_obj = connectors.void.Connector()
        self.test_mapping_obj = framework.Mapping(pattern="TEST_PATTERN", connector=self.test_connector_obj)

    def test_pattern(self):
        """Tests validation of the Mapping object's 'pattern' attribute."""
        # Ensure this value can only be set to a string
        self.test_mapping_obj.pattern = "TEST_PATTERN"

        # Ensure Type error is raised when not a string
        with self.assertRaises(TypeError):
            self.test_mapping_obj.pattern = False

    def test_connector(self):
        """Tests validation of the Mapping object's 'connector' attribute."""
        # Ensure this value can only be set to a BaseConnector child class
        self.test_mapping_obj.connector = self.test_connector_obj

        # Ensure Type error is raised when not a BaseConnector child class
        with self.assertRaises(TypeError):
            self.test_mapping_obj.connector = False

        # Ensure the parent BaseConnector class is also not accepted
        with self.assertRaises(TypeError):
            self.test_mapping_obj.connector = framework.BaseConnector()

    def test_field(self):
        """Tests validation of the Mapping object's 'field' attribute."""
        # Ensure this value can only be set to a valid option
        self.test_mapping_obj.field = "recipients"
        self.test_mapping_obj.field = "sender"
        self.test_mapping_obj.field = "ip"
        self.test_mapping_obj.field = "subject"
        self.test_mapping_obj.field = "body"

        # Ensure Value error is raised when not a BaseConnector child class
        with self.assertRaises(ValueError):
            self.test_mapping_obj.field = False

    def test_is_match(self):
        """Tests the Mapping object's is_match() method."""
        # Ensure bad pattern matches fail.
        self.assertFalse(self.test_mapping_obj.is_match("NO_MATCH"))

        # Ensure exact pattern matches are successful.
        self.assertTrue(
            self.test_mapping_obj.is_match(
                value=self.test_mapping_obj.pattern
            )
        )


if __name__ == '__main__':
    unittest.main()
