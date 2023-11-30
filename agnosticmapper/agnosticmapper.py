"""
Copyright 2023, Leibniz-Institut für Werkstofforientierte Technologien - IWT.
All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
__author__      = "Jannis Grundmann (Leibniz-Institut für Werkstofforientierte Technologien - IWT), Robert Heimsoth (DECOIT GmbH & Co. KG)"

import os, sys
from uuid import uuid4
import rdflib
import argparse
import json
from typing import Union


def gen_uuid() -> str:
    """Generates a new UUID with no dashes

    Returns
    ------
    str: A new UUID
    """
    return str(uuid4()).replace("-", "")

incrementalInt = 0
def get_incremental_int() -> int:
    """Gets a new unique integer within this program session

    This method uses the global variable incrementalInt for storing the last value.

    Returns
    ------
    int: Unique integer
    """
    global incrementalInt
    incrementalInt += 1
    return incrementalInt

primitive = (bool, int, float, str)
def is_primitive(element: object) -> bool:
    """Checks if element is a primitive datatype of (bool, int, float, str)

    Parameters
    ------
    element: object
        Element to check

    Returns
    ------
    bool: True if element is a primitive datatype, False otherwise
    """
    return isinstance(element, primitive)

class Mapper:
    """
    Provides methods to map canonical json to Turtle

    Possible to set the environment variable "RAISE" to "true" to force an exception if a Label is not found
    in the given ontology terminologies.
    """

    def map(self, canon: Union[list[dict], dict], ontos: list[str], context: dict, entityContextTuple: tuple, ignoreEntityInstantiationList: list[str]) -> str:
        """Maps the given canonical json to Turtle. Based on provided ontology terminologies.
        Instantiates classes by its labels with a uuid and using the given entity context as namespace

        Parameters
        ------
        canon: Union[list[dict], dict]
            Given dict or list of dicts of the canonical json to be converted to Turtle
        ontos: list[str]
            List of ontology terminologies as strings which are used to resolve the labels
        context: dict
            Dictionary of all used namespaces in the canonical json with its prefix as key and IRI as value
        entityContextTuple: tuple
            Tuple with exactly 2 elements where the first element is the prefix and the second element the IRI.
            The prefix is used for the instantiated classes.
        ignoreEntityInstantiationList: list[str]
            List of strings which are the labels that will be not resolved to the full IRIs.
            Instead keeps the associated value as it is in the given canonical json.

        Returns
        ------
        str: Converted Turtle output

        Raises
        ------
        Exception
            If the parameter entityContextTuple is not exactly a tuple with a length of 2.
            Or if the RAISE environment is set, also if a Label in the given canonical json is not found 
            in the given ontology terminologies.
        """
        self.canon = canon
        
        #Parse uploaded ontologies into a rdflib Graph
        self.g = rdflib.Graph()
        [self.g.parse(data=data) for data in ontos]
        
        self.context = context
        self.entityContextTuple = entityContextTuple
        if len(entityContextTuple) != 2:
            raise Exception("Entity Context must be a Tuple of 2 columns")
        self.context[entityContextTuple[0]] = entityContextTuple[1]
        self.__create_labelmaps()
        self.ignoreEntityInstantiationList = ignoreEntityInstantiationList
        self.__create_entity_instation_entity_list()
        self.__create_jsonld_instances()
        self.__apply_namespaces()
        self.__apply_uuids()
        return self.__serialize_graph()
    
    def __create_entity_instation_entity_list(self) -> None:
        """Creates the entity instances of the given ignoreEntityInstatiationList
        
        Returns:
            None
        """
        self.ignoreEntityInstantiationEntityList = []
        for elem in self.ignoreEntityInstantiationList:
            self.ignoreEntityInstantiationEntityList.append(self.__get_class_by_label(elem, elem))

    def __get_class_by_label(self, label: str, default: str = None) -> str:
        """Resolves a given label to a rdfs:label or skos:altlabel to its IRI based on the given language annotation.

        The first match is returned.
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

        Parameters
        ------
        label: str
            Label to resolve to the corresponding IRI
        default, optional: str
            Default value if the Label is not found in the labelmaps (defaults to None)
        
        Returns
        ------
        str: The found IRI or given default if not found

        Raises
        ------
        Exception
            If the RAISE environment is set, also if a Label is not found in the labelmaps
        """

        if isinstance(label, list):
            return default

        if label in self.altlabelmaps["en"]:
            return self.altlabelmaps["en"][label]
        if label in self.altlabelmaps["en-us"]:
            return self.altlabelmaps["en-us"][label]
        if label in self.altlabelmaps["en-gb"]:
            return self.altlabelmaps["en-gb"][label]
        if label in self.altlabelmaps["nolang"]:
            return self.altlabelmaps["nolang"][label]
        if label in self.labelmaps["en"]:
            return self.labelmaps["en"][label]
        if label in self.labelmaps["en-us"]:
            return self.labelmaps["en-us"][label]
        if label in self.labelmaps["en-gb"]:
            return self.labelmaps["en-gb"][label]
        if label in self.labelmaps["nolang"]:
            return self.labelmaps["nolang"][label]
        if label in self.altlabelmaps["de"]:
            return self.altlabelmaps["de"][label]
        if label in self.labelmaps["de"]:
            return self.labelmaps["de"][label]

        if not default:
            raise Exception(f"Error finding class for label {label}")
        else:
            return default

    def __create_labelmaps(self) -> None:
        """Create the labelmaps used to resolve Labels to IRI, grouped by the languages.

        Returns:
            None
        """
        self.labelmaps = {} #{lang: {label : uri, ...}, lang2: {label : uri, ...}, ...}
        self.altlabelmaps = {} #{lang: {label : uri, ...}, lang2: {label : uri, ...}, ...}

        # Prepare always available language label maps
        self.labelmaps["en"] = {}
        self.labelmaps["en-us"] = {}
        self.labelmaps["en-gb"] = {}
        self.labelmaps["nolang"] = {}
        self.labelmaps["de"] = {}
        self.altlabelmaps["en"] = {}
        self.altlabelmaps["en-us"] = {}
        self.altlabelmaps["en-gb"] = {}
        self.altlabelmaps["nolang"] = {}
        self.altlabelmaps["de"] = {}

        # Create maps for labels
        labels_query = f"""
                SELECT DISTINCT  ?lbl ?cls (lang(?lbl) as ?lang)
                WHERE {{
                    ?cls rdfs:label ?lbl .
                    }}
                """
        query = self.g.query(labels_query)
        for row in query:
            lbl = str(row["lbl"])
            cls = str(row["cls"])
            lang = str(row["lang"])
            if not lang:
                lang = "nolang"
            # If the lang is not used before, create a new entry for the lang for possible later use
            if lang not in self.labelmaps:
                self.labelmaps[lang] = {}
            self.labelmaps[lang][lbl] = cls

        # Create maps for skos alt-labels
        altlabelsQuery = f"""
                SELECT DISTINCT  ?lbl ?cls (lang(?lbl) as ?lang)
                WHERE {{
                    ?cls <http://www.w3.org/2004/02/skos/core#altLabel> ?lbl .
                    }}
                """
        altquery = self.g.query(altlabelsQuery)
        for row in altquery:
            lbl = str(row["lbl"])
            cls = str(row["cls"])
            lang = str(row["lang"])
            if not lang:
                lang = "nolang"
            # If the lang is not used before, create a new entry for the lang for possible later use
            if lang not in self.altlabelmaps:
                self.altlabelmaps[lang] = {}
            self.altlabelmaps[lang][lbl] = cls

    def __create_jsonld_instances(self) -> None:
        """Creates the list with the jsonld type dictionaries for each class instance of the given canonical json
        
        Returns:
            None
        """
        classMap = {}

        def __fill_class_map(iterable: Union[dict, list], isOrderedList: bool) -> None:
            """Method that handles an entry of the given canonical json.
            Method calls itself recursively and generates the jsonld dictionaries.

            This method fills the non-local classMap variable.

            Parameters
            ------
            iterable: Union[dict, list]
                Iterable of dict or list which contains the element to generate its jsonld dictionary
            isOrderedList: bool
                If True all Lists are handled as jsonld ordered List elements, if False the list elements are unordered
            
            Returns
            ------
            dict: A jsonld instance dictionary
            """
            if isinstance(iterable, dict):
                tmp = {}

                # Save the given keys which should be handled as ordered list for this iteration
                tmpListHandler = []
                if "listHandler" in iterable.keys():
                    tmpListHandler = iterable["listHandler"]

                for key, value in iterable.items():
                    # The value of hasIdentifier is always a string
                    if key == 'hasIdentifier':
                        value = str(value)

                    # Ignore listHandler key, because it is used above
                    if key == 'listHandler':
                        continue

                    cls = self.__get_class_by_label(key, "default")

                    if key[0].isupper() and isinstance(value, dict):
                        # Generate the identifier either with the given hasIdentifier value 
                        try:
                            identifier = value.get(value["hasIdentifier"], value["hasIdentifier"])
                            identifier = f"{key}_{identifier}"
                        # if not possible use the key with an incremental value to make it unique
                        except:
                            identifier = f"{key}_{get_incremental_int()}"

                        # Check if there are more keys than only hasIdentifier in the value dict
                        if not all([k == "hasIdentifier" for k in value.keys()]):
                            types = [cls]

                            # Additional types will be added with the resolved labels (object is type of multiple classes)
                            if isinstance(value, dict) and "additionalTypes" in value and isinstance(value["additionalTypes"], list):
                                for additionalType in value["additionalTypes"]:
                                    if additionalType and additionalType.strip():
                                        types.append(self.__get_class_by_label(additionalType, additionalType))

                            # Prepare JSON LD Format for that instance
                            ldCls = {"@type": types, "@id": identifier}
                            
                            # Add the identifier as a unique label for later access in a different canon
                            ldCls[self.__get_class_by_label("label", "http://www.w3.org/2000/01/rdf-schema#label")] = key
                            
                            # Call method again recursively for the value
                            subClassMap = __fill_class_map(value, False)

                            for k, v in subClassMap.items():
                                # Add all keys except the identifier
                                if not k == "hasIdentifier":
                                    ldCls[k] = v

                            # Add to the classMap
                            if identifier not in classMap.keys():
                                classMap[identifier] = ldCls
                            else:
                                # Update the entry in the classMap if there are more keys available
                                if len(ldCls) > len(classMap[identifier]):
                                    # update class_map entry if more keyvalues are present in later encounter
                                    classMap[identifier].update(ldCls)
                        
                        # Save the identifier for this iteration
                        tmp["@id"] = identifier
                    elif key[0].islower() and isinstance(value, dict):
                        # Save the identifier for this iteration as sub identifier
                        identifier = f"{key}_sub_{get_incremental_int()}"
                        tmp[key] = {"@id": identifier}
                    elif isinstance(value, list):
                        # Calling subs recursiveley
                        tmp[key] = __fill_class_map(value, key in tmpListHandler)
                    elif not key == "hasIdentifier" and not isinstance(value, dict) and not isinstance(value, list):
                        # If the value of that key should not be instantiated as own instance later
                        # e.g. for qudt units
                        if key in self.ignoreEntityInstantiationList:
                            value = {
                                "@id": self.__get_class_by_label(value, value)
                            }
                        tmp[key] = value
                return tmp
            elif isinstance(iterable, list):
                # Check if all values are primitives (dataproperties)
                if all([is_primitive(val) for val in iterable]): 
                    vals = [{"@value": val} for val in iterable]
                    return vals
                
                tmp = list(range(len(iterable)))
                for idx, elem in enumerate(iterable):
                    tmp[idx] = __fill_class_map(elem, False)

                if isOrderedList:
                    return {"@list": tmp}
                
                return tmp

        __fill_class_map(self.canon, False)
        # Convert the classMap into a list of all values in it, because the keys are not relevant for further handling
        self.classList = [v for v in classMap.values()]

    def __apply_namespaces(self) -> None:
        """Set the namespaces for the jsonld instances by resolving the Labels to its IRI's
        
        Returns:
            None
        """

        def __set_namespaces(iterable: Union[dict, list]) -> dict:
            """Method that handles an entry of the given jsonld instances.
            Method calls itself recursively and resolves the given Labels to their corresponding IRI's.

            Parameters
            ------
            iterable: Union[dict, list]
                Iterable of dict or list which contains the element to generate its IRI's

            Returns
            ------
            dict: The dictionary with the resolved namespace
            """
            if isinstance(iterable, dict):
                tmp = {}
                for key, value in iterable.items():
                    if key == "@id":
                        tmp[key] = value
                    if key == "@type":
                        tmp[key] = self.__get_class_by_label(value, value)
                    elif isinstance(value, list):
                        tmp[self.__get_class_by_label(key, key)] = __set_namespaces(value)
                    elif key == "@value":
                        return {"@value": value}
                    elif key != "@type" and key != "@id":
                        tmp[self.__get_class_by_label(key, key)] = value
                return tmp
            elif isinstance(iterable, list):
                tmp = []
                for elem in iterable:
                    tmp.append(__set_namespaces(elem))
                return tmp

        self.classList = __set_namespaces(self.classList)

    def __apply_uuids(self) -> None:
        """Applies unique IDs to all jsonld instances that are not in the given ignoreEntityInstantiationEntityList"""
        # apply pmde uuids and units
        idMap = {}
        def __set_uuid(iterable: Union[dict, list], parentKey: str) -> None:
            """Method that handles an entry of the given jsonld instances.
            Method calls itself recursively and generates a unique ID for every instance,
            except the labels that are given in ignoreEntityInstantiationEntityList.

            This method fills the non-local idMap with the jsonld instances with the generated UUIDs.

            Generated labels are in format UUID_ClassName_IterationNumber

            Parameters
            ------
            iterable: Union[dict, list]
                Iterable of dict or list which contains the element to generate their UUIDs
            parentKey: str
                The parent key of the previous iteration

            Returns:
                None
            """
            if isinstance(iterable, dict):
                for key, value in iterable.items():
                    if key == "@id" and parentKey not in self.ignoreEntityInstantiationEntityList:
                        uuid = gen_uuid()
                        if value not in idMap:
                            if value.startswith(self.entityContextTuple[0]+":"):
                                idMap[value] = value
                            else:
                                idMap[value] = f"{self.entityContextTuple[1]}{uuid}"
                        iterable[key] = idMap[value]
                        if self.__get_class_by_label("label", "http://www.w3.org/2000/01/rdf-schema#label") in iterable:
                            labelAppendix = value
                            if "http://www.w3.org/2000/01/rdf-schema#label" in iterable:
                                labelAppendix = iterable["http://www.w3.org/2000/01/rdf-schema#label"]
                            shortid = idMap[value].replace(self.entityContextTuple[1], "")[:6]
                            iterable[self.__get_class_by_label("label", "http://www.w3.org/2000/01/rdf-schema#label")] = f"{shortid} {labelAppendix}"
                    elif isinstance(value, list) or isinstance(value, dict):
                        __set_uuid(value, key)
            elif isinstance(iterable, list):
                for elem in iterable:
                    __set_uuid(elem, None)

        __set_uuid(self.classList, None)

        # apply context
        for elem in self.classList:
            elem["@context"] = self.context

    def __serialize_graph(self) -> str:
        """This method serializes the generated json-ld instances to the Turtle format
        
        Returns
        ------
        str: The serialized Turtle of the generated json-ld based on the given canonical json
        """
        gData = rdflib.Graph()

        # save as jsonlds and parse into graph
        for elem in self.classList:
            gData.parse(data=elem, format='json-ld')

        # save onto as ttl (as  as output)
        return gData.serialize(format='turtle')
    
def example():
    mapper = Mapper()
    ontos = [open(file, "r").read() for file in [f"{os.path.dirname(__file__)}/example/foaf.ttl",
                                                 f"{os.path.dirname(__file__)}/example/rdf-schema.ttl",
                                                 f"{os.path.dirname(__file__)}/example/dublin_core_terms.ttl"]] 
    canon_json = json.loads(open(f"{os.path.dirname(__file__)}/example/foaf_canon.json", "r").read())
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



if __name__=="__main__":
    mapper = Mapper()

    parser=argparse.ArgumentParser(description='Converts canonical json json to Turtle', prog='agnosticmapper')
    parser.add_argument('-o','--ontologies', action='append', dest='ontos', help="Ontology Turtle filepaths (Multiple possible)", required=True)
    parser.add_argument('-j','--jsoncanon', action='store', dest='canon_json', help='Provided canonical json filepath', required=True)
    parser.add_argument('-c','--context', action='store', dest='context', help='Json Filepath to the context json', required=True)
    parser.add_argument('-p','--entitycontextprefix', action='store', dest='entity_context_prefix', help="Entity Context Prefix (e.g. entity)", required=True)
    parser.add_argument('-e','--entitycontext', action='store', dest='entity_context', help="Entity Context (e.g. https://example.org/entity/)", required=True)
    parser.add_argument('-i','--ignoreinstantiation', action='append', dest='ignore_instantiation', help='List of Labels which are not instantiated with entity context (e.g. interest) (Multiple possible)', required=False)
    parser.add_argument('-w','--writefilepath', action='store', dest='write_path', help='Write generated Turtle to the given file instead of print it. (e.g. /tmp/test.ttl)', required=False)

    args = parser.parse_args()

    ontos = [open(file, "r").read() for file in args.ontos] 
    canon_json = json.loads(open(f"{args.canon_json}", "r").read())

    context = json.loads(open(f"{args.context}", "r").read())

    entityContextTuple = (args.entity_context_prefix, args.entity_context)

    if not args.entity_context.endswith("/") and not args.entity_context.endswith("#"):
        print("WARNING: Entity-Context URI does not end with a / or # - maybe the prefix won't be used!")
        if input('Do you want to continue? (y/n)') != 'y':
            sys.exit(0)


    ignoreEntityInstantiationList = []
    if "ignore_instantiation" in args and args.ignore_instantiation:
        ignoreEntityInstantiationList = args.ignore_instantiation

    result = mapper.map(canon=canon_json,
                ontos=ontos,
                context=context,
                entityContextTuple=entityContextTuple,
                ignoreEntityInstantiationList=ignoreEntityInstantiationList)
    
    if "write_path" in args and args.write_path:
        f = open(args.write_path, "w")
        f.write(result)
        f.close()
        print(f"Written to file {args.write_path}")
    else:
        print(result)

    sys.exit(0)

