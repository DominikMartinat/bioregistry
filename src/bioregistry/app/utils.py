# -*- coding: utf-8 -*-

"""Utility functions for the Bioregistry :mod:`flask` app."""

import json
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml
from flask import abort, current_app, redirect, render_template, request, url_for
from pydantic import BaseModel

import bioregistry
from bioregistry.schema import Resource, sanitize_model
from bioregistry.utils import extended_encoder


def _get_resource_providers(
    prefix: str, identifier: Optional[str]
) -> Optional[List[Dict[str, Any]]]:
    if identifier is None:
        return None
    rv = []
    for metaprefix, uri in bioregistry.get_providers_list(prefix, identifier):
        if metaprefix == "default":
            metaprefix = prefix
            name = bioregistry.get_name(prefix)
            homepage = bioregistry.get_homepage(prefix)
        else:
            name = bioregistry.get_registry_name(metaprefix)
            homepage = bioregistry.get_registry_homepage(metaprefix)
        rv.append(
            dict(
                metaprefix=metaprefix,
                homepage=homepage,
                name=name,
                uri=uri,
            )
        )
    return rv


def _get_resource_mapping_rows(resource: Resource) -> Optional[List[Mapping[str, Any]]]:
    mappings = resource.get_mappings()
    if mappings is None:
        return None
    return [
        dict(
            metaprefix=metaprefix,
            metaresource=bioregistry.get_registry(metaprefix),
            xref=xref,
            homepage=bioregistry.get_registry_homepage(metaprefix),
            name=bioregistry.get_registry_name(metaprefix),
            uri=bioregistry.get_registry_provider_uri_format(metaprefix, xref),
        )
        for metaprefix, xref in mappings.items()
    ]


def _normalize_prefix_or_404(prefix: str, endpoint: Optional[str] = None):
    try:
        norm_prefix = bioregistry.normalize_prefix(prefix)
    except ValueError:
        norm_prefix = None
    if norm_prefix is None:
        return render_template("resolve_errors/missing_prefix.html", prefix=prefix), 404
    elif endpoint is not None and norm_prefix != prefix:
        return redirect(url_for(endpoint, prefix=norm_prefix))
    return norm_prefix


def _search(q: str) -> List[str]:
    q_norm = q.lower()
    return [
        prefix
        for prefix, resource in bioregistry.read_registry().items()
        if q_norm in prefix or q_norm in resource.get_synonyms()
    ]


def _get_identifier(prefix: str, identifier: str) -> Mapping[str, Any]:
    prefix = _normalize_prefix_or_404(prefix)
    if not bioregistry.is_known_identifier(prefix, identifier):
        return abort(
            404,
            f"invalid identifier: {prefix}:{identifier} for pattern {bioregistry.get_pattern(prefix)}",
        )
    providers = bioregistry.get_providers(prefix, identifier)
    if not providers:
        return abort(404, f"no providers available for {prefix}:{identifier}")

    return dict(
        query=dict(prefix=prefix, identifier=identifier),
        providers=providers,
    )


def jsonify(data):
    """Dump data as JSON, like like :func:`flask.jsonify`."""
    return current_app.response_class(
        json.dumps(data, ensure_ascii=False, default=extended_encoder) + "\n",
        mimetype=current_app.config["JSONIFY_MIMETYPE"],
    )


def yamlify(data):
    """Dump data as YAML, like :func:`flask.jsonify`."""
    if isinstance(data, BaseModel):
        data = sanitize_model(data)

    return current_app.response_class(
        yaml.safe_dump(data=data),
        mimetype="text/plain",
    )


def _get_format(default: str = "json") -> str:
    return request.args.get("format", default=default)


def serialize(data, serializers: Optional[Sequence[Tuple[str, str, Callable]]] = None):
    """Serialize either as JSON or YAML."""
    fmt = _get_format()
    if fmt == "json":
        return jsonify(data)
    elif fmt in {"yaml", "yml"}:
        return yamlify(data)
    for name, mimetype, func in serializers or []:
        if fmt == name:
            return current_app.response_class(func(data), mimetype=mimetype)
    return abort(404, f"invalid format: {fmt}")
