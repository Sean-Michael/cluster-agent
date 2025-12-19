from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from dataclasses import dataclass
from typing import Optional
import subprocess


@dataclass
class CommandResult:
    """Structured result from command execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    error_message: str | None = None


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


class KubectlDescribeInput(BaseModel):
    """Input model for kubectl describe operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid'
    )

    resource_type: str = Field(
        ...,
        description="Kubernetes resource type",
        min_length=1
    )
    name: Optional[str] = Field(
        default=None,
        description="Name or name prefix of the resource. If omitted, describes all resources of the given type."
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Namespace to query. Leave blank for cluster-scoped resources or default namespace."
    )
    selector: Optional[str] = Field(
        default=None,
        description="Label selector to filter resources"
    )


def run_command_helper(command: list[str], timeout_seconds: int = 30) -> CommandResult:
    """
    Execute a kubectl command safely.

    Args:
        command: Command as a list of strings (never a shell string)
        timeout_seconds: Max execution time before killing the process

    Returns:
        CommandResult with success status, output, and any errors
    """
    if isinstance(command, str):
        return CommandResult(
            success=False,
            stdout="",
            stderr="",
            return_code=-1,
            error_message="Security error: command must be a list, not a string"
        )

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False
        )

        return CommandResult(
            success=(result.returncode == 0),
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
            error_message=result.stderr if result.returncode != 0 else None
        )

    except subprocess.TimeoutExpired:
        return CommandResult(
            success=False,
            stdout="",
            stderr="",
            return_code=-1,
            error_message=f"Command timed out after {timeout_seconds} seconds"
        )
    except FileNotFoundError:
        return CommandResult(
            success=False,
            stdout="",
            stderr="",
            return_code=-1,
            error_message="kubectl not found."
        )
    except Exception as e:
        return CommandResult(
            success=False,
            stdout="",
            stderr="",
            return_code=-1,
            error_message=f"Unexpected error: {type(e).__name__}: {str(e)}"
        )

mcp = FastMCP(
    name="HelpfulAssistant",
    instructions="""
        This server provides kubernetes cluster administration tools.
    """,
)


@mcp.tool(
    name="kubectl_get_api_resources",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False
    }
)
async def get_all_api_resources() -> str:
    """Get all available Kubernetes API resources.

    Returns:
        JSON listing all API resources the cluster supports, or an error message.
    """
    command = ["kubectl", "api-resources", "-o", "json"]
    result = run_command_helper(command)

    if not result.success:
        return f"Error: {result.error_message}"

    return result.stdout


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

    if not result.success:
        return f"Error: {result.error_message}"

    return result.stdout


@mcp.tool(
    name="kubectl_describe_resource",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False
    }
)
async def kubectl_describe_resource(params: KubectlDescribeInput) -> str:
    """Show detailed information about a specific resource or group of resources.

    Returns a detailed description including related resources like events and controllers.
    You can select by exact name, name prefix, or label selector.

    Args:
        params: Validated input containing resource type, optional name/prefix,
            namespace, and label selector for filtering.

    Returns:
        Detailed resource description, or an error message.
    """
    command = ["kubectl", "describe", params.resource_type]

    if params.name:
        command.append(params.name)
    if params.namespace:
        command.extend(["-n", params.namespace])
    if params.selector:
        command.extend(["--selector", params.selector])

    result = run_command_helper(command)

    if not result.success:
        return f"Error: {result.error_message}"

    return result.stdout


if __name__ == "__main__":
    mcp.run()