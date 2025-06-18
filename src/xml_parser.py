# src/xml_parser.py
from lxml import etree
import os

def extract_roles_from_xml(xml_filepath: str, role_xpath: str) -> list:
    """Extracts role names from an XML file using XPath."""
    if not os.path.exists(xml_filepath):
        print(f"Error: XML file not found at {xml_filepath}")
        return []
    try:
        # Use a parser that can handle byte strings if file encoding is complex
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        tree = etree.parse(xml_filepath, parser=parser)
        roles = [str(element).strip() for element in tree.xpath(role_xpath) if element is not None]
        return roles
    except etree.XMLSyntaxError as e:
        print(f"Error parsing XML file {xml_filepath}: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while parsing XML: {e}")
        return []