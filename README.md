# agnosticmapper

The agnosticmapper is a Python package depending on rdflib .

By parsing a [canonical JSON](#Canonical-JSON-example), it generates assertions (abox) and returns a turtle file-like string, that

- uses rdfs:lables described in provided terminology boxes to determine which classes/object-/dataproperties are instantiated
- creates class instances with uuids in the IRIs 
- cross-references instances within the abox


## Getting Started

### Installation of the module

To install the module locally for usage in another python script, after cloning the repository, navigate to the module path and build a wheel file.

```
$ cd path/to/agnosticmapper/
```

The structure of the directory should look like this:
```
$ ls .
....
agnosticmapper
setup.py
pyproject.toml
...
```

Build the wheel file:
```
python3 setup.py bdist_wheel
```

Check for the creation of the wheel file in the `dist` directory
```
$ ls ./dist
agnosticmapper-1.0-py3-none-any.whl
```

Navigate to the top path to install the python module
```
$ cd ../
$ ls
...
agnosticmapper
...
$ pip install agnosticmapper/dist/agnosticmapper-1.0-py3-none-any.whl
...
Successfully installed agnosticmapper-1.0
```

If necessary you can uninstall again the module with
```
pip uninstall agnosticmapper
```

### Usage
If the module is installed you can use the python `import` to use the module in your code.
```
from agnosticmapper import Mapper
```

You can then create a new Mapper instance
```
mapper = Mapper()
```

The mapper only provides one method, called `map(...)`.
The method creates the Turtle file out of the given canonical json. Based on provided ontology terminologies. It instantiates classes by its labels with a uuid and using the given entity context as the namespace.

```
mapper.map(canon, ontos, context, entityContextTuple, ignoreEntityInstantiationList)
```

#### Parameter description


| Parameter | Type | Description |
| -------- | -------- | -------- |
| canon    | list[dict]\|dict | Given dict or list of dicts of the canonical json to be converted to Turtle |
| ontos | list[str] | List of ontology terminologies as strings which are used to resolve the labels |
| context | dict | Dictionary of all used namespaces in the canonical json with its prefix as key and IRI as value |
| entityContextTuple | tuple | Tuple with exactly 2 elements where the first element is the prefix and the second element the IRI. The prefix is used for the instantiated classes. |
| ignoreEntityInstantiationList | list[str] | List of strings which are the labels that will not be instatiated. Instead it keeps the associated value as it is in the given canonical json. |

#### Example usage
```
from agnosticmapper import Mapper
import json
import os

mapper = Mapper()
ontos = [open(file, "r").read() for file in [f"/path/to/agnosticmapper/example/foaf.ttl",
                                             f"/path/to/agnosticmapper/example/rdf-schema.ttl",
                                             f"/path/to/agnosticmapper/example/dublin_core_terms.ttl"]]
                                             
canon_json = json.loads(open(f"/path/to/agnosticmapper/example/foaf_canon.json", "r").read())

context = {
    "foaf": "http://xmlns.com/foaf/0.1",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "dcterms": "http://purl.org/dc/terms/"
}
    
entityContextTuple = ("entity", "http://example.org/entity/")
    
ignoreEntityInstantiationList = ["interest"]

result = mapper.map(canon=canon_json,
                    ontos=ontos,
                    context=context,
                    entityContextTuple=entityContextTuple,
                    ignoreEntityInstantiationList=ignoreEntityInstantiationList)
    
print(result)
```


### Canonical JSON example
Essentially a canonical json (shorthand: canon json) is an ontology independent linked data json file similar to json-ld. 

```
[{
  "Group": {
    "listHandler": ["member"],
    "member": [{
      "Person": {
        "hasIdentifier": "a"
      }
    }, {
      "Person": {
        "hasIdentifier": "b"
      }
    }]
  }
}, {
  "Person": {
    "hasIdentifier": "a",
    "additionalTypes": ["Agent"],
    "name": "Alice",
    "interest": "http://purl.org/dc/terms/BibliographicResource"
  }
}, {
  "Person": {
    "hasIdentifier": "b",
    "name": "Bob",
    "knows": [{
      "Person": {
        "name": "Charlie"
      }
    }, {
      "Person": {
        "name": "Dave"
      }
    }]
  }
}]
```

The json-keys are strings that match with rdfs:labels in the provided terminology-boxes. 

Special keys that must not be used as a rdfs:label are "hasIdentifier", "additionalTypes" and "listHandler".

JSON values can be primitive datatypes, in which case the provided value is directly written as a value in the assertion box.
If the json values are json objects themselves, it indicates that a new class instance will be created except the label is part of the parameter "ignoreEntityInstantiationList" in which case the provided value will kept in the abox as is. (see the objectproperty "interest" in the example)

For each element in an json array a new class instance will be created and added to the domain of the object.
If the label is marked in "listHandler", the array will be handled as a ordered list (see "member" in the example). There can be multiple labels dedicated as a list. It only is valid within the same json object.

"hasIdentifier" is used to cross reference class instances within the canon json. If you reference a class instance at another point, you must use it or else it will create two different class instances with different uuids.

"additoinalTypes" will add more subclasses to the class instance apart from the label that is used as the key.

The prefix and namespace that is prefixed to the uuids of the class instance IRIs ist provided via the "entityContextTuple" parameter.

### Output example
```
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix entity: <http://example.org/entity/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

entity:ef4cc7abeebf4ca2b0db3e9625bfaba9 a foaf:Group ;
    rdfs:label "ef4cc7 Group" ;
    rdfs:member ( entity:e78d4393bc3d4decb38e2c335294b480 entity:b2c30466cbf34bc18429d3aa9e3d7a8b ) .

entity:e78d4393bc3d4decb38e2c335294b480 a dcterms:Agent,
        foaf:Person ;
    rdfs:label "e78d43 Person" ;
    foaf:interest dcterms:BibliographicResource ;
    foaf:name "Alice" .
    
entity:b2c30466cbf34bc18429d3aa9e3d7a8b a foaf:Person ;
    rdfs:label "b2c304 Person" ;
    foaf:knows entity:c466dac731024d0a88d493ceaab70ea1,
        entity:e054f53709a84c27aade3b2c097375e5 ;
    foaf:name "Bob" .

entity:e054f53709a84c27aade3b2c097375e5 a foaf:Person ;
    rdfs:label "e054f5 Person" ;
    foaf:name "Charlie" .

entity:c466dac731024d0a88d493ceaab70ea1 a foaf:Person ;
    rdfs:label "c466da Person" ;
    foaf:name "Dave" .
```

The order of searching for the label is:
1. skos:altlabel
    a. en
    b. en-us
    c. en-gb
    d. nolang
2. rdfs:label
    a. en
    b. en-us
    c. en-gb
    d. nolang
3. skos:altlabel
    a. de
4. rdfs:label
    b. de



### Standalone program

This python module can also be used as a standalone running program using command line arguments and files to work with without the need of using it as a module in another python program.

#### Parameters

#### Using python call with parameters

| Parameter | Description | Multiple Possible | Required |
| -------- | -------- | -------- | -------- |
| -h, --help | show help message and exit | No | Yes |
| -o ONTOS, --ontologies ONTOS | ONTOS is the path to the ontology turtle file | Yes | Yes |
| -j, --jsoncanon | CANON_JSON is the path to the canonical json file | No | Yes |
| -c, --context | CONTEXT is the path to the context json file | No | Yes |
| -p, --entitycontextprefix | Prefix which is used for the generated entities | No | Yes |
| -e, --entitycontext | URI which is used for the generated entities | No | Yes |
| -i, --ignoreinstantiation | Label which are not instantiated as entities | Yes | No |
| -w, --writefilepath | Filepath to write the generated turtle instead of print it on console | No | No |

#### Example call
`python3 path/to/agnosticmapper/agnosticmapper.py -o agnosticmapper/agnosticmapper/example/foaf.ttl -o agnosticmapper/agnosticmapper/example/rdf-schema.ttl -o agnosticmapper/agnosticmapper/example/dublin_core_terms.ttl -j agnosticmapper/agnosticmapper/example/foaf_canon.json -c agnosticmapper/agnosticmapper/example/context.json -p entity -e "https://example.org/entity/" -i interest -w /tmp/myabox.ttl`

#### Building standalone program with it's requirements using pyinstaller

It is also possible to build a standalone program where all requirements are included and can be exeucted on the command line directly.

Install requirement
`pip install pyinstaller`

Go to the directory of the agnosticmapper module and execute the pyinstaller

```
$ cd path/to/agnosticmapper/agnosticmapper
```

The structure of the directory should look like this:
```
$ ls .
....
agnosticmapper.py
__init__.py
...
```

Build the standalone program file:
```
python3 -m PyInstaller agnosticmapper.py
```

You find the executable now in the `dist` directory.

The usage and parameters are the same as the call above when you call the python program directly.
