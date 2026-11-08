from __future__ import annotations

from xml.etree import ElementTree as ET

import httpx
from pydantic import ValidationError

from app.schemas import CustomerOut

SOAP_NAMESPACE = "http://schemas.xmlsoap.org/soap/envelope/"
SERVICE_NAMESPACE = "urn:databridge:customers"


class SoapIntegrationError(Exception):
    """Base exception for SOAP integration failures."""


class SoapTransportError(SoapIntegrationError):
    """Raised when the SOAP endpoint cannot be reached."""


class SoapResponseError(SoapIntegrationError):
    """Raised when the SOAP response is invalid or contains a fault."""


def build_customer_envelope(customer_id: str) -> str:
    """Build a SOAP 1.1 request envelope for the fictional provider."""
    envelope = ET.Element(f"{{{SOAP_NAMESPACE}}}Envelope")
    body = ET.SubElement(envelope, f"{{{SOAP_NAMESPACE}}}Body")
    request = ET.SubElement(body, f"{{{SERVICE_NAMESPACE}}}GetCustomerRequest")
    identifier = ET.SubElement(request, f"{{{SERVICE_NAMESPACE}}}CustomerId")
    identifier.text = customer_id
    return ET.tostring(envelope, encoding="unicode", xml_declaration=True)


def _text_by_local_name(element: ET.Element, name: str) -> str:
    for child in element.iter():
        if child.tag.split("}")[-1] == name:
            return (child.text or "").strip()
    return ""


def parse_customer_response(xml_content: str) -> CustomerOut:
    """Parse an XML SOAP payload into the API's validated response model."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        raise SoapResponseError("SOAP response contains malformed XML.") from exc

    fault = next(
        (node for node in root.iter() if node.tag.split("}")[-1] == "Fault"),
        None,
    )
    if fault is not None:
        message = _text_by_local_name(fault, "faultstring") or "SOAP provider fault"
        raise SoapResponseError(message)

    values = {
        "customer_id": _text_by_local_name(root, "CustomerId"),
        "first_name": _text_by_local_name(root, "FirstName"),
        "last_name": _text_by_local_name(root, "LastName"),
        "email": _text_by_local_name(root, "Email"),
        "status": _text_by_local_name(root, "Status"),
    }
    if not all(values.values()):
        raise SoapResponseError("SOAP response is missing one or more customer fields.")

    try:
        return CustomerOut(**values)
    except ValidationError as exc:
        raise SoapResponseError("SOAP response does not match the expected customer format.") from exc


class SoapCustomerClient:
    def __init__(
        self,
        endpoint_url: str,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def get_customer(self, customer_id: str) -> CustomerOut:
        envelope = build_customer_envelope(customer_id)
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "GetCustomer",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    self.endpoint_url,
                    content=envelope.encode("utf-8"),
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise SoapTransportError("SOAP provider timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise SoapTransportError(
                f"SOAP provider returned HTTP {exc.response.status_code}."
            ) from exc
        except httpx.RequestError as exc:
            raise SoapTransportError("Could not reach the SOAP provider.") from exc

        return parse_customer_response(response.text)
