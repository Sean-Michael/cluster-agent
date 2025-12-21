# Cluster Agent

Uses custom MCP servers and agentic workflow to provide assistance administering Kubernetes clusters.

## MCP Servers

kubectl_mcp.py - work in prog

Example output:

```bash
% python client.py          
INFO:__main__:Connected to MCP server: kubectl_mcp.py
Processing request of type ListToolsRequest
INFO:__main__:Found 3 tools
INFO:__main__:Formatted: kubectl_get_api_resources into OpenAI/Ollama compatible format
INFO:__main__:Formatted: kubectl_get_resource into OpenAI/Ollama compatible format
INFO:__main__:Formatted: kubectl_describe_resource into OpenAI/Ollama compatible format
INFO:__main__:Formatted 3 tools.
INFO:httpx:HTTP Request: POST http://127.0.0.1:11434/api/chat "HTTP/1.1 200 OK"
INFO:__main__:Calling tool: kubectl_get_resource with args: {'params': {'namespace': None, 'resource': 'nodes'}}
Processing request of type CallToolRequest
Tool kubectl_get_resource result:
NAME                             STATUS   ROLES    AGE   VERSION
aks-system-vmss000000   Ready    <none>   15d   v1.32.9
aks-user-vmss000000     Ready    <none>   14d   v1.32.9
aks-user-vmss000001     Ready    <none>   14d   v1.32.9
aks-user-vmss000002     Ready    <none>   14d   v1.32.9

INFO:__main__:MCP client connection closed
```

#### References

- https://modelcontextprotocol.io/docs/develop/build-client

