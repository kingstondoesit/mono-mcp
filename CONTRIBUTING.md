# Contributing to Mono Banking MCP Server

Thank you for your interest in contributing to the Mono Banking MCP Server! This guide will help you get started with contributing to this project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- A Mono account and API keys (for testing)
- Claude Desktop (for MCP integration testing)

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mono-mcp.git
   cd mono-mcp
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/sin4ch/mono-mcp.git
   ```

## 🛠 Development Setup

### 1. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
MONO_SECRET_KEY=your_mono_secret_key_here
MONO_PUBLIC_KEY=your_mono_public_key_here
```

### 4. Verify Installation

```bash
# Run tests to ensure everything works
python -m pytest tests/ -v

# Start the MCP server to test
python -m mono_banking_mcp.server
```

## 🔄 Making Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 2. Development Workflow

- **Keep commits focused**: Each commit should represent a single logical change
- **Write descriptive commit messages**: Use the format:
  ```
  Add feature: Brief description
  
  - Detailed explanation of what was changed
  - Why the change was necessary
  - Any breaking changes or migration notes
  ```
- **Reference issues**: Include `Fixes #123` or `Addresses #123` in commit messages

### 3. Stay Updated

Regularly sync with the upstream repository:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git checkout your-feature-branch
git rebase main
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=mono_banking_mcp --cov-report=html

# Run specific test file
python -m pytest tests/test_mono_banking.py -v
```

### Test Requirements

- **All new features** must include tests
- **Bug fixes** should include regression tests  
- **Maintain test coverage** above 80%
- **Test both success and error scenarios**

### Test Categories

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test API interactions (marked with `@pytest.mark.integration`)
3. **Performance Tests**: Test concurrent operations and large datasets
4. **Error Handling**: Test all error scenarios and edge cases

### Using Make Commands

```bash
# Quick unit tests only
make test

# All tests with coverage report
make test-all

# Integration tests (requires API key)
make test-integration

# Performance benchmarks
make test-performance

# Full CI pipeline locally
make ci
```

### Test Structure Guidelines

```python
"""Test module docstring explaining what is being tested."""

import pytest
from unittest.mock import AsyncMock, patch
from mono_banking_mcp.server import your_tool

class TestYourFeature:
    """Test class for specific feature or tool."""

    @pytest.fixture
    def mock_client(self):
        """Mock MonoClient for testing."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_successful_operation(self, mock_client):
        """Test successful operation with proper response."""
        mock_client.method.return_value = {"status": True, "data": {}}
        
        with patch('mono_banking_mcp.server.mono_client', mock_client):
            result = await your_tool("param")
            
        assert result["success"] is True

    @pytest.mark.asyncio  
    async def test_error_handling(self, mock_client):
        """Test proper error handling."""
        mock_client.method.side_effect = Exception("API Error")
        
        result = await your_tool("param")
        assert result["success"] is False
```

## 🎨 Code Style

### Python Style Guidelines

- **Follow PEP 8**: Use consistent Python style
- **Type hints**: Include type annotations for all functions
- **Docstrings**: Document all public functions and classes
- **Format with Black**: Run `black .` before committing
- **Lint with Ruff**: Run `ruff check .` to catch issues

### Example Function

```python
async def get_account_balance(account_id: str) -> Dict[str, Any]:
    """
    Get current account balance for a linked account.
    
    Args:
        account_id: The account ID to get balance for
        
    Returns:
        Dictionary containing account balance information
        
    Raises:
        MonoAPIError: If the API request fails
    """
    # Implementation here
    pass
```

## 📤 Submitting Changes

### 1. Pre-submission Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear
- [ ] Changes are focused and atomic

### 2. Create Pull Request

1. **Push your branch**:
   ```bash
   git push origin your-feature-branch
   ```

2. **Create PR on GitHub** with:
   - **Clear title**: Summarize the change in one line
   - **Detailed description**: Explain what, why, and how
   - **Reference issues**: Use "Fixes #123" or "Addresses #123"
   - **Screenshots**: If UI/output changes are involved

### 3. PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass

## Related Issues
Fixes #123
```

## 📝 Issue Guidelines

### Reporting Bugs

Include:
- **Clear title**: Summarize the problem
- **Steps to reproduce**: Detailed reproduction steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: Python version, OS, etc.
- **Error messages**: Full stack traces

### Feature Requests

Include:
- **Use case**: Why is this needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Other approaches considered
- **Implementation notes**: Technical considerations

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or improvement
- `documentation`: Documentation updates
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed

## 🤝 Community Guidelines

- **Be respectful**: Treat everyone with kindness and respect
- **Be collaborative**: Work together to solve problems
- **Be patient**: Remember that everyone is learning
- **Be constructive**: Provide helpful feedback and suggestions

## 🎯 Development Focus Areas

Current areas where contributions are especially welcome:

1. **Test Coverage**: Expand tests for banking tools
2. **Error Handling**: Improve error scenarios and edge cases  
3. **Documentation**: API documentation and examples
4. **Performance**: Optimize API calls and response handling
5. **Webhook Testing**: Add integration tests for webhook server

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Review**: Request reviews on your PRs

---

Thank you for contributing to the Mono Banking MCP Server! 🚀
