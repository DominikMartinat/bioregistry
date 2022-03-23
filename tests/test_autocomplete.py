import unittest

from bioregistry.autocomplete import AutocompleteResult, Match, autocomplete_omni, autocomplete_prefix

PREFIX_QUERIES = queries = [
    (
        "chebi",
        AutocompleteResult(
            query="chebi",
            prefix="chebi",
            success=True,
            reason="matched prefix",
            url="https://bioregistry.io/chebi",
        ),
    ),
    (
        "cheb",
        AutocompleteResult(
            query="cheb",
            success=True,
            reason="searched prefix",
            matches=[
                Match(
                    prefix="chebi",
                    synonym="chebi",
                    start=0,
                ),
                Match(
                    prefix="chebi",
                    synonym="chebiid",
                    start=0,
                ),
                Match(
                    prefix="goche",
                    synonym="gochebi",
                    start=2,
                ),
            ],
        ),
    ),
    (
        "pmid",
        AutocompleteResult(
            query="pmid",
            prefix="pubmed",
            success=True,
            reason="matched prefix",
            url="https://bioregistry.io/pubmed",
        ),
    )
]


class TestAutocomplete(unittest.TestCase):
    def test_autocomplete_prefix(self):
        """Test autocompletion of prefixes."""
        for query, results in PREFIX_QUERIES:
            with self.subTest(query=query):
                self.assertEqual(results.dict(), autocomplete_prefix(query).dict())

    def test_autocomplete_omni(self):
        """Test the full autocomplete tool."""
        queries = PREFIX_QUERIES + [

        ]

        for query, results in queries:
            with self.subTest(query=query):
                self.assertEqual(results.dict(), autocomplete_omni(query).dict())
