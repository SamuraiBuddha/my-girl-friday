#!/usr/bin/env python3
"""
My Girl Friday MCP Server
Handles Microsoft Outlook integration via Microsoft Graph API
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import asyncio

import msal
import httpx
from mcp import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server

logger = logging.getLogger(__name__)

class MyGirlFridayServer:
    """MCP Server for Microsoft Outlook integration"""
    
    def __init__(self):
        self.server = Server("my-girl-friday")
        self.client_id = os.getenv('OUTLOOK_CLIENT_ID')
        self.client_secret = os.getenv('OUTLOOK_CLIENT_SECRET')
        self.tenant_id = os.getenv('OUTLOOK_TENANT_ID', 'common')
        self.redirect_uri = os.getenv('OUTLOOK_REDIRECT_URI', 'http://localhost:8080')
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = [
            "https://graph.microsoft.com/Mail.Read",
            "https://graph.microsoft.com/Mail.ReadWrite",
            "https://graph.microsoft.com/Mail.Send",
            "https://graph.microsoft.com/Calendar.Read",
            "https://graph.microsoft.com/Calendar.ReadWrite",
            "https://graph.microsoft.com/Tasks.Read",
            "https://graph.microsoft.com/Tasks.ReadWrite",
            "https://graph.microsoft.com/User.Read"
        ]
        
        self.token_cache_file = os.getenv('TOKEN_CACHE_FILE', 'token_cache.json')
        self.token_cache = msal.SerializableTokenCache()
        self._load_cache()
        
        self.app = None
        self.access_token = None
        self._setup_handlers()
    
    def _load_cache(self):
        """Load token cache from file if it exists"""
        if os.path.exists(self.token_cache_file):
            try:
                with open(self.token_cache_file, 'r') as f:
                    self.token_cache.deserialize(f.read())
                logger.info("Token cache loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load token cache: {e}")
    
    def _save_cache(self):
        """Save token cache to file"""
        try:
            with open(self.token_cache_file, 'w') as f:
                f.write(self.token_cache.serialize())
            logger.debug("Token cache saved")
        except Exception as e:
            logger.error(f"Failed to save token cache: {e}")
    
    def _get_msal_app(self):
        """Get or create MSAL application instance"""
        if not self.app:
            self.app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret,
                token_cache=self.token_cache
            )
        return self.app
    
    async def _get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary"""
        app = self._get_msal_app()
        
        # First, try to get token from cache
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(self.scope, account=accounts[0])
            if result and "access_token" in result:
                self._save_cache()
                return result["access_token"]
        
        # If no cached token, we need to authenticate
        # For MCP, we'll use device code flow since we can't open browsers
        flow = app.initiate_device_flow(scopes=self.scope)
        
        if "user_code" not in flow:
            logger.error("Failed to create device flow")
            return None
        
        # Return the device code info for the user
        logger.info(f"To authenticate, please visit: {flow['verification_uri']}")
        logger.info(f"And enter the code: {flow['user_code']}")
        
        # Wait for user to authenticate
        result = app.acquire_token_by_device_flow(flow)
        
        if "access_token" in result:
            self._save_cache()
            return result["access_token"]
        else:
            logger.error(f"Authentication failed: {result.get('error_description', 'Unknown error')}")
            return None
    
    async def _make_graph_request(
        self, 
        endpoint: str, 
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated request to Microsoft Graph API"""
        token = await self._get_access_token()
        if not token:
            return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                
                response.raise_for_status()
                return response.json() if response.text else None
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Graph API error: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return None
    
    def _setup_handlers(self):
        """Set up MCP server handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available Outlook tools"""
            return [
                Tool(
                    name="list_emails",
                    description="List emails from Outlook inbox or specified folder",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "folder": {
                                "type": "string",
                                "description": "Folder name (default: Inbox)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of emails to return (default: 10)",
                                "minimum": 1,
                                "maximum": 50
                            },
                            "filter": {
                                "type": "string",
                                "description": "OData filter query (e.g., 'isRead eq false')"
                            },
                            "search": {
                                "type": "string",
                                "description": "Search query to find specific emails"
                            }
                        }
                    }
                ),
                Tool(
                    name="read_email",
                    description="Read a specific email by ID",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "email_id": {
                                "type": "string",
                                "description": "The ID of the email to read"
                            }
                        },
                        "required": ["email_id"]
                    }
                ),
                Tool(
                    name="get_folders",
                    description="List all email folders",
                    input_schema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            
            if name == "list_emails":
                folder = arguments.get("folder", "Inbox")
                limit = arguments.get("limit", 10)
                filter_query = arguments.get("filter")
                search_query = arguments.get("search")
                
                # Build the endpoint
                endpoint = "/me/mailFolders/Inbox/messages" if folder == "Inbox" else f"/me/mailFolders('{folder}')/messages"
                
                # Build query parameters
                params = [f"$top={limit}"]
                if filter_query:
                    params.append(f"$filter={filter_query}")
                if search_query:
                    params.append(f"$search=\"{search_query}\"")
                
                query = "?" + "&".join(params) if params else ""
                
                result = await self._make_graph_request(endpoint + query)
                
                if not result:
                    return [TextContent(
                        type="text",
                        text="Failed to retrieve emails. Please check authentication."
                    )]
                
                emails = result.get("value", [])
                
                if not emails:
                    return [TextContent(
                        type="text",
                        text="No emails found matching your criteria."
                    )]
                
                # Format email list
                email_list = []
                for email in emails:
                    sender = email.get("sender", {}).get("emailAddress", {})
                    received = email.get("receivedDateTime", "Unknown")
                    
                    # Parse and format date
                    try:
                        dt = datetime.fromisoformat(received.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%b %d, %I:%M %p")
                    except:
                        formatted_date = received
                    
                    email_info = (
                        f"**Subject:** {email.get('subject', 'No Subject')}\n"
                        f"**From:** {sender.get('name', 'Unknown')} <{sender.get('address', 'Unknown')}>\n"
                        f"**Date:** {formatted_date}\n"
                        f"**Read:** {'Yes' if email.get('isRead', False) else 'No'}\n"
                        f"**ID:** {email.get('id', 'Unknown')}\n"
                    )
                    
                    if email.get("hasAttachments", False):
                        email_info += "**Attachments:** Yes\n"
                    
                    email_list.append(email_info)
                
                response = f"Found {len(emails)} email(s):\n\n" + "\n---\n\n".join(email_list)
                
                return [TextContent(type="text", text=response)]
            
            elif name == "read_email":
                email_id = arguments["email_id"]
                
                result = await self._make_graph_request(f"/me/messages/{email_id}")
                
                if not result:
                    return [TextContent(
                        type="text",
                        text=f"Failed to retrieve email with ID: {email_id}"
                    )]
                
                sender = result.get("sender", {}).get("emailAddress", {})
                recipients = result.get("toRecipients", [])
                
                # Format recipients
                to_list = ", ".join([
                    f"{r['emailAddress']['name']} <{r['emailAddress']['address']}>" 
                    for r in recipients
                ])
                
                # Get body content
                body = result.get("body", {})
                content = body.get("content", "No content")
                
                email_details = (
                    f"**Subject:** {result.get('subject', 'No Subject')}\n\n"
                    f"**From:** {sender.get('name', 'Unknown')} <{sender.get('address', 'Unknown')}>\n"
                    f"**To:** {to_list}\n"
                    f"**Date:** {result.get('receivedDateTime', 'Unknown')}\n\n"
                    f"**Body:**\n{content}"
                )
                
                return [TextContent(type="text", text=email_details)]
            
            elif name == "get_folders":
                result = await self._make_graph_request("/me/mailFolders")
                
                if not result:
                    return [TextContent(
                        type="text",
                        text="Failed to retrieve folders. Please check authentication."
                    )]
                
                folders = result.get("value", [])
                
                folder_list = []
                for folder in folders:
                    folder_info = (
                        f"**{folder.get('displayName', 'Unknown')}**\n"
                        f"  Unread: {folder.get('unreadItemCount', 0)}\n"
                        f"  Total: {folder.get('totalItemCount', 0)}"
                    )
                    folder_list.append(folder_info)
                
                response = "Email Folders:\n\n" + "\n\n".join(folder_list)
                
                return [TextContent(type="text", text=response)]
            
            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]

async def main():
    """Main entry point for the server"""
    # Check for required environment variables
    required_vars = ['OUTLOOK_CLIENT_ID', 'OUTLOOK_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file or environment")
        return
    
    server = MyGirlFridayServer()
    
    # Run the server
    options = server.server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            options,
            raise_exceptions=True
        )

if __name__ == "__main__":
    asyncio.run(main())
