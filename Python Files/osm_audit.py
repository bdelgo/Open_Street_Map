#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 28 14:10:47 2017

@author: behruz
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

osm_sample = "/map.osm"
osm_sanjose = "/san-jose_california.osm"


# ================================================== #
#              Getting familiarize with data         #
# ================================================== #
def count_tags(filename):
    tag_dic = {}
    for event, elem in ET.iterparse(filename, events=("start",)):
        if elem.tag not in tag_dic.keys():
            tag_dic[elem.tag] = 1
        else:
            tag_dic[elem.tag] += 1
    return tag_dic 

def get_user(element):
    tags = ["way", "node", "relation"]
    if element.tag in tags:
        return element.attrib['uid']
    else:
        return False

def process_map(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        if get_user(element):
            users.add(get_user(element))
        pass

    return users

# ================================================== #
#              Auditing Street Types                 #
# ================================================== #

expected_types = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Highway", "Commons", "Alley", "Expressway", "Way", "Circle", "Terrace"]

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

def street_type(street_name):
    """
    using Regular Expressions, it extracts the street type from the 
    street name
    """
    match = street_type_re.search(street_name)
    if match:
        return match.group()
    else:
        return None     

def audit_street(osmfile):
    """ 
    Iteratively parses through each element in an OSM file. For 'node' and 
    'way' elements, it parses through the 'tag' sub-elements with 
    'address:street' as their 'k' attribute. if the type of the street name is
    not what we expected we add this unexpected type as a new key to 
    'unexpected_types' Dictionary; each key has a Set as its value, and 
    the actual street names with corresponding unexpected type are added to 
    this Set
    """
    with open(osmfile, "r") as osm_file:
        unexpected_types = defaultdict(set)
        for event, elem in ET.iterparse(osm_file, events=("start",)):
    
            if elem.tag == "node" or elem.tag == "way":
                for tag in elem.iter("tag"):
                    if tag.attrib['k'] == "addr:street":
                        st_name = tag.attrib['v']
                        st_type = street_type(st_name)
                        if st_type not in expected_types:
                            unexpected_types[st_type].add(st_name)
    return unexpected_types

street_mapping = { "St": "Street",
            "St.": "Street",
            "street": "Street",
            "Blvd.": "Boulevard",
            "Blvd": "Boulevard",
            "Rd.": "Road",
            "Rd": "Road",
            "Ct.": "Court",
            "Ct": "Court",
            "Ave": "Avenue",
            "Ave,": "Avenue",
            "ave": "Avenue",
            "Cir" : "Circle",
            "Dr" : "Drive",
            "Ct": "Court",
            "ct": "Court",
            "court": "Court",
            "Rd": "Road",
            "Hwy": "Highway", 
            "Ln": "Lane"
            }

def update_street_type(name, mapping):
    st_type = street_type(name)
    if st_type in street_mapping:
        modified_name = street_type_re.sub(mapping[st_type], name)
    else:
        modified_name = name
        
    return modified_name


# ================================================== #
#              Auditing City Names                   #
# ================================================== #
   
    

def audit_city(osmfile):
    """ 
    Iteratively parses through each element in an OSM file. For 'node' and 
    'way' elements, it parses through the 'tag' sub-elements with 
    'address:city' as their 'k' attribute and add its value to a set
    """
    with open(osmfile, "r") as osm_file:
        city_names = set()
        for event, elem in ET.iterparse(osm_file, events=("start",)):
    
            if elem.tag == "node" or elem.tag == "way":
                for tag in elem.iter("tag"):
                    if tag.attrib['k'] == "addr:city":
                        city_name = tag.attrib['v']
                        city_names.add(city_name)

    return city_names

city_mapping={'cupertino':'Cupertino', 
'Sunnyvale, CA':'Sunnyvale',  
'campbell':'Campbell', 
'Los Gato': 'Los Gatos',
'San jose': 'San Jose',
'san Jose':'San Jose', 
'Campbelll':'Campbell', 
'SUnnyvale':'Sunnyvale', 
u'San Jos\xe9': 'San Jose',  
'san jose':'San Jose', 
'Los Gatos, CA':'Los Gatos', 
'Mt Hamilton':'Mount Hamilton', 
'Santa clara':'Santa Clara', 
'los gatos':'Los Gatos', 
'santa clara':'Santa Clara', 
'santa Clara':'Santa Clara', 
'sunnyvale':'Sunnyvale' 
}    

def update_city(name, mapping):
    if name in mapping:
        return mapping[name]
    else:
        return name    


# ================================================== #
#              Auditing Postal Codes                 #
# ================================================== #

TWO_PART_POSTCODE = re.compile(r"(.+?)-(.+)")
CA_INCLUDED = re.compile(r'CA ')
only_digit = re.compile(r'^([0-9]|-)+$')
first_3_digit = re.compile(r'^[0-9]{3}')

def is_only_digit(postcode):
    m = only_digit.match(postcode)
    if m:
        return True
    else:
        return False
    
       
def out_of_range(postcode):
    """ checks if the first 3 digits of the postal code is in the valid 
    range for San Jose area """

    valid_zipcode = ['940', '945', '950', '951']
    if first_3_digit.search(postcode).group() not in valid_zipcode:
        return True
    else:
        return False

def audit_postcodes(osmfile):
    """ 
    Iteratively parses through each element in an OSM file. For 'node' and 
    'way' elements, it parses through the 'tag' sub-elements with 
    'address:postcode as their 'k' attribute. If the postal code contains 
    anything other than digits and dash character; or if it is out of the 
    valid range, it is added to the 'problem_postcode' Set 
    """
    with open(osmfile, "r") as osm_file:
        problem_postcode = set()

        for event, elem in ET.iterparse(osm_file, events=("start",)):
    
            if elem.tag == "node" or elem.tag == "way":
                for tag in elem.iter("tag"):      
                    if tag.attrib['k'] == "addr:postcode":
                        postcode = tag.attrib['v']
                        if not is_only_digit(postcode):
                            problem_postcode.add(postcode)
                            
                        elif out_of_range(postcode): 
                            problem_postcode.add(postcode)

    return problem_postcode

def five_digit_postcode(postcode):
    m = TWO_PART_POSTCODE.match(postcode)
    if m:
        return m.group(1)
    else:
        return postcode
    
def find_postcode_addr(osmfile, postcode):
    """ 
    Iteratively parses through each element in an OSM file, until it finds
    an element with 'postcode' as its postal code; then it returns node_id, address
    and house number of that element
    """
    with open(osmfile, "r") as osm_file:
        for event, elem in ET.iterparse(osm_file, events=("start",)):

            if elem.tag == "node" or elem.tag == "way":
                element_id = elem.attrib['id']
                code = None
                address = None
                house_no = None
                
                for tag in elem.iter("tag"):      
                    if tag.attrib['k'] == "addr:postcode":
                        code = tag.attrib['v']
                    elif tag.attrib['k'] == "addr:street":
                        address = tag.attrib['v']
                    elif tag.attrib['k'] == "addr:housenumber":
                        house_no = tag.attrib['v']
                        
                if code == postcode:
                    return (element_id, house_no, address)

def update_postcode(postcode):
    """ Clears 'CA' from postal codes and modifies few other 
    problematic postal codes. Finally, if the postal code is and extended 
    one(e.g. '95014-1234'), it returns the non-extended version(e.g. '95014')
    """
    
    if CA_INCLUDED.search(postcode):
        modified_postcode = CA_INCLUDED.sub(r'', postcode)
        
    elif postcode == 'CUPERTINO':
        modified_postcode = '95014'
        
    elif postcode == '95914':
        modified_postcode = '95014'
        
    elif postcode == '95014-2143;95014-2144':
        modified_postcode = '95014'
        
    elif postcode == u'94087\u200e':
        modified_postcode = '94087'
        
    else:
        modified_postcode = five_digit_postcode(postcode)
        
    return modified_postcode