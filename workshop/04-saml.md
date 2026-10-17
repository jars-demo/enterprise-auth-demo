# SAML in one page

> The XML standard that most enterprise customers still ask for. The same ideas as OIDC, in a different envelope, with sharper edges.

**Time:** 12 minutes

## Goal

Read a SAML assertion, map its parts to the OIDC claims you already know, and run the checks an app must make.

## The same story, in XML

Open `lab/samples/assertion.xml`. It is the trimmed version of what an identity provider posts to your app after sign-in:

| SAML                                | OIDC equivalent    |
| ----------------------------------- | ------------------ |
| `Issuer`                            | `iss`              |
| `NameID`                            | `sub` or `email`   |
| `Audience`                          | `aud`              |
| `Conditions NotOnOrAfter`           | `exp`              |
| `SubjectConfirmationData Recipient` | the `redirect_uri` |
| `AttributeStatement`                | extra claims       |
| `ds:Signature`                      | the JWT signature  |

The flow differs too. There is no code exchange: the browser posts the signed assertion straight to your app's Assertion Consumer Service (ACS) URL. That is why the signature and the conditions carry all the weight.

## Check it

```bash
uv run python -m sso saml samples/assertion.xml
```

```text
user        alice@acme.test
attributes  {'tenant': ['acme'], 'roles': ['admin']}

  reject: expired at 2026-03-02T09:05:00+00:00
```

The assertion was valid for five minutes in March 2026. Rejecting it now is correct. Check it as of the moment it was issued:

```bash
uv run python -m sso saml samples/assertion.xml --now 2026-03-02T09:01:00Z
```

```text
  accept (the signature is not checked here, see saml.py)
```

## The part this lab skips on purpose

`lab/sso/saml.py` does not verify the XML signature, and says so at the top. XML signatures sign one element inside a document, and attackers move elements around so that the signed part and the part your code reads are different (signature wrapping). Real apps use a maintained library such as python3-saml or xmlsec, and parse with defusedxml. Writing your own SAML signature check is the classic mistake to avoid.

## Check it works

- The sample is rejected as expired, and accepted with `--now 2026-03-02T09:01:00Z`.
- You can map five SAML elements to their OIDC claims.

## Exercise

Copy the sample to `samples/evil.xml` and change one thing at a time: the `Audience`, then the `Recipient`, then `NotBefore` to a time after `--now`. Run the check after each change and read the reason it gives. Which of these would a signature have caught, and which only your own checks catch?

### More to try

- Add an `InResponseTo` check: SAML's version of `state`. Where would your app store the request id it is waiting for?
- Look at your identity provider's SAML app setup screen. Find the ACS URL, the Entity ID (audience) and the attribute mapping.
