"""Constants for the IVOA OAI-PMH publishing registry."""

from pydantic import AnyUrl, TypeAdapter

__all__ = [
    "DC_NS",
    "IVO_MANAGED_SET",
    "IVO_MANAGED_SET_NAME",
    "IVO_VOR_NAMESPACE",
    "IVO_VOR_PREFIX",
    "IVO_VOR_SCHEMA",
    "OAI_DC_NS",
    "OAI_DC_PREFIX",
    "OAI_DC_SCHEMA",
    "OAI_DELETED_RECORD_POLICY",
    "OAI_ERRORS",
    "OAI_GRANULARITY",
    "OAI_NS",
    "OAI_SCHEMA",
    "SIA_STANDARD_ID",
    "SODA_ASYNC_STANDARD_ID",
    "SODA_SYNC_STANDARD_ID",
    "SUPPORTED_PREFIXES",
    "TAP_OUTPUT_FORMAT_MIME",
    "TAP_UPLOAD_ID",
    "VO_SUBJECT",
    "XSI_NS",
    "anyurl",
]

# vo_modelss uses AnyUrl so we use a TypeAdapter to validate our strings
anyurl: TypeAdapter[AnyUrl] = TypeAdapter(AnyUrl)
"""Adapter for validating and constructing Pydantic AnyUrl objects."""

# OAI-PMH namespaces and schema locations
OAI_NS = "http://www.openarchives.org/OAI/2.0/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
OAI_SCHEMA = (
    "http://www.openarchives.org/OAI/2.0/"
    " http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"
)
DC_NS = "http://purl.org/dc/elements/1.1/"

# oai_dc metadata format
OAI_DC_PREFIX = "oai_dc"
OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"
OAI_DC_SCHEMA = "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"

# ivo_vor metadata format
IVO_VOR_PREFIX = "ivo_vor"
IVO_VOR_SCHEMA = "http://www.ivoa.net/xml/VOResource/VOResource-v1.1.xsd"
IVO_VOR_NAMESPACE = "http://www.ivoa.net/xml/RegistryInterface/v1.0"

# OAI-PMH protocol values
IVO_MANAGED_SET = "ivo_managed"
IVO_MANAGED_SET_NAME = "IVOA Managed records"
OAI_DELETED_RECORD_POLICY = "no"
OAI_GRANULARITY = "YYYY-MM-DDThh:mm:ssZ"

SUPPORTED_PREFIXES = (IVO_VOR_PREFIX, OAI_DC_PREFIX)

# IVOA standard IDs
SIA_STANDARD_ID = "ivo://ivoa.net/std/SIA#query-2.0"
SODA_SYNC_STANDARD_ID = "ivo://ivoa.net/std/SODA#sync-1.0"
SODA_ASYNC_STANDARD_ID = "ivo://ivoa.net/std/SODA#async-1.0"

# TAP output format
TAP_OUTPUT_FORMAT_MIME = "application/x-votable+xml"

# TAP Upload
TAP_UPLOAD_ID = "ivo://ivoa.net/std/DALI#upload"

# VOResource subject keyword used on all records produced by this registry
VO_SUBJECT = ["virtual observatory"]

OAI_ERRORS: dict[str, str] = {
    "badArgument": (
        "The request includes illegal arguments or is missing"
        " required arguments."
    ),
    "badResumptionToken": "The resumption token is invalid or expired.",
    "badVerb": "Value of the verb argument is not a legal OAI-PMH verb.",
    "cannotDisseminateFormat": (
        "The metadata format identified by metadataPrefix is not supported."
    ),
    "idDoesNotExist": (
        "The value of the identifier argument is unknown or illegal."
    ),
    "noRecordsMatch": "The combination of arguments results in an empty list.",
    "noMetadataFormats": "There are no metadata formats available.",
}
