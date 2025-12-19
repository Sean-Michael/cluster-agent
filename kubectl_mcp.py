from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import subprocess
import json

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

def run_command_helper(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True)
        return result
    except Exception as e:
        return e


@mcp.tool(
    name="kubectl_get_resource",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False
    }
)
async def get_all_api_resources():
    """Get a JSON of all the Kubernetes API Resources"""
    command = "kubectl api-resources -o json"
    result = run_command_helper(command)
    return json.loads(result.stdout)


@mcp.tool()
async def kubectl_get_resource(resource : str, namespace : str, flags) -> str:
    """Display one or many resources."""
    command = ["kubectl", "get", resource, "-n", namespace, flags]
    result = run_command_helper(command)
    return result