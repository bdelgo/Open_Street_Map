#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 27 12:57:44 2017

@author: behruz
"""

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import cerberus
import schema

from osm_audit import street_mapping
from osm_audit import update_street_type
from osm_audit import update_city
from osm_audit import city_mapping
from osm_audit import update_postcode



OSM_PATH = "/map.osm"

NODES_PATH = "/nodes.csv"
NODE_TAGS_PATH = "/nodes_tags.csv"
WAYS_PATH = "/ways.csv"
WAY_NODES_PATH = "/ways_nodes.csv"
WAY_TAGS_PATH = "/ways_tags.csv"


SCHEMA = schema.schema

MY_LOWER_COLON = re.compile(r"(.+?):(.+)")
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# ======================================================== #
# Transforming elements from document to tabular format    #
# ======================================================== #

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """
    The function should take as input an iterparse Element object and return a 
    dictionary. If the element top level tag is "node" the dictionary returned 
    should have the format {"node": .., "node_tags": ...}
    If the element top level tag is "way" the dictionary should have the format
    {"way": ..., "way_tags": ..., "way_nodes": ...}
    """

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  
           
    if element.tag == 'node':
        for field in node_attr_fields:
            if field == 'id':
                node_attribs[field] = int(element.attrib[field])
            if field == 'lat':
                node_attribs[field] = float(element.attrib[field])
            if field == 'lon':
                node_attribs[field] = float(element.attrib[field])
            if field == 'uid':
                node_attribs[field] = int(element.attrib[field])
            if field == 'version':
                node_attribs[field] = int(element.attrib[field])
            if field == 'changeset':
                node_attribs[field] = int(element.attrib[field])
            else:                
                node_attribs[field] = element.attrib[field]                
             
        for child in element:
            if (child.tag =='tag') and not(PROBLEMCHARS.search(child.attrib['k'])):
                tag_attribs = {} 
                tag_attribs['id'] = node_attribs['id']
                tag_attribs['type'] = 'regular'
                tag_attribs['key'] = child.attrib['k']
                
                #here I update the address values
                if tag_attribs['key'] == 'addr:postcode':
                    tag_attribs['value'] = update_postcode(child.attrib['v'])
                    
                elif tag_attribs['key'] == 'addr:city':
                    tag_attribs['value'] = update_city(child.attrib['v'], city_mapping)
                    
                elif tag_attribs['key'] == 'addr:street':
                    tag_attribs['value'] = update_street_type(child.attrib['v'], street_mapping)
                    
                else:
                    tag_attribs['value'] = child.attrib['v']
                    
                key_colon = MY_LOWER_COLON.search(child.attrib['k'])
                
                if key_colon:
                    tag_attribs['type'] = key_colon.group(1)
                    tag_attribs['key'] = key_colon.group(2)
                tags.append(tag_attribs)
                
        return {'node': node_attribs, 'node_tags': tags}    
    
    elif element.tag == 'way':
        for field in way_attr_fields:
            if field == 'id':
                way_attribs[field] = int(element.attrib[field])
            if field == 'uid':
                way_attribs[field] = int(element.attrib[field])
            if field == 'changeset':
                way_attribs[field] = int(element.attrib[field])
            else:                
                way_attribs[field] = element.attrib[field]
        
        nd_order = 0 
        
        for child in element:
            if (child.tag =='tag') and not(PROBLEMCHARS.search(child.attrib['k'])):
                tag_attribs = {} 
                tag_attribs['id'] = way_attribs['id']
                tag_attribs['type'] = 'regular'
                tag_attribs['key'] = child.attrib['k']
                
                #here I update the address values
                if tag_attribs['key'] == 'addr:postcode':
                    tag_attribs['value'] = update_postcode(child.attrib['v'])
                    
                elif tag_attribs['key'] == 'addr:city':
                    tag_attribs['value'] = update_city(child.attrib['v'], city_mapping)
                    
                elif tag_attribs['key'] == 'addr:street':
                    tag_attribs['value'] = update_street_type(child.attrib['v'], street_mapping)
                    
                else:
                    tag_attribs['value'] = child.attrib['v']
                    
                key_colon = MY_LOWER_COLON.search(child.attrib['k'])
                
                if key_colon:
                    tag_attribs['type'] = key_colon.group(1)
                    tag_attribs['key'] = key_colon.group(2)
                    
                tags.append(tag_attribs)
                
            elif child.tag =='nd':
                WAY_NODES_FIELDS = ['id', 'node_id', 'position']
                nd_attribs ={}
                nd_attribs['id'] = way_attribs['id']
                nd_attribs['node_id'] = int(child.attrib['ref'])
                nd_attribs['position'] = nd_order
                nd_order +=1
                way_nodes.append(nd_attribs)
                          
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)
        
        """
        I exclude the following part, because it caused type mismatch error when i 
        tried to import csv files into the database. Since I will specify the
        field names when I create tables in Sqlite3, there is no need for
        writing them into the csv file
        """
        """
        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()
        """

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate= False)
