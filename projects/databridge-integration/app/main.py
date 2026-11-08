from xml.etree import ElementTree as ET

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import Response

from app.config import settings
from app.schemas import CustomerOut
from app.soap_client import (
    SERVICE_NAMESPACE,
    SOAP_NAMESPACE,
    SoapCustomerClient,
    SoapResponseError,
    SoapTransportError,
)

app = FastAPI(
    title=settings.app_name,
    description="A demonstration REST facade for a fictional SOAP/XML customer service.",
    version="1.0.0",
)


def get_soap_client() -> SoapCustomerClient:
    return SoapCustomerClient(
        endpoint_url=settings.soap_endpoint_url,
        timeout_seconds=settings.soap_timeout_seconds,
    )


@app.get("/health", tags=["Operations"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/v1/customers/{customer_id}",
    response_model=CustomerOut,
    tags=["Customers"],
)
async def get_customer(
    customer_id: str,
    soap_client: SoapCustomerClient = Depends(get_soap_client),
) -> CustomerOut:
    if not customer_id.strip():
        raise HTTPException(status_code=400, detail="Customer ID must not be empty.")

    try:
        return await soap_client.get_customer(customer_id)
    except (SoapTransportError, SoapResponseError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/mock-soap", include_in_schema=False)
async def mock_soap_provider(request: Request) -> Response:
    """Local SOAP 1.1 provider used to make the portfolio demo self-contained."""
    raw_body = await request.body()
    try:
        envelope = ET.fromstring(raw_body)
    except ET.ParseError:
        return Response(
            content=(
                f'<soap:Envelope xmlns:soap="{SOAP_NAMESPACE}"><soap:Body>'
                "<soap:Fault><faultstring>Malformed request XML</faultstring></soap:Fault>"
                "</soap:Body></soap:Envelope>"
            ),
            media_type="text/xml",
            status_code=400,
        )

    customer_id = ""
    for node in envelope.iter():
        if node.tag.split("}")[-1] == "CustomerId":
            customer_id = (node.text or "").strip()
            break

    if customer_id != "CUST-1001":
        body = f"""<soap:Envelope xmlns:soap="{SOAP_NAMESPACE}">
          <soap:Body><soap:Fault>
            <faultcode>soap:Client</faultcode>
            <faultstring>Customer not found</faultstring>
          </soap:Fault></soap:Body>
        </soap:Envelope>"""
        return Response(content=body, media_type="text/xml")

    body = f"""<soap:Envelope xmlns:soap="{SOAP_NAMESPACE}" xmlns:svc="{SERVICE_NAMESPACE}">
      <soap:Body><svc:GetCustomerResponse><svc:Customer>
        <svc:CustomerId>CUST-1001</svc:CustomerId>
        <svc:FirstName>Avery</svc:FirstName>
        <svc:LastName>Morgan</svc:LastName>
        <svc:Email>avery.morgan@example.test</svc:Email>
        <svc:Status>active</svc:Status>
      </svc:Customer></svc:GetCustomerResponse></soap:Body>
    </soap:Envelope>"""
    return Response(content=body, media_type="text/xml")
