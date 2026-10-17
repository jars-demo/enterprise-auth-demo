"""Read a SAML 2.0 assertion and check the conditions an app must enforce.

This does NOT verify the XML signature. Signature checks in SAML are where real attacks live
(signature wrapping, comments in NameID), so production code uses a maintained library such as
python3-saml or xmlsec, and parses XML with defusedxml. Everything after the signature, the
checks below, is still your app's job.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime

NS = {"saml": "urn:oasis:names:tc:SAML:2.0:assertion"}


@dataclass
class Assertion:
    issuer: str
    name_id: str
    audience: str
    recipient: str
    not_before: datetime
    not_on_or_after: datetime
    attributes: dict[str, list[str]] = field(default_factory=dict)


def when(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def parse(xml: str) -> Assertion:
    root = ET.fromstring(xml)
    conditions = root.find("saml:Conditions", NS)
    confirmation = root.find(".//saml:SubjectConfirmationData", NS)
    if conditions is None or confirmation is None:
        raise ValueError("assertion has no Conditions or SubjectConfirmationData")
    attributes = {
        attr.get("Name", ""): [v.text or "" for v in attr.findall("saml:AttributeValue", NS)]
        for attr in root.findall(".//saml:Attribute", NS)
    }
    return Assertion(
        issuer=root.findtext("saml:Issuer", "", NS),
        name_id=root.findtext(".//saml:NameID", "", NS),
        audience=root.findtext(".//saml:Audience", "", NS),
        recipient=confirmation.get("Recipient", ""),
        not_before=when(conditions.get("NotBefore", "")),
        not_on_or_after=when(conditions.get("NotOnOrAfter", "")),
        attributes=attributes,
    )


def problems(
    assertion: Assertion, issuer: str, audience: str, acs_url: str, now: datetime | None = None
) -> list[str]:
    """Everything wrong with this assertion for this app. Empty means accept."""
    now = now or datetime.now(UTC)
    found = []
    if assertion.issuer != issuer:
        found.append(f"issued by {assertion.issuer!r}, not by our identity provider")
    if assertion.audience != audience:
        found.append(f"meant for {assertion.audience!r}, not for this app")
    if assertion.recipient != acs_url:
        found.append(f"sent to {assertion.recipient!r}, not to our ACS URL")
    if now < assertion.not_before:
        found.append("not valid yet")
    if now >= assertion.not_on_or_after:
        found.append(f"expired at {assertion.not_on_or_after.isoformat()}")
    return found
