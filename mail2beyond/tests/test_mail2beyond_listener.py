"""Contains tests that test the mail2beyond.framework.Listener class."""

import smtplib
import unittest

from mail2beyond import connectors
from mail2beyond import framework


class ListenerTestCase(unittest.TestCase):
    """Creates a test case for testing the mail2beyond.framework.Listener class."""
    def setUp(self):
        """Setup the test environment."""
        # Create mappings to assign the listener
        self.default_mapping = framework.Mapping(pattern="default", connector=connectors.void.Connector())

        # Create a listener to test with
        self.listener = framework.Listener(
            mappings=[self.default_mapping]
        )

    def test_get_default_mapping(self):
        """Test the Listener class's get_default_mapping() method directly."""
        # Fetch the default mapping
        default_mapping = self.listener.get_default_mapping()

        # Ensure it is actually the default mapping
        self.assertEqual(default_mapping.pattern, "default")

    def test_address(self):
        """Test the Listener class's 'address' attribute validation."""
        # Ensure IP addresses, wildcard and localhost are accepted
        self.listener.address = "0.0.0.0"
        self.listener.address = "localhost"

        # Ensure other values are rejected
        with self.assertRaises(framework.Error):
            self.listener.address = "invalid"

    def test_port(self):
        """Test the Listener class's 'port' attribute validation."""
        # Ensure valid port can be set
        self.listener.port = 1

        # Ensure values less than 1 are rejected.
        with self.assertRaises(framework.Error):
            self.listener.port = 0

        # Ensure values greater than 65535 are rejected.
        with self.assertRaises(framework.Error):
            self.listener.port = 65536

    def test_mappings(self):
        """Test the Listener class's 'mappings' attribute validation."""
        # Ensure mappings is type list
        with self.assertRaises(TypeError):
            self.listener.mappings = False

        # Ensure mappings contains at least one item
        with self.assertRaises(framework.Error):
            self.listener.mappings = []

        # Ensure mappings items are type Mapping
        with self.assertRaises(framework.Error):
            self.listener.mappings = [False]

        # Ensure mappings requires default mapping
        with self.assertRaises(framework.Error):
            non_default_mapping = self.default_mapping
            non_default_mapping.pattern = "not_the_default"
            self.listener.mappings = [non_default_mapping]

        # Ensure multiple default mappings cannot be set
        with self.assertRaises(framework.Error):
            self.listener.mappings = [self.default_mapping, self.default_mapping]

    def test_controller_start(self):
        """Test starting the listener controller with the start() method."""
        # Test the listener on various ports
        for port in [2525, 12525, 25252, 62125]:
            # Start the listener and ensure it is working.
            self.listener.address = "127.0.0.1"
            self.listener.port = port
            self.listener.setup_controller()
            self.listener.controller.start()

            # Ensure we can send SMTP messages to the server.
            smtp = smtplib.SMTP(self.listener.address, self.listener.port, timeout=10)
            smtp.sendmail(
                "sender@example.com",
                "recipient@example.com",
                "FROM: sender@example.com\nTO: recipient@example.com\nSubject: Test subject\n\nTest body"
            )

            # Close the SMTP connection and stop the SMTP server.
            smtp.close()
            self.listener.controller.stop()
            del self.listener.controller


if __name__ == '__main__':
    unittest.main()
