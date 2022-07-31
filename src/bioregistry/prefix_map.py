from typing import Optional, Tuple, Mapping

from pytrie import StringTrie

__all__ = [
    "PrefixMap",
]


class CompressTrie(StringTrie):
    def compress(self, uri: str) -> Optional[Tuple[str, str]]:
        """Compress a URI to a CURIE pair."""
        try:
            value, prefix = self.longest_prefix_item(uri)
        except KeyError:
            return None
        else:
            return prefix, uri[len(value):]


class PrefixMap:
    """

    Construct a prefix map
    >>> prefix_map = PrefixMap({
    ...    "CHEBI": "http://purl.obolibrary.org/obo/CHEBI_",
    ...    "MONDO": "http://purl.obolibrary.org/obo/MONDO_",
    ...    "GO": "http://purl.obolibrary.org/obo/GO_",
    ...    "OBO": "http://purl.obolibrary.org/obo/",
    ... })

    Example with ChEBI
    >>> prefix_map.compress("http://purl.obolibrary.org/obo/CHEBI_1")
    ('CHEBI', '1')
    >>> prefix_map.expand("CHEBI", "1")
    'http://purl.obolibrary.org/obo/CHEBI_1'

    Example with unparsable URI
    >>> prefix_map.compress("http://example.com/nope")

    Example with missing prefix
    >>> prefix_map.expand("xxx", "1")
    """

    def __init__(self, d: Mapping[str, str]):
        """

        :param d:
            A prefix map where the keys are prefixes (e.g., ``chebi``)
            and the values are URI prefixes (e.g., ``http://purl.obolibrary.org/obo/CHEBI_``).
        """
        self.d = dict(d)
        self.trie = CompressTrie(**{v: k for k, v in self.d.items()})

    def compress(self, uri: str) -> Optional[Tuple[str, str]]:
        """Compress a URI to a CURIE pair."""
        return self.trie.compress(uri)

    def expand(self, prefix: str, identifier: str) -> Optional[str]:
        """Expand a CURIE to a URI."""
        uri_prefix = self.d.get(prefix)
        if uri_prefix is None:
            return None
        return uri_prefix + identifier


def _main():
    map = PrefixMap({
        "CHEBI": "http://purl.obolibrary.org/obo/CHEBI_",
        "MONDO": "http://purl.obolibrary.org/obo/MONDO_",
        "GO": "http://purl.obolibrary.org/obo/GO_",
        "OBO": "http://purl.obolibrary.org/obo/",
    })
    res = map.compress("http://purl.obolibrary.org/obo/CHEBI_1")
    print(res)
    res = map.compress("aaaaaa")
    print(res)

    print(map.expand("CHEBI", "1234"))


if __name__ == '__main__':
    _main()
