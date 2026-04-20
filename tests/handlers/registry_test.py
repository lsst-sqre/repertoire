"""Tests for the repertoire.handlers.registry module and routes."""

import re

import pytest
from httpx import AsyncClient
from safir.testing.data import Data


def normalize_oai_xml(xml: str) -> str:
    """Normalize OAI-PMH XML by fixing timestamps and removing date filters."""
    xml = re.sub(
        r"<responseDate>.*?</responseDate>",
        "<responseDate>1970-01-01T00:00:00Z</responseDate>",
        xml,
    )
    xml = re.sub(
        r"<datestamp>.*?</datestamp>",
        "<datestamp>1970-01-01T00:00:00Z</datestamp>",
        xml,
    )
    xml = re.sub(
        r' updated="[^"]*"', ' updated="1970-01-01T00:00:00.000Z"', xml
    )
    return re.sub(r' (?:from|until)="[^"]*"', "", xml)


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_identify(data: Data, client: AsyncClient) -> None:
    r = await client.get("/registry/oai?verb=Identify")
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/identify.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_list_metadata_formats(data: Data, client: AsyncClient) -> None:
    r = await client.get("/registry/oai?verb=ListMetadataFormats")
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/list_metadata_formats.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_list_sets(data: Data, client: AsyncClient) -> None:
    r = await client.get("/registry/oai?verb=ListSets")
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/list_sets.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_list_identifiers(data: Data, client: AsyncClient) -> None:
    r = await client.get(
        "/registry/oai?verb=ListIdentifiers&metadataPrefix=ivo_vor"
    )
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/list_identifiers.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
@pytest.mark.parametrize(
    "url",
    [
        "/registry/oai?verb=NotAVerb",
        "/registry/oai",
    ],
)
async def test_bad_verb(url: str, data: Data, client: AsyncClient) -> None:
    r = await client.get(url)
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/bad_verb.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_cannot_disseminate_format(
    data: Data, client: AsyncClient
) -> None:
    r = await client.get(
        "/registry/oai?verb=ListIdentifiers&metadataPrefix=marc21"
    )
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text),
        "output/registry/cannot_disseminate_format.xml",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_id_does_not_exist(data: Data, client: AsyncClient) -> None:
    r = await client.get(
        "/registry/oai?verb=GetRecord&metadataPrefix=ivo_vor&identifier=ivo://example.com/nonexistent"
    )
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/id_does_not_exist.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_list_records(data: Data, client: AsyncClient) -> None:
    r = await client.get(
        "/registry/oai?verb=ListRecords&metadataPrefix=ivo_vor"
    )
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/list_records.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_get_record(data: Data, client: AsyncClient) -> None:
    r = await client.get(
        "/registry/oai?verb=GetRecord&metadataPrefix=ivo_vor&identifier=ivo://example.com/tap"
    )
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/get_record.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_get_record_missing_id(data: Data, client: AsyncClient) -> None:
    r = await client.get("/registry/oai?verb=GetRecord&metadataPrefix=ivo_vor")
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/get_record_missing_id.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_get_record_wrong_prefix(
    data: Data, client: AsyncClient
) -> None:
    r = await client.get(
        "/registry/oai?verb=GetRecord&metadataPrefix=not_ivo_vor&identifier"
        "=ivo://example.com/tap"
    )
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text),
        "output/registry/get_record_wrong_prefix.xml",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
@pytest.mark.parametrize(
    "url",
    [
        "/registry/oai?verb=ListRecords&metadataPrefix=ivo_vor&from=1960-01-01",
        "/registry/oai?verb=ListRecords&metadataPrefix=ivo_vor&from=1960-01-01T00:00:00Z",
        "/registry/oai?verb=ListRecords&metadataPrefix=ivo_vor&until=2026-12-12",
        "/registry/oai?verb=ListRecords&metadataPrefix=ivo_vor&until=2026-12-12T00:00:00Z",
    ],
)
async def test_list_records_date_filter(
    url: str, data: Data, client: AsyncClient
) -> None:
    r = await client.get(url)
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/list_records.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
@pytest.mark.parametrize(
    "url",
    [
        "/registry/oai?verb=ListRecords&metadataPrefix=ivo_vor&from=2026-12-12",
        "/registry/oai?verb=ListRecords&metadataPrefix=ivo_vor&from=1960-01-01&until=1961-01-01",
    ],
)
async def test_list_records_no_results(
    url: str, data: Data, client: AsyncClient
) -> None:
    r = await client.get(url)
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/list_no_records.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_list_metadata_formats_bad_identifier(
    data: Data, client: AsyncClient
) -> None:
    r = await client.get(
        "/registry/oai?verb=ListMetadataFormats"
        "&identifier=ivo://example.com/nonexistent"
    )
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text),
        "output/registry/list_metadata_formats_bad_id.xml",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_bad_argument_duplicate_params(
    data: Data, client: AsyncClient
) -> None:
    r = await client.get("/registry/oai?verb=Identify&verb=Identify")
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text),
        "output/registry/bad_argument_duplicate.xml",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_bad_argument_forbidden(data: Data, client: AsyncClient) -> None:
    r = await client.get("/registry/oai?verb=Identify&metadataPrefix=ivo_vor")
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text),
        "output/registry/bad_argument_forbidden.xml",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_bad_argument_invalid_date(
    data: Data, client: AsyncClient
) -> None:
    r = await client.get(
        "/registry/oai?verb=ListRecords&metadataPrefix=ivo_vor&from=not-a-date"
    )
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text),
        "output/registry/bad_argument_invalid_date.xml",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_bad_argument_from_after_until(
    data: Data, client: AsyncClient
) -> None:
    r = await client.get(
        "/registry/oai?verb=ListRecords&metadataPrefix=ivo_vor"
        "&from=2026-01-01&until=2025-01-01"
    )
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text),
        "output/registry/bad_argument_date_range.xml",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_bad_argument_mixed_granularity(
    data: Data, client: AsyncClient
) -> None:
    r = await client.get(
        "/registry/oai?verb=ListRecords&metadataPrefix=ivo_vor"
        "&from=2025-01-01&until=2025-01-01T00:00:00Z"
    )
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text),
        "output/registry/bad_argument_mixed_granularity.xml",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_post_identify(data: Data, client: AsyncClient) -> None:
    r = await client.post("/registry/oai", data={"verb": "Identify"})
    assert r.status_code == 200
    data.assert_text_matches(
        normalize_oai_xml(r.text), "output/registry/identify.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("app", ["registry"], indirect=True)
async def test_list_identifiers_excludes_unregistered_services(
    client: AsyncClient,
) -> None:
    r = await client.get(
        "/registry/oai?verb=ListIdentifiers&metadataPrefix=ivo_vor"
    )
    assert r.status_code == 200
    assert "ssotap" not in r.text
    for ivoid in (
        "ivo://example.com/registry",
        "ivo://example.com",
        "ivo://example.com/org",
        "ivo://example.com/tap",
        "ivo://example.com/cutout",
        "ivo://example.com/sia/dp02",
        "ivo://example.com/sia/dp1",
    ):
        assert ivoid in r.text
