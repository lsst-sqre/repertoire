"""In-memory store of built VOResource records (keyed by ivoid)."""

from datetime import datetime

from vo_models.voresource.models import Resource


class RecordStore:
    """Store of VOResource records.

    Records are keyed by IVOID and queried by the OAI-PMH handler to serve
    ``GetRecord``, ``ListIdentifiers``, and ``ListRecords`` requests.

    Parameters
    ----------
    records
        Mapping of IVOID strings to built VOResource records.
    """

    def __init__(self, records: dict[str, Resource]) -> None:
        self._records = records

    def get(self, record_id: str) -> Resource | None:
        """Return a single record by IVOID, or ``None`` if not found.

        Parameters
        ----------
        record_id
            The IVOID of the record to retrieve.

        Returns
        -------
        Resource | None
            The matching record, or ``None`` if the IVOID is not in the store.
        """
        return self._records.get(record_id)

    def all(self) -> list[Resource]:
        """Return all records in the store.

        Returns
        -------
        list[Resource]
            All VOResource records.
        """
        return list(self._records.values())

    def earliest_datestamp(self) -> datetime | None:
        """Return the earliest ``created`` datestamp across all records.

        Used to populate the ``earliestDatestamp`` field in the OAI-PMH
        ``Identify`` response.

        Returns
        -------
        datetime | None
            The earliest creation datestamp, or ``None`` if the store is empty.
        """
        if not self._records:
            return None
        return min(record.created for record in self._records.values())
