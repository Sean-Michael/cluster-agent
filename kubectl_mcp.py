from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from dataclasses import dataclass
from typing import Optional, List, Union
import subprocess
import json


@dataclass
class CommandResult:
    """Structured result from command execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    error_message: str | None = None


def run_command_helper(command: list[str], timeout_seconds: int = 30) -> CommandResult:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True)
        return result
    except Exception as e:
        return e


class KubectlGetInput(BaseModel):
    """Input model for kubectl get operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid'
    )

    resource: str = Field(
        ...,
        description="Kuberenetes resource type",
        min_length=1
    )
    namespace: Optional[str] = Field(
        default=None,
        description="namespace to query. Leave blank for cluster-scoped or default namespace"
    )
    selector: Optional[str] = Field(
        default=None,
        description="You can filter the list using a label selector and the --selector flag"
    ) 
    output_format: Optional[str] = Field(
        default=None,
        description="Output format: 'json', 'yaml', 'wide', or 'name'"
    )


mcp = FastMCP(
    name="HelpfulAssistant",
    instructions="""
        This server provides kubernetes cluster administration tools.
    """,
)



@mcp.tool()
async def get_all_api_resources():
    """Get a JSON of all the Kubernetes API Resources"""
    command = "kubectl api-resources -o json"
    result = run_command_helper(command)
    return json.loads(result.stdout)


@mcp.tool(    
    name="kubectl_get_resource",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False
    }
)
async def kubectl_get_resource(params: KubectlGetInput) -> str:
    """Display one or many Kubernetes resources.
    
    Args:
        params: Validated input containing resource type, namespace
            (Optional) label selectors for filtering and output format
        
    Returns:
        Resource data in the requested format, or an error message.
    """
    command = ["kubectl", "get", params.resource]
    if params.namespace:
        command.extend(["-n", params.namespace])
    if params.output_format:
        command.extend(["-o", params.output_format])
    if params.selector:
        command.extend(["--selector", params.selector])
    
    result = run_command_helper(command)
    return result.stdout