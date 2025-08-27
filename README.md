# Mono Banking MCP Server

A **Model Context Protocol (MCP)** server for Nigerian banking operations using the [Mono Open Banking API](https://mono.co).

## Features

- **Account Management**: Link and manage Nigerian bank accounts
- **Real-time Balances**: Get current account balances in Naira (₦)
- **Payment Processing**: Initiate payments using Mono DirectPay
- **Transaction History**: Retrieve detailed transaction records
- **Account Verification**: Verify recipient account names before payments
- **BVN Lookup**: Identity verification using Bank Verification Number
- **Webhook Support**: Real-time event handling for production use

## Architecture

Clean, event-driven architecture optimized for AI assistant integration using FastMCP and async Python.

## Local Development

### Prerequisites
- Python 3.12+
- Mono API credentials from [mono.co](https://mono.co)

### Setup
```bash
git clone <your-repo-url>
cd mono-banking-mcp
pip install -r requirements.txt
```

### Environment Configuration
Create `.env` file:
```env
MONO_SECRET_KEY=your_actual_mono_secret_key_here
MONO_WEBHOOK_SECRET=your_webhook_secret_here
MONO_BASE_URL=https://api.withmono.com
```

### Run Server
```bash
python -m mono_banking_mcp.server
```

### Run Webhook Server
```bash
python -m mono_banking_mcp.webhook_server
```

## Claude Desktop Integration

Add to `~/.config/claude-desktop/config.json`:
```json
{
  "mcpServers": {
    "mono-banking": {
      "command": "python",
      "args": ["-m", "mono_banking_mcp.server"],
      "env": {
        "MONO_SECRET_KEY": "your_actual_mono_secret_key_here"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_linked_accounts` | List all linked bank accounts |
| `get_account_balance` | Get current account balance |
| `get_account_details` | Get comprehensive account info with BVN |
| `get_transaction_history` | Retrieve transaction records |
| `verify_account_name` | Verify recipient account details |
| `initiate_payment` | Start a payment via DirectPay |
| `verify_payment` | Check payment status |
| `lookup_bvn` | BVN identity verification |
| `get_nigerian_banks` | List supported Nigerian banks |
| `initiate_account_linking` | Start account linking process |

## Use Cases

- **Personal Banking**: "Check my balance", "Send ₦5000 to John's account"
- **Account Management**: "Link my GTBank account", "Show transaction history"
- **Identity Verification**: "Lookup BVN 12345678901", "Verify account details"
- **Payment Processing**: "Initiate payment to 0123456789 at Access Bank"

## Security Best Practices

### API Security
- Store secret keys in environment variables only
- Use HTTPS for all communications
- Rotate keys regularly

### Payment Security
- Always verify account names before payments
- Validate payment amounts and recipient details
- Use webhook verification for real-time events

### Webhook Security
- Verify webhook signatures using `mono-webhook-secret`
- Use HTTPS endpoints for webhook URLs
- Implement replay attack protection

### Environment Security
- Use sandbox environment for testing
- Separate production and development credentials
- Monitor API usage and set up alerts
