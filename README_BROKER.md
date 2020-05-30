# AWS Identity Broker

The identity broker is used to obtain short-lived and per-region credentials
for an account. Opt-in regions require the use of a long-lived credential (e.g.
IAM user), enabling global STS tokens, or an STS token sourced in that region.
The identity broker holds long-term credentials and uses them to acquire
short-term credentials in a given region. The broker also provides a list of
opt-in regions and should be used to enumerate regions.

For human-interactive users the identity broker performs OAUTH against GitHub
to chain the user's GitHub identity to the tokens they are given from the
broker. The broker also provides the user an API key to use when interacting
with the broker programmatically.

As of May 2020 the identity broker is not open sourced. If you want to provide
your own identity broker, the rest of this document specifies the URLs
endpoints and response formats to do so.

# The API

The identity broker API is a REST-ful service with an entry-point of
`/api/account`. All further navigation through the API follows links within the
hypertext.

**Note:** Outside of the account entry-point, URI formats should be considered
implementation details of the broker API and should never be templated. Beyond
the account entry-point, nothing in this specification is normative with
respect to URI paths and locations.

## Authentication

All requests to the API must be authenticated with a broker-specific key. That
key is provided to the broker in the `X-API-Key` header. When the broker
determines that the key is either expired or invalid it must redirect the user
to `/logout` to indicate that the user is logged out and must log-in again.

API keys are bearer tokens and thus must only be exchanged over HTTPS.

## Status Codes

`200 OK`: indicates that the request to the broker was successful.

`302 Found`: indicates that the broker is providing a redirect. Users should
check the redirect, if it is to the location `/logout` the user should consider
themselves logged out and proceed to login. This condition should not be
followed. Otherwise the user should follow all redirects.

`400 Bad Request`: indicates that some part of the request is invalid as
submitted. The hypertext MAY provide a description of this error and how to
remedy it.

`429 Rate Limit Exceeded`: indicates that the broker has rate-limited the user.
A user should discontinue requests to the broker immediately and wait for at
least 30 seconds before continuing their requests. The rate limit parameters
are specific to the broker and not controlled by this spec.

`500 Server Error`: indicates a server error condition that is not under the
user's control.

## Account End-point

The account end-point acts as a index of the rest of the API. It presents a
list of accounts to which the user has access as well as links to navigate
further into the API. The format of this document is:

`short_name` (string): a url-safe name for the account, used as the primary
account identifier within the broker.

`account_number` (integer): the AWS account number

`name` (string): a user-friendly name for the account

`console_redirect_url` (uri): a URI that, when followed, leads to a resource
that redirects the user to an authenticated console session.

`get_console_url` (uri): a URI that, when followed, leads to a console URL
resource.

`credentials_url` (uri):  a URI that, when followed, leads to a region list
resource.

`global_credential_url` (uri): a URI that, when followed, leads to a credential
resource which provides a credential usable by all non-opt-in regions. The
contents of this resource are a STS global credential which is not usable in
opt-in regions.

```
[
    {
        "short_name": "primary-account",
        "account_number": 123456789012,
        "name": "Primary AWS Account",
        "console_redirect_url": "https://broker/api/account/primary-account/console?redirect=1",
        "get_console_url": "https://broker/api/account/primary-account/console",
        "credentials_url": "https://broker/api/account/primary-account/credentials",
        "global_credential_url": "https://broker/api/account/primary-account/credentials/global"
    }
]
```

## Console URL Resource

**Note:** This resource is not used by the build scripts.

The console URL resource provides a URL to the AWS console. This resource is
designed for interactive use.

When provided the query parameter `redirect` with a value of `1` this resource
will not generate a body and will instead redirect to the URL that would have
been returned for `console_url`.

`console_url` (uri): a link to the AWS console with authentication credentials
embedded.

```
{
    "console_url": "https://signin.aws.amazon.com/federation?..."
}
```

## Credential Resource

The credential resource provides a set of credentials that can be used to
configure AWS tools to access an account.

`access_key` (string): the AWS access key ID

`secret_key` (string): the AWS secret access key

`session_token` (string): the AWS session token

`expiration` (iso-formatted date): the date and time when the credential will
expire

```
{
    "access_key": "ASIA123ABC456DEF567G",
    "secret_key": "r7KcIuGdPwoUG2YOLISX2XDrVts55IFGTGaY5Tqa",
    "session_token": "7C7FyvzyneaS/eRCVDcjHOSTTIHQyvhGqW...",
    "expiration": "2020-01-01T00:00:00Z"
}
```

## Region List Resource

The region list resource provides a list of regions associated with the account
both opted-in and not. For opted-in regions the resource includes a link to a
credential resource for that region.

`name` (string): AWS name for the region

`enabled` (boolean): indicates if the region is enabled and opted-in for this
account.

`credentials_url` (uri): a URI that, when followed, leads to a credential
resource containing a credential for access to that region. The credential
provided will be usable against the region-local STS endpoint for the specified
region. This also applies for classic regions, which typically use a global
endpoint and credential. The returned credential is scoped to the acquiring
region and may not be usable against the global endpoints or a different
regional endpoint.

```
[
    {
        "name": "af-south-1",
        "enabled": false
    },
    {
        "name": "us-west-2",
        "enabled": true,
        "credentials_url": "https://broker/api/account/primary-account/credentials/us-west-2"
    }
]
```
