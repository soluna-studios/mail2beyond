"""Contains tests that test the mail2chat.tools module."""

import os
import unittest
import mail2chat


class ToolsTestCase(unittest.TestCase):
    """Creates a test case for testing the mail2chat.tools module."""
    @classmethod
    def setUpClass(cls):
        # Generate a self-signed TLS certificate to use for testing.
        mail2chat.tools.generate_tls_certificate("./test_mail2chat_tools.crt", "./test_mail2chat_tools.key")

    @classmethod
    def tearDownClass(cls):
        # Remove the self-signed TLS certificate.
        try:
            os.remove("./test_mail2chat_tools.crt")
            os.remove("./test_mail2chat_tools.key")
        except FileNotFoundError:
            pass

    def test_get_connectors_from_dict(self):
        """Tests the mail2chat.tools.get_connectors_from_dict() method."""
        # Ensure error is raised when config does not contain connectors
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_connectors_from_dict({})

        # Ensure error is raised when connectors is not a list
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_connectors_from_dict({"connectors": False})

        # Ensure error is raised when connectors list is empty
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_connectors_from_dict({"connectors": []})

        # Ensure error is raised when connectors list is empty
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_connectors_from_dict({"connectors": []})

        # Ensure error is raised if connector is not a dict
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_connectors_from_dict(
                {"connectors": [False]}
            )

        # Ensure error is raised if connector name is not set
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_connectors_from_dict(
                {"connectors": [{}]}
            )

        # Ensure error is raised if connector name is not unique
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_connectors_from_dict(
                {
                    "connectors": [
                        {"name": "test_connector", "connector": "void"},
                        {"name": "test_connector", "connector": "void"}
                    ]
                }
            )

        # Ensure error is raised if connector module is not set
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_connectors_from_dict(
                {
                    "connectors": [
                        {"name": "test_connector"}
                    ]
                }
            )

        # Ensure error is raised if connector module is not known
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_connectors_from_dict(
                {
                    "connectors": [
                        {"name": "test_connector", "connector": "invalid"}
                    ]
                }
            )

        # Ensure function correctly creates the configured connectors
        connectors = mail2chat.tools.get_connectors_from_dict(
            {
                "connectors": [
                    {"name": "test_connector", "connector": "void"}
                ]
            }
        )
        self.assertIsInstance(connectors[0], mail2chat.connectors.void.Connector)
        self.assertEqual(connectors[0].name, "test_connector")

    def test_get_connector_by_name(self):
        """Tests the mail2chat.tools.get_connector_by_name() method."""
        # Ensure None is return if no match is found.
        self.assertIsNone(mail2chat.tools.get_connector_by_name("invalid", []))

        # Ensure this function correctly identifies connectors by name
        self.assertEqual(
            mail2chat.connectors.void.Connector,
            mail2chat.tools.get_connector_by_name(
                name="void",
                connector_objs=[mail2chat.connectors.void.Connector]
            )
        )

    def test_get_mappings_from_dict(self):
        """Tests the mail2chat.tools.get_mappings_from_dict() method."""
        # Ensure error is raised when config does not contain mappings
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_mappings_from_dict({})

        # Ensure error is raised when mappings is not a list
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_mappings_from_dict({"mappings": False})

        # Ensure error is raised when mappings list is empty
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_mappings_from_dict({"mappings": []})

        # Ensure error is raised when mappings list is empty
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_mappings_from_dict({"mappings": []})

        # Ensure error is raised if mappings is not a dict
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_mappings_from_dict(
                {"mappings": [False]}
            )

        # Ensure error is raised if mappings connector is not set
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_mappings_from_dict(
                {"mappings": [{}]}
            )

        # Ensure error is raised if mappings connector is not known
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_mappings_from_dict(
                {"mappings": [{"connector": "unknown"}]}
            )

        # Ensure function correctly creates the configured mappings
        mappings = mail2chat.tools.get_mappings_from_dict(
            {
                "connectors": [
                    {"name": "test_connector", "connector": "void"}
                ],
                "mappings": [
                    {"pattern": "TEST_PATTERN", "field": "sender", "connector": "test_connector"}
                ]
            }
        )
        self.assertIsInstance(mappings[0], mail2chat.framework.Mapping)
        self.assertIsInstance(mappings[0].connector, mail2chat.connectors.void.Connector)
        self.assertEqual(mappings[0].connector.name, "test_connector")

    def test_get_listeners_from_dict(self):
        """Tests the mail2chat.tools.get_listeners_from_dict() method."""
        # Ensure error is raised if no listeners are defined in the config
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_listeners_from_dict(
                {
                    "mappings": [{"pattern": "default", "connector": "void"}],
                    "connectors": [{"name": "void", "connector": "void"}]
                }
            )

        # Ensure error is raised if listeners is not a list
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_listeners_from_dict(
                {
                    "mappings": [{"pattern": "default", "connector": "void"}],
                    "connectors": [{"name": "void", "connector": "void"}],
                    "listeners": False
                }
            )

        # Ensure error is raised if listeners have no items
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_listeners_from_dict(
                {
                    "mappings": [{"pattern": "default", "connector": "void"}],
                    "connectors": [{"name": "void", "connector": "void"}],
                    "listeners": []
                }
            )

        # Ensure error is raised if listeners item is not dict
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_listeners_from_dict(
                {
                    "mappings": [{"pattern": "default", "connector": "void"}],
                    "connectors": [{"name": "void", "connector": "void"}],
                    "listeners": [False]
                }
            )

        # Ensure error is raised if listeners item does not contain address
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_listeners_from_dict(
                {
                    "mappings": [{"pattern": "default", "connector": "void"}],
                    "connectors": [{"name": "void", "connector": "void"}],
                    "listeners": [{}]
                }
            )

        # Ensure error is raised if listeners item does not contain port
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_listeners_from_dict(
                {
                    "mappings": [{"pattern": "default", "connector": "void"}],
                    "connectors": [{"name": "void", "connector": "void"}],
                    "listeners": [
                        {
                            "address": "127.0.0.1"
                        }
                    ]
                }
            )

        # Ensure enable_smtp cannot be non-bool value
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_listeners_from_dict(
                {
                    "mappings": [{"pattern": "default", "connector": "void"}],
                    "connectors": [{"name": "void", "connector": "void"}],
                    "listeners": [
                        {
                            "address": "127.0.0.1",
                            "port": 62125,
                            "enable_smtps": "yes",
                            "tls_cert": "./test_mail2chat_tools.crt",
                            "tls_key": "./test_mail2chat_tools.key"
                        }
                    ]
                }
            )

        # Ensure enable_smtp and enable_starttls cannot be enabled at the same time
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_listeners_from_dict(
                {
                    "mappings": [{"pattern": "default", "connector": "void"}],
                    "connectors": [{"name": "void", "connector": "void"}],
                    "listeners": [
                        {
                            "address": "127.0.0.1",
                            "port": 62125,
                            "enable_smtps": True,
                            "enable_starttls": True,
                            "tls_cert": "./test_mail2chat_tools.crt",
                            "tls_key": "./test_mail2chat_tools.key"
                        }
                    ]
                }
            )

        # Ensure enable_starttls must be bool
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_listeners_from_dict(
                {
                    "mappings": [{"pattern": "default", "connector": "void"}],
                    "connectors": [{"name": "void", "connector": "void"}],
                    "listeners": [
                        {
                            "address": "127.0.0.1",
                            "port": 62125,
                            "enable_starttls": "yes",
                            "tls_cert": "./test_mail2chat_tools.crt",
                            "tls_key": "./test_mail2chat_tools.key"
                        }
                    ]
                }
            )

        # Ensure require_starttls must be bool
        with self.assertRaises(mail2chat.framework.Error):
            mail2chat.tools.get_listeners_from_dict(
                {
                    "mappings": [{"pattern": "default", "connector": "void"}],
                    "connectors": [{"name": "void", "connector": "void"}],
                    "listeners": [
                        {
                            "address": "127.0.0.1",
                            "port": 62125,
                            "enable_starttls": True,
                            "require_starttls": "yes",
                            "tls_cert": "./test_mail2chat_tools.crt",
                            "tls_key": "./test_mail2chat_tools.key"
                        }
                    ]
                }
            )

        # Create a SMTP, STARTTLS and SMTPS listener via dict
        config = {
            "mappings": [{"pattern": "default", "connector": "void"}],
            "connectors": [{"name": "void", "connector": "void"}],
            "listeners": [
                {"address": "127.0.0.1", "port": 2525},
                {
                    "address": "127.0.0.1",
                    "port": 46500,
                    "enable_smtps": True,
                    "tls_cert": "./test_mail2chat_tools.crt",
                    "tls_key": "./test_mail2chat_tools.key"
                },
                {
                    "address": "127.0.0.1",
                    "port": 46500,
                    "enable_starttls": True,
                    "tls_cert": "./test_mail2chat_tools.crt",
                    "tls_key": "./test_mail2chat_tools.key"
                }
            ]
        }
        listeners = mail2chat.tools.get_listeners_from_dict(config)

        # Ensure the listens created are expected
        self.assertEqual(len(listeners), 3)


if __name__ == '__main__':
    unittest.main()
