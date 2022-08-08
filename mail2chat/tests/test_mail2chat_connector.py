"""Contains tests that test the mail2chat.framework.BaseConnector class."""

import unittest
from mail2chat import framework


class ConnectorTestCase(unittest.TestCase):
    """Runs tests against the BaseConnector class."""
    def setUp(self):
        # Define a new child class for testing inheritance
        class TestChildConnector(framework.BaseConnector):
            """Class to test class inheritance."""

            def submit(self, mail):
                """Overwrites the submit() method."""
                return

            def pre_submit(self, mail):
                """Overwrites the pre-submit method"""
                return

        # Create a base and child connector object to test with
        self.base_connector = framework.BaseConnector()
        self.child_connector = TestChildConnector()

    def test_base_connector_submit(self):
        """Test the BaseConnector class's submit() method directly."""
        # Ensure calling the BaseConnector class's submit() method raises an error by default
        with self.assertRaises(framework.Error):
            self.base_connector.submit(mail=None)

    def test_base_connector_run(self):
        """Test the BaseConnector class's run() method directly."""
        # Ensure calling the BaseConnector class's run() method raises an error by default as it calls submit()
        with self.assertRaises(framework.Error):
            self.base_connector.run(mail=None)

    def test_base_connector_pre_submit(self):
        """Test the BaseConnector class's pre_submit() method directly."""
        # Ensure calling the BaseConnector class's pre_submit() method returns nothing
        self.assertIsNone(self.base_connector.pre_submit(mail=None))

    def test_child_connector_submit(self):
        """Test the TestChildConnector class's submit() method directly."""
        # Ensure calling the TestChildConnector class's submit() returns nothing since it was overwritten.
        self.assertIsNone(
            self.child_connector.submit(mail=None)
        )

    def test_child_connector_run(self):
        """Test the TestChildConnector class's run() method directly."""
        # Ensure calling the TestChildConnector class's submit() returns nothing since submit() was overwritten.
        self.assertIsNone(
            self.child_connector.run(mail=None)
        )

    def test_child_connector_pre_submit(self):
        """Test the TestChildConnector class's pre_submit() method directly."""
        # Ensure calling the TestChildConnector class's pre_submit() method returns nothing
        self.assertIsNone(
            self.base_connector.pre_submit(mail=None)
        )


if __name__ == '__main__':
    unittest.main()
