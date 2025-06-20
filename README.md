# My Girl Friday 👩‍💼
> An MCP (Model Context Protocol) server for Microsoft Outlook integration - Your AI assistant for email, calendar, and tasks.

Named after the classic personal assistant, My Girl Friday brings your Outlook directly into Claude, eliminating constant context switching and making email management a breeze.

## 🌟 Features

### Phase 1: Email Operations (Current Focus)
- `list_emails` - View inbox and folders without leaving Claude
- `read_email` - Get full email content including attachments
- `search_emails` - Find specific messages quickly
- `get_folders` - Navigate your folder structure

### Phase 2: Email Actions (Coming Soon)
- `compose_email` - Draft emails directly in Claude
- `send_email` - Send without switching apps
- `reply_to_email` - Quick replies
- `forward_email` - Forward with context
- `move_email` - Organize your inbox
- `delete_email` - Clean up

### Phase 3: Calendar Integration (Planned)
- `list_events` - See your schedule
- `create_event` - Schedule meetings
- `update_event` - Modify appointments
- `check_availability` - Find free time

### Phase 4: Tasks & Contacts (Future)
- `list_tasks` - View Outlook tasks
- `create_task` - Turn emails into todos
- `search_contacts` - Quick contact lookup

## 🚀 Quick Start

### Prerequisites
1. Python 3.11+
2. Microsoft 365 account (personal or work/school)
3. Azure App Registration (see setup below)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/SamuraiBuddha/my-girl-friday.git
cd my-girl-friday
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Azure app credentials
```

### Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "App registrations" → "New registration"
3. Configure your app:
   - Name: "My Girl Friday MCP"
   - Supported account types: Choose based on your needs
   - Redirect URI: `http://localhost:8080` (for local development)

4. After creation, note down:
   - Application (client) ID
   - Directory (tenant) ID

5. Create a client secret:
   - Go to "Certificates & secrets"
   - New client secret
   - Copy the secret value immediately

6. Set API permissions:
   - Add permissions → Microsoft Graph
   - Delegated permissions:
     - `Mail.Read`
     - `Mail.ReadWrite` 
     - `Mail.Send`
     - `Calendar.Read`
     - `Calendar.ReadWrite`
     - `Tasks.Read`
     - `Tasks.ReadWrite`
     - `User.Read`

### Configuration

Add to your Claude Desktop config:

```json
{
  "my-girl-friday": {
    "command": "python",
    "args": ["-m", "my_girl_friday"],
    "env": {
      "OUTLOOK_CLIENT_ID": "your-client-id",
      "OUTLOOK_CLIENT_SECRET": "your-client-secret", 
      "OUTLOOK_TENANT_ID": "your-tenant-id"
    }
  }
}
```

## 📖 Usage Examples

### Check Recent Emails
```
"Friday, check my emails from today"
"Show me unread messages"
"Any emails from Jordan about the Chicago project?"
```

### Search and Filter
```
"Find all emails about blockchain"
"Show me emails with attachments from this week"
"Check for meeting invites"
```

### Email Management
```
"Read the latest email from Marie"
"Show me emails in the Projects folder"
"Draft a reply to the last email"
```

## 🏗️ Architecture

My Girl Friday uses:
- **Microsoft Graph API** for Outlook access
- **MSAL (Microsoft Authentication Library)** for OAuth2
- **MCP SDK** for Claude integration
- **Token caching** for seamless authentication

## 🤝 Integration with Other MCPs

My Girl Friday works beautifully with:
- **Memory MCP**: Tracks email interactions
- **Orchestrator**: Routes email-related requests
- **Blockchain MCP**: Creates audit trails of important emails

## 📝 Development

### Project Structure
```
my-girl-friday/
├── my_girl_friday/
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py          # Main MCP server
│   ├── auth.py            # Authentication handling
│   ├── email_handler.py   # Email operations
│   ├── calendar_handler.py # Calendar operations (future)
│   └── models.py          # Data models
├── pyproject.toml
├── README.md
└── .env.example
```

### Running in Development
```bash
# With environment variables set
python -m my_girl_friday

# Or with inline env vars
OUTLOOK_CLIENT_ID=xxx python -m my_girl_friday
```

## 🔒 Security

- Credentials are never stored in code
- OAuth2 tokens are cached securely
- All API calls use Microsoft's secure Graph API
- Supports both personal and organizational accounts

## 🐛 Troubleshooting

### Authentication Issues
- Ensure your Azure app has the correct permissions
- Check that redirect URI matches your setup
- Verify client ID and secret are correct

### Token Errors
- Delete the token cache and re-authenticate
- Check if your app registration is active

### Permission Denied
- Ensure you've granted admin consent for organizational apps
- Verify the user has access to the requested resources

## 🚧 Roadmap

- [x] Basic email reading
- [x] Email search functionality
- [ ] Email composition and sending
- [ ] Calendar integration
- [ ] Task management
- [ ] Contact lookup
- [ ] Attachment handling
- [ ] Email templates
- [ ] Smart filtering and categorization

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Named after the 1940 film "His Girl Friday" - the perfect assistant
- Built for Jordan Ehrig, father of 7, who desperately needed email in Claude
- Part of the MAGI ecosystem of AI tools

---

*"Who needs to switch to Outlook when you have Friday?"* 🎬
