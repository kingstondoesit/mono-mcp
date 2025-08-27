# Mono Banking MCP Server

A comprehensive **Model Context Protocol (MCP)** server for Nigerian banking operations using the [Mono Open Banking API](https://mono.co).

## � Table of Contents

- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technologies Used](#️-technologies-used)
- [Project Structure](#-project-structure)
- [Installation and Setup](#-installation-and-setup)
- [Usage](#-usage)
- [Available Banking Tools](#️-available-banking-tools)
- [Development](#-development)
- [Contributing](#-contributing)

## �🚀 Key Features

Complete Nigerian banking operations through AI assistants with account management, real-time payments, BVN verification, and secure webhook integration via the Model Context Protocol (MCP).

## 📊 Architecture

```mermaid
sequenceDiagram
    participant User as 👤 User
    participant AI as 🤖 AI Assistant<br/>(Claude/Gemini)
    participant MCP as 🔌 MCP Server<br/>(FastMCP)
    participant Client as 📡 Mono Client<br/>(httpx)
    participant API as 🏦 Mono API<br/>(Nigerian Banks)

    User->>AI: "Check my account balance"
    AI->>MCP: list_tools()
    MCP-->>AI: Available banking tools

    AI->>MCP: get_account_balance(account_id)
    MCP->>Client: get_account_balance(account_id)
    Client->>API: GET /accounts/{id}/balance
    API-->>Client: {"balance": 50000, "currency": "NGN"}
    Client-->>MCP: Account balance data
    MCP-->>AI: {"success": true, "balance": "₦500.00"}
    AI-->>User: "Your account balance is ₦500.00"

    Note over User,API: Payment Flow
    User->>AI: "Send ₦1000 to 0123456789 at GTBank"
    AI->>MCP: verify_account_name("0123456789", "058")
    MCP->>Client: resolve_account_name()
    Client->>API: POST /misc/banks/resolve
    API-->>Client: {"account_name": "JOHN DOE"}
    Client-->>MCP: Account verification
    MCP-->>AI: {"verified": true, "account_name": "JOHN DOE"}

    AI->>MCP: initiate_payment(amount, recipient, customer)
    MCP->>Client: initiate_payment()
    Client->>API: POST /payments/initiate
    API-->>Client: {"mono_url": "https://connect.mono.co/..."}
    Client-->>MCP: Payment authorization URL
    MCP-->>AI: {"success": true, "mono_url": "..."}
    AI-->>User: "Payment initiated. Complete at: [URL]"
```

## 🛠️ Technologies Used

- **Python 3.12+** - Modern Python with async/await support
- **FastMCP** - Simplified MCP server implementation with decorators
- **httpx** - Modern async HTTP client for API communication
- **Mono Open Banking API v2** - Nigerian banking infrastructure
- **python-dotenv** - Environment variable management
- **uv** - Fast Python package manager (recommended)

## 📁 Project Structure

```
mono-banking-mcp/
├── mono_banking_mcp/           # Main package
│   ├── __init__.py            # Package initialization
│   ├── server.py              # FastMCP server with comprehensive banking tools
│   ├── mono_client.py         # Mono API client with httpx
│   ├── webhook_server.py      # FastAPI webhook server for real-time events
│   └── database.py            # SQLite database for webhook events storage
├── tests/                     # Test suite
│   └── test_mono_banking.py   # Unit tests for MCP tools
├── .vscode/                   # VS Code configuration
│   └── settings.json          # Editor settings for development
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Modern Python project configuration
├── claude_desktop_config.json # Claude Desktop MCP integration
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules and build artifacts
└── README.md                 # This comprehensive documentation
```

## 📦 Installation and Setup

### Prerequisites

- **Python 3.12+** - Modern Python with async/await support
- **pip** or **[uv](https://docs.astral.sh/uv/)** - Python package manager
- **Mono API credentials** - Get them at [mono.co](https://mono.co)

### Step 1: Get Mono API Credentials

1. **Sign up & KYC**: Create an account on the [Mono Dashboard](https://app.withmono.com) and complete KYC verification
2. **Create an App**: Go to **Apps** → **Create app** and choose product scopes:
   - **Connect**: For account linking and data access
   - **Payments**: For DirectPay transactions
3. **Obtain API Keys**: Copy your **Secret Key** and **Public Key** from the dashboard
4. **Configure Webhooks** (optional): Set up webhook URLs for real-time events

### Step 2: Project Setup

1. **Clone and setup the project:**
   ```bash
   git clone <your-repo-url>
   cd mono-banking-mcp
   ```

2. **Install dependencies:**
   ```bash
   # Using pip (recommended)
   pip install -r requirements.txt

   # Or using uv (faster)
   uv pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Mono API credentials
   ```

### Step 3: Environment Configuration

Create a `.env` file with your Mono credentials:

```env
MONO_SECRET_KEY=your_actual_mono_secret_key_here
MONO_PUBLIC_KEY=your_mono_public_key_here
MONO_WEBHOOK_SECRET=your_webhook_secret_here
MONO_BASE_URL=https://api.withmono.com
MONO_ENVIRONMENT=sandbox  # or 'production'
```

## 🚀 Usage

### Standalone Server

Run the MCP server directly:

```bash
# Run the server
python -m mono_banking_mcp.server

# Or with environment variables
MONO_SECRET_KEY=your_key python -m mono_banking_mcp.server
```

### Claude Desktop Integration

Add to your Claude Desktop configuration (`~/.config/claude-desktop/config.json`):

```json
{
  "mcpServers": {
    "mono-banking": {
      "command": "python",
      "args": ["-m", "mono_banking_mcp.server"],
      "cwd": "/path/to/mono-banking-mcp",
      "env": {
        "MONO_SECRET_KEY": "your_actual_mono_secret_key_here",
        "MONO_BASE_URL": "https://api.withmono.com"
      }
    }
  }
}
```

### VS Code / GitHub Copilot Integration

The project includes VS Code configuration files in `.vscode/` for seamless integration with GitHub Copilot's MCP support.

### Usage Examples

Once connected to an AI assistant, you can use natural language commands:

- *"List all my linked bank accounts"*
- *"Check the balance for account ID abc123"*
- *"Initiate a payment of ₦5000 to account 1234567890 at Access Bank"*
- *"Show me all Nigerian banks and their codes"*
- *"Verify account name for account 0123456789 at GTBank"*

## 🛠️ Available Banking Tools

The server provides these comprehensive banking tools:

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_linked_accounts` | List all linked bank accounts | None |
| `get_account_balance` | Get current account balance | `account_id` |
| `get_account_info` | Get detailed account information | `account_id` |
| `get_transaction_history` | Retrieve transaction records | `account_id`, `limit`, `page` |
| `verify_account_name` | Verify recipient account details | `account_number`, `bank_code` |
| `initiate_payment` | Start a payment via DirectPay | `amount`, recipient details, customer info |
| `verify_payment` | Check payment status | `reference` |
| `get_nigerian_banks` | List supported Nigerian banks | None |
| `initiate_account_linking` | Start account linking process | customer details |

### Tool Details

#### Account Management
- **`list_linked_accounts`**: Returns all bank accounts linked to your business
- **`get_account_balance`**: Retrieves real-time balance for a specific account
- **`get_account_info`**: Gets comprehensive account details including bank information
- **`get_transaction_history`**: Fetches transaction records with pagination support

#### Payment Operations
- **`verify_account_name`**: Verifies recipient account name before payments (recommended)
- **`initiate_payment`**: Starts a DirectPay payment flow (returns authorization URL)
- **`verify_payment`**: Checks the status of a payment using its reference

#### Utility Functions
- **`get_nigerian_banks`**: Returns complete list of supported banks with codes
- **`initiate_account_linking`**: Starts the account linking process for new customers

## 🚀 Development

### Quick Start
```bash
# Clone and setup
git clone <your-repo-url>
cd mono-banking-mcp

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Mono API key

# Run server
python -m mono_banking_mcp.server
```

### Testing
```bash
# Run tests
pytest

# Run with coverage (install coverage first: pip install coverage)
coverage run -m pytest
coverage report

# Test specific functionality
python -c "from mono_banking_mcp.server import mcp; print('Server works!')"
```

### Code Quality
```bash
# Format code
black mono_banking_mcp/

# Lint code
ruff check mono_banking_mcp/

# Type checking
mypy mono_banking_mcp/
```

## 🤝 Contributing

We welcome contributions to the Mono Banking MCP Server! For questions or help getting started, please open an issue or check our [Contributing Guide](CONTRIBUTING.md).

**Quick Start for Contributors:**
```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/mono-mcp.git
cd mono-mcp

# Set up development environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create feature branch and start developing
git checkout -b feature/your-feature-name
```