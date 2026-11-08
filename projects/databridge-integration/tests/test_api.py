import httpx
from fastapi.testclient import TestClient

from app.main import app, get_soap_client
from app.soap_client import SoapCustomerClient

CUSTOMER_XML = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:svc="urn:example">
<soap:Body><svc:Customer><svc:CustomerId>CUST-1001</svc:CustomerId>
<svc:FirstName>Avery</svc:FirstName><svc:LastName>Morgan</svc:LastName>
<svc:Email>avery.morgan@example.test</svc:Email><svc:Status>active</svc:Status>
</svc:Customer></soap:Body></soap:Envelope>"""
FAULT_XML = """<Envelope><Body><Fault><faultstring>Customer not found</faultstring></Fault></Body></Envelope>"""


def client_with_soap_response(xml_payload: str) -> TestClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert "text/xml" in request.headers["content-type"]
        assert "CustomerId" in request.content.decode()
        return httpx.Response(200, text=xml_payload, headers={"Content-Type": "text/xml"})

    app.dependency_overrides[get_soap_client] = lambda: SoapCustomerClient(
        "https://mock-soap.example.test/service",
        transport=httpx.MockTransport(handler),
    )
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_customer_endpoint_returns_normalized_json() -> None:
    response = client_with_soap_response(CUSTOMER_XML).get("/api/v1/customers/CUST-1001")
    assert response.status_code == 200
    assert response.json() == {
        "customer_id": "CUST-1001",
        "first_name": "Avery",
        "last_name": "Morgan",
        "email": "avery.morgan@example.test",
        "status": "active",
    }


def test_customer_endpoint_maps_soap_fault_to_gateway_error() -> None:
    response = client_with_soap_response(FAULT_XML).get("/api/v1/customers/CUST-9999")
    assert response.status_code == 502
    assert response.json()["detail"] == "Customer not found"


def test_mock_soap_provider_returns_customer_xml() -> None:
    envelope = (
        '<?xml version="1.0"?><soap:Envelope '
        'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:svc="urn:databridge:customers"><soap:Body>'
        '<svc:GetCustomerRequest><svc:CustomerId>CUST-1001</svc:CustomerId>'
        '</svc:GetCustomerRequest></soap:Body></soap:Envelope>'
    )
    response = TestClient(app).post("/mock-soap", content=envelope, headers={"Content-Type": "text/xml"})
    assert response.status_code == 200
    assert "avery.morgan@example.test" in response.text
