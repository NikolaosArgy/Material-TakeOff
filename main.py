"""This module contains the function's business logic.

Use the automation_context module to wrap your function in an Automate context helper.
"""

from pydantic import Field, SecretStr
from speckle_automate import (
    AutomateBase,
    AutomationContext,
    execute_automate_function,
)

import pandas as pd
from datetime import datetime

from utils import flatten_base, filter_objects_by_category, extract_material_data


class FunctionInputs(AutomateBase):
    """These are function author-defined values.

    Automate will make sure to supply them matching the types specified here.
    Please use the pydantic model schema to define your inputs:
    https://docs.pydantic.dev/latest/usage/models/
    """

    file_name: str = Field(
        title="File Name",
        description="The name of the Excel file.",
    )

    calculate_structural: bool = Field(
        default=False,
        title="Type Structural Parameters (Optional)",
        description="If enabled, it extracts Type Structural Parameters together with Material Quantities.",
    )

    categories: str = Field(
        title="Revit Categories (Optional)",
        description="A list of revit categories to use, if empty then calculate all elements.",
        default = ""
    )

    parameters: str = Field(
        title="Parameters (Optional)",
        description="A list of revit parameters to extract together with Material Quantities, Level, Category, Family and Type.",
        default = ""
    )

    group_by_level: bool = Field(
        default=False,
        title="Group by Level",
        description="If enabled, it groups the quantities by Level",
    )

    group_by_category: bool = Field(
        default=False,
        title="Group by Category",
        description="If enabled, it groups the quantities by Category",
    )

    group_by_type: bool = Field(
        default=False,
        title="Group by Type",
        description="If enabled, it groups the quantities by Type",
    )

    group_by_materialName: bool = Field(
        default=False,
        title="Group by materialName",
        description="If enabled, it groups the quantities by Material Name",
    )



def automate_function(
    automate_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """This is an example Speckle Automate function.

    Args:
        automate_context: A context-helper object that carries relevant information
            about the runtime context of this function.
            It gives access to the Speckle project data that triggered this run.
            It also has convenient methods for attaching result data to the Speckle model.
        function_inputs: An instance object matching the defined schema.
    """
    # The context provides a convenient way to receive the triggering version.
    version_root_object = automate_context.receive_version()

    all_objects = list(flatten_base(version_root_object))

    file_name = function_inputs.file_name

    filter_categories = [categ.strip() for categ in function_inputs.categories.split(",")]
    list_prop = [prop.strip() for prop in function_inputs.parameters.split(",")]
    
    group_by_level = function_inputs.group_by_level
    group_by_category = function_inputs.group_by_category
    group_by_type = function_inputs.group_by_type
    group_by_materialName = function_inputs.group_by_materialName

    include_structural = function_inputs.calculate_structural

    # Define mapping of booleans to column names
    group_columns = []

    if group_by_level:
        group_columns.append("Level Name")
    if group_by_category:
        group_columns.append("Category")
    if group_by_type:
        group_columns.append("Type")
    if group_by_materialName:
        group_columns.append("materialName")

    # Apply filtering if categories are specified
    if function_inputs.categories:
        filtered_items = filter_objects_by_category(all_objects, filter_categories)
    else:
        filtered_items = all_objects
        
    try:
        # Extract material data from the appropriate object set
        material_dataset = extract_material_data(filtered_items, list_prop, include_structural)
    except Exception as e:
        automate_context.mark_run_failed(f"Something went wrong when extrecting material data. Exception detail: {e}") 

    # Convert to DataFrame
    df = pd.DataFrame(material_dataset)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    xlsx_filename = f"{file_name}_{timestamp}.xlsx"

    # Ensure there's at least one grouping column
    if not group_columns:
        try:
            #df.to_csv(csv_filename, index=False)
            with pd.ExcelWriter(xlsx_filename, engine="xlsxwriter") as writer: df.to_excel(writer, sheet_name="Sheet1", index=False)

            # Pass CSV file to function
            automate_context.store_file_result(f"./{xlsx_filename}")
        except Exception as e:
            automate_context.mark_run_failed(f"Something went wrong when writing to excel all elements (no grouping). Exception detail: {e}") 
    else:
        try:
            # Group by 'materialName'
            df_grouped = df.groupby(group_columns).agg(
                # For numeric columns: sum them
                # For non-numeric columns: join unique values
                lambda x: x.sum() if pd.api.types.is_numeric_dtype(x) else ', '.join(set(x.astype(str)))
            )

            # Add a new column 'Quantity' that counts the number of rows in each group
            df_grouped["Quantity"] = df.groupby(group_columns).size()

            # Move 'Quantity' to the front
            df_grouped = df_grouped.reset_index()
            cols = ["Quantity"] + [col for col in df_grouped.columns if col != "Quantity"]
            df_grouped = df_grouped[cols]

            #df.to_csv(csv_filename, index=False)
            with pd.ExcelWriter(xlsx_filename, engine="xlsxwriter") as writer: df_grouped.to_excel(writer, sheet_name="Sheet1", index=False)
        except Exception as e:
            automate_context.mark_run_failed(f"Something went wrong when grouping. Exception detail: {e}") 


        # Pass CSV file to function
        automate_context.store_file_result(f"./{xlsx_filename}")


# make sure to call the function with the executor
if __name__ == "__main__":
    # NOTE: always pass in the automate function by its reference; do not invoke it!

    # Pass in the function reference with the inputs schema to the executor.
    execute_automate_function(automate_function, FunctionInputs)

    # If the function has no arguments, the executor can handle it like so
    # execute_automate_function(automate_function_without_inputs)
