"""The agnosticmapper is a Python package depending on rdflib 7.0.0

By providing a canonical json, it generates assertions and returns a turtle file-like string.

    uses uuids in the IRIs of instantiated classes
    uses rdfs:lables described in loaded terminology boxes to determine which classes/object-/dataproperties are instantiated

A tiny example:

    >>> from agnosticmapper import Mapper
    >>> import json
    >>> import os

    >>> mapper = Mapper()
    >>> ontos = [open(file, "r").read() for file in [f"{os.path.dirname(__file__)}/example/foaf.ttl",
                                                     f"{os.path.dirname(__file__)}/example/rdf-schema.ttl",
                                                     f"{os.path.dirname(__file__)}/example/dublin_core_terms.ttl"]]

    >>> canon_json = json.loads(open(f"{os.path.dirname(__file__)}/example/foaf_canon.json", "r").read())

    >>> context = {
            "foaf": "http://xmlns.com/foaf/0.1",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "dcterms": "http://purl.org/dc/terms/"
        }

    >>> ignoreEntityInstantiationList = ["interest"]

    >>> result = mapper.map(canon=canon_json,
                            ontos=ontos,
                            context=context,
                            entityContextTuple=entityContextTuple,
                            ignoreEntityInstantiationList=ignoreEntityInstantiationList)
    >>> print(result)

"""

from .agnosticmapper import Mapper