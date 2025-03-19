"""Helper functions."""

from collections.abc import Iterable

from specklepy.objects import Base

def flatten_base(base: Base) -> Iterable[Base]:
    """Flatten a base object into an iterable of bases.
    
    This function recursively traverses the `elements` or `@elements` attribute of the 
    base object, yielding each nested base object.

    Args:
        base (Base): The base object to flatten.

    Yields:
        Base: Each nested base object in the hierarchy.
    """
    # Attempt to get the elements attribute, fallback to @elements if necessary
    elements = getattr(base, "elements", getattr(base, "@elements", None))
    
    if elements is not None:
        for element in elements:
            yield from flatten_base(element)
    
    yield base

def filter_objects_by_category(all_objects, filter_categories):
    """
    Filters objects by category and returns a list of matching objects and their IDs.

    Parameters:
    all_objects (list): List of objects to filter.
    filter_categories (list): List of categories to filter by.

    Returns:
    list: filtered_objects
    """
    filtered_objects = []

    for i in all_objects:
        if hasattr(i, "category"):  # Check if the object has the "category" attribute
            if i.category in filter_categories:  # Check if the category matches the filter list
                filtered_objects.append(i)  # Append the whole object to the items list
        else:
            continue  # Skip if "category" does not exist

    return filtered_objects

def get_nested_attr(obj, attr_path, default=None):
    """
    Safely get a nested attribute or dictionary key using a dot-separated path.
    """
    try:
        parts = attr_path.split('.')
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part, default)
            else:
                obj = getattr(obj, part, default)
            if obj is None:
                return default

        return obj
    except AttributeError:
        return default

def extract_material_data(all_objects, other_params, include_structural=False):
    """
    Extracts material data from a list of objects, including additional parameters and level name.

    Parameters:
    all_objects (list): List of objects to extract data from.
    other_params (list): List of additional parameters to include.
    include_structural (bool): Whether to include structural quantities in the output.

    Returns:
    list: A list of dictionaries containing extracted material data.
    """
    materials_data = []

    for item in all_objects:
        properties = getattr(item, 'properties', {})  # Get 'properties' safely
        material_quantities = properties.get('Material Quantities', {})
        
        # Only calculate structural quantities if include_structural is True
        structural_quantities = {}
        if include_structural:
            # Correct path to structural data based on your JSON - with None checks
            parameters = properties.get('Parameters', {})
            # Add null check - if parameters is None, use empty dict
            type_parameters = parameters.get('Type Parameters', {}) if parameters is not None else {}
            # Add null check - if type_parameters is None, use empty dict
            structural_quantities = type_parameters.get('Structure', {}) if type_parameters is not None else {}

        item_level_name = getattr(item, 'level', None)
        item_family = getattr(item, 'family', None)
        item_category = getattr(item, 'category', None)
        item_type = getattr(item, 'type', None)

        # Process each material quantity
        for index, (material, attributes) in enumerate(material_quantities.items()):
            row = {
                'Material': material, 
                'Level Name': item_level_name,
                'Category': item_category,
                'Family': item_family,
                'Type': item_type
            }

            for param in other_params:
                row[param.capitalize()] = get_nested_attr(item, param)

            # Extract material properties
            for key, value in attributes.items():
                if isinstance(value, dict) and 'value' in value:
                    row[key.capitalize() + " ( " + value.get("units", "") + " )"] = round(value['value'], 4)
                else:
                    row[key] = value
            
            # Extract structural quantities only if include_structural is True
            if include_structural and structural_quantities:
                struct_items = list(structural_quantities.items())
                # If we have a matching structural item (by index), add it
                if index < len(struct_items):
                    struct_key, struct_value = struct_items[index]
                    # Process each property in the structural item
                    if isinstance(struct_value, dict):
                        for sub_key, sub_value in struct_value.items():
                            row[f"Structural {sub_key.capitalize()}"] = sub_value
                
            materials_data.append(row)
    
    return materials_data