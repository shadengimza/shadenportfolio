import pytest

from app.soap_client import SoapResponseError, build_customer_envelope, parse_customer_response

CUSTOMER_XML = """<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:svc="urn:example:customers">
  <soap:Body><svc:GetCustomerResponse><svc:Customer>
    <svc:CustomerId>CUST-1001</svc:CustomerId>
    <svc:FirstName>Avery</svc:FirstName>
    <svc:LastName>Morgan</svc:LastName>
    <svc:Email>avery.morgan@example.test</svc:Email>
    <svc:Status>active</svc:Status>
  </svc:Customer></svc:GetCustomerResponse></soap:Body>
</soap:Envelope>
"""


def test_build_customer_envelope_contains_identifier() -> None:
    envelope = build_customer_envelope("CUST-1001")
    assert "CUST-1001" in envelope
    assert "GetCustomerRequest" in envelope
    assert "Envelope" in envelope


def test_parse_customer_response_maps_xml_to_model() -> None:
    result = parse_customer_response(CUSTOMER_XML)
    assert result.customer_id == "CUST-1001"
    assert result.first_name == "Avery"
    assert result.status == "active"


def test_parse_customer_response_raises_on_malformed_xml() -> None:
    with pytest.raises(SoapResponseError, match="malformed XML"):
        parse_customer_response("<not-closed>")


def test_parse_customer_response_raises_on_soap_fault() -> None:
    fault_xml = """<Envelope><Body><Fault><faultstring>Customer not found</faultstring></Fault></Body></Envelope>"""
    with pytest.raises(SoapResponseError, match="Customer not found"):
        parse_customer_response(fault_xml)


def test_parse_customer_response_rejects_missing_fields() -> None:
    xml = "<Envelope><Body><CustomerId>CUST-1</CustomerId></Body></Envelope>"
    with pytest.raises(SoapResponseError, match="missing"):
        parse_customer_response(xml)
