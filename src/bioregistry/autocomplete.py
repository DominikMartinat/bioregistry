import re
from typing import List, Optional

from pydantic import BaseModel

from bioregistry import manager
from bioregistry.constants import BIOREGISTRY_REMOTE_URL

__all__ = [
    "Match",
    "AutocompleteResult",
    "autocomplete_prefix",
    "autocomplete_omni",
]


class Match(BaseModel):
    prefix: str
    name: str
    synonym: str
    start: int


REASON_MATCHED = "matched prefix"
REASON_SEARCHED = "searched prefix"
REASON_BAD_PREFIX = "bad prefix"
REASON_NO_PATTERN = "no pattern"
REASON_PASSED_VALIDATION = "passed validation"
REASON_FAILED_VALIDATION = "failed validation"


class AutocompleteResult(BaseModel):
    query: str
    reason: str
    prefix: Optional[str]
    identifier: Optional[str]
    pattern: Optional[str]
    url: Optional[str]
    matches: Optional[List[Match]]
    success: bool = True


def autocomplete_prefix(query: str) -> AutocompleteResult:
    norm_prefix = manager.normalize_prefix(query)
    if norm_prefix:
        return AutocompleteResult(
            query=query,
            prefix=norm_prefix,
            reason=REASON_MATCHED,
            url=f"{BIOREGISTRY_REMOTE_URL.rstrip()}/{norm_prefix}",
        )
    norm_query = manager.synonyms.norm(query)
    matches = [
        Match(
            prefix=prefix,
            name=manager.get_name(prefix),
            synonym=synonym,
            start=synonym.index(norm_query),
        )
        for synonym, prefix in manager.synonyms.items()
        if norm_query in synonym
    ]
    return AutocompleteResult(
        query=query,
        matches=matches,
        reason=REASON_SEARCHED,
    )


def autocomplete_omni(query: str) -> AutocompleteResult:
    r"""Run the autocomplete algorithm.

    :param query: The query string
    :return: A dictionary with the autocomplete results.

    Before completion is of prefix:

    >>> autocomplete_omni('cheb')
    {'query': 'cheb', 'results': ['chebi'], 'success': True, 'reason': 'searched prefix', 'url': None}

    If only prefix is complete:

    >>> autocomplete_omni('chebi')
    {'query': 'chebi', 'results': ['chebi'], 'success': True, 'reason': 'matched prefix', 'url': 'https://bioregistry.io/chebi'}

    Using a synonym:

    >>> autocomplete_omni('pmid')
    {'query': 'pmid', 'results': ['pubmed'], 'success': True, 'reason': 'matched prefix', 'url': 'https://bioregistry.io/pubmed'}

    Not matching the pattern:

    >>> autocomplete_omni('chebi:NOPE')
    {'query': 'chebi:NOPE', 'prefix': 'chebi', 'pattern': '^\\d+$', 'identifier': 'NOPE', 'success': False, 'reason': 'failed validation', 'url': None}

    Matching the pattern:

    >>> autocomplete_omni('chebi:1234')
    {'query': 'chebi:1234', 'prefix': 'chebi', 'pattern': '^\\d+$', 'identifier': '1234', 'success': True, 'reason': 'passed validation', 'url': 'https://bioregistry.io/chebi:1234'}
    """  # noqa: E501
    if ":" not in query:
        return autocomplete_prefix(query)
    prefix, identifier = query.split(":", 1)
    norm_prefix = manager.normalize_prefix(prefix)
    if norm_prefix is None:
        return AutocompleteResult(
            query=query,
            prefix=prefix,
            identifier=identifier,
            success=False,
            reason=REASON_BAD_PREFIX,
        )
    pattern = manager.get_pattern(prefix)
    if pattern is None:
        success = True
        reason = REASON_NO_PATTERN
        url = manager.get_bioregistry_iri(prefix, identifier)
    elif re.match(pattern, identifier):
        success = True
        reason = REASON_PASSED_VALIDATION
        url = manager.get_bioregistry_iri(prefix, identifier)
    else:
        # Fails on GOGO
        # Fails on double HGNC
        success = False
        reason = REASON_FAILED_VALIDATION
        url = None
    return AutocompleteResult(
        query=query,
        prefix=prefix,
        pattern=pattern,
        identifier=identifier,
        success=success,
        reason=reason,
        url=url,
    )
