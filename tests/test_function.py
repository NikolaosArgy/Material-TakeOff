"""Run integration tests with a speckle server."""

from pydantic import SecretStr

from speckle_automate import (
    AutomationContext,
    AutomationRunData,
    AutomationStatus,
    run_function
)

from main import FunctionInputs, automate_function

from speckle_automate.fixtures import *


def test_function_run(test_automation_run_data: AutomationRunData, test_automation_token: str):
    """Run an integration test for the automate function."""
    automation_context = AutomationContext.initialize(
        test_automation_run_data, test_automation_token
    )
    automate_sdk = run_function(
        automation_context,
        automate_function,
        FunctionInputs(
        file_name = "TestFileNikos",
        calculate_structural = False,
        categories = '',
        parameters = '',
        group_by_level= False,
        group_by_category= False,
        group_by_type= False,
        group_by_materialName = False
        ),
    )

    assert automate_sdk.run_status == AutomationStatus.SUCCEEDED
