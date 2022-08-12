Mail2Beyond Command Line Interface
================================
Mail2Beyond can be used entirely by CLI. After installing Mail2Beyond, you will have access to the `mail2beyond` command line
tool. The CLI allows you define listeners, connectors and mappings using a JSON or YAML formatted configuration file.

## Arguments

| Argument               | Required | Description                                                                   |
|------------------------|:---------|-------------------------------------------------------------------------------|
| `--config (-c) <FILE>` | Yes      | Specifies which configuration file to load. This must be a JSON or YAML file. |
| `--version (-V)`       | No       | Prints the version of mail2beyond installed.                                    |
| `--verbose (-v)`       | No       | Enables verbose logging.                                                      |
| `--help (-h)`          | No       | Prints the help page.                                                         |

## Configuration
A configuration file must be written before `mail2beyond` is started. It may also be helpful to check out the 
[examples on GitHub](https://github.com/jaredhendrickson13/mail2beyond/tree/master/examples/configs). Configuration 
requirements and options are:

-----------------------------------------------------------------------------------------------------------------------
### `listeners`
A list of listeners for mail2beyond to use. At least one listener must be configured. Each listener has the following 
options available:

- **address**
  - _Required_: Yes
  - _Description_: The IP address this listener will listen on. This must be an address known to the local system.

- **port**
  - _Required_: Yes
  - _Description_: The TCP port this listen will listen on. This must be a numeric value within 1-65535.

- **enable_smtps**
  - _Required_: No
  - _Options_: [`true`, `false`]
  - _Default_: false
  - _Description_: Enables or disables SMTPS. If set to `true`, the `tls_cert` and `tls_key` options must be set. This
  option cannot be set to `true` if `enable_starttls` is also set to `true`.

- **enable_starttls**
  - _Required_: No
  - _Options_: [`true`, `false`]
  - _Default_: false
  - _Description_: Enables or disables advertisement for the SMTP protocol's STARTTLS function. STARTTLS allows an 
  insecure SMTP connections to upgrade to a secure connection. If set to `true`, the `tls_cert` and `tls_key` options 
  must be set. This option cannot be set to `true` if `enable_smtps` is also set to `true`.

- **require_starttls**
  - _Required_: No
  - _Options_: [`true`, `false`]
  - _Default_: false
  - _Description_: Enables or disables requirement for SMTP clients to use the STARTTLS function. If set to `true`, any 
  SMTP connection received must use the STARTTLS function to be accepted. This option is only available when 
  `enable_starttls` is set to `true`. 

- **tls_cert**
  - _Required_: Yes w/`enable_smtps` or `enable_starttls`
  - _Description_: The file path to the TLS certificate to use for secure connections. Only PEM formatted certificates
  are supported. This option is only available when `enable_starttls` is set to `true`. 
  
- **tls_key**
  - _Required_: Yes w/`enable_smtps` or `enable_starttls`
  - _Description_: The file path to the TLS private key to use for secure connections. Only PEM formatted private keys
  are supported. This option is only available when `enable_starttls` is set to `true`. 

- **minimum_tls_protocol**
  - _Required_: No
  - _Options_: [`tls1`, `tls1_1`, `tls1_2`, `tls1_3`]
  - _Default_: `tls1_2`
  - _Description_: Explicitly sets the minimum TLS protocol allowed by the server. Deprecated SSLv2 and SSLv3 are not 
  supported as these protocols contain major security vulnerabilities. This option is only available when 
  `enable_smtps` or `enable_starttls` is set to `true`. 

### `connectors`
A list of connectors for mail2beyond to enable. At least one connector item must be configured. Each connector has the 
following options available:

- **name**
  - _Required_: Yes
  - _Description_: The name to assign this connector. This name must be unique from any other connector defined in your 
  configuration. This name will be used to assign this connector to mappings in your configuration.

- **module**
  - _Required_: Yes
  - _Options_: [`void`, `smtp`, `google_chat`, `slack`]
  - _Description_: The module this connector will use. Multiple connectors can use the same underlying module.

- **config**
  - _Required_: Dependent on `module` selected.
  - _Description_: Additional module specific configurations. Refer to the 
  [connector-specific configurations section](#connector-specific-configuration) for requirements and options for the 
  specified module for this connector.

### `mappings`
A list of mapping rules to apply. Mappings allow you to apply logic to which connectors are used based on the SMTP 
headers of incoming SMTP messages. A specified header is checked for a specific pattern using regular expressions. If a
match is found, the connector specified in the mapping will be used to redirect the message. Mappings are checked in 
descending order and are used on a first-match basis. At least one mapping must be defined, and one mapping
must use the pattern `default` to assume a default if no other mappings were matched. Each mapping has the following 
options available:

- **pattern**
  - _Required_: Yes
  - _Description_: The regex pattern to use when checking for matches. 

- **connector**
  - _Required_: Yes
  - _Description_: The name of the connector use upon match. This must be the name of a connector defined in your
  configuration. Multiple mappings can use the same the connector.

- **parser**
  - _Required_: No
  - _Options_: [`auto`, `plain`, `html`]
  - _Default_: `auto`
  - _Description_: Explicitly set the content-type parser to use. By default, the `auto` parser will be chosen to 
  select the parser that best matches the SMTP message's content-type header. The `plain` parser will not parse the
  content body and is the fallback for the `auto` parser if no parser exists for the content-type. The `html` parser
  will parse the content body as HTML and convert it to a more human-readable markdown format.
  - _Notes_:
    - Some connector modules do not respect the `parser` option (e.g. `smtp`, `void`)
    - Even though the `html` parser converts the content to markdown, this does not guarantee the markdown content will
    be rendered by the upstream server (e.g. `google_chat`, `slack`)

- **field**
  - _Required_: No
  - _Default_: `from`
  - _Description_: The SMTP header to check for a match. Most commonly this will be `from` or `to` to match
  based on the sender or recipient of the SMTP message respectively.

## Connector-Specific Configuration
Connector modules may contain their own configurable options and requirements. Below are the available configuration
options available to each built-in connector module:

### `void`
The `void` connector module simply discards the received SMTP message. This connector module has no available 
configuration options. 

### `smtp`
The `smtp` connector module forwards received SMTP messages to an upstream SMTP server. On its own, Mail2Beyond does not
actually deliver the SMTP message to the recipient's mailbox. This connector module enables that functionality but 
requires an upstream SMTP to deliver the message. Available options for this module are:

- **smtp_host**
  - _Required_: Yes
  - _Description_: The IP address or hostname of the upstream SMTP server to forward messages to.

- **smtp_port**
  - _Required_: Yes
  - _Description_: The TCP port of the upstream SMTP server. This must be a numeric value within 1-65535. In most cases
  this is `25` for SMTP and `465` for SMTPS.

- **smtp_use_tls**
  - _Required_: No
  - _Options_: [`true`, `false`]
  - _Default_: `false`
  - _Description_: Enable or disable forwarding messages to the upstream SMTP server using SMTPS. If `true`, the 
  upstream SMTP server must be configured to allow SMTPS connections.

- **smtp_use_login**
  - _Required_: No
  - _Options_: [`true`, `false`]
  - _Default_: `false`
  - _Description_: Enable or disable SMTP authentication. If the upstream SMTP server requires authentication, this
  option should be set to `true`. If set to `true`, the `smtp_login_user` and `smtp_login_password` must be set.

- **smtp_login_user**
  - _Required_: Yes w/`smtp_use_login`
  - _Description_: The username to authenticate with.

- **smtp_login_password**
  - _Required_: Yes w/`smtp_use_login`
  - _Description_: The password to authenticate with.

### `slack`
The `slack` module allows SMTP messages to be redirected to a Slack channel using a webhook. A webhook must be
created for your channel beforehand. Available options for this module are:

- **webhook_url**
  - _Required_: Yes
  - _Description_: The full Slack webhook URL. For help to create a webhook, refer to 
  https://api.slack.com/messaging/webhooks

### `google_chat`
The `google_chat` module allows SMTP messages to be redirected to a Google Chat space using an app webhook. A webhook 
must be created for your space beforehand. Available options for this module are:

- **webhook_url**
  - _Required_: Yes
  - _Description_: The full Slack webhook URL. For help to create a webhook, refer to 
  https://developers.google.com/chat/how-tos/webhooks

## Starting the Server
Once you have your configuration file written, you can start the server by running the following command:
```commandline
mail2beyond --config /path/to/your/config.yml
```
