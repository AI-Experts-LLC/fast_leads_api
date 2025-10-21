# 🤝 Contributing to Salesforce Lead Enrichers

Thank you for your interest in contributing to the Salesforce Lead Enrichers project! This document provides guidelines for contributing to this repository.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Submitting Changes](#submitting-changes)
- [Testing](#testing)
- [Documentation](#documentation)

---

## 🤝 Code of Conduct

This project aims to foster an open and welcoming environment. We expect all contributors to:

- Be respectful and professional in all interactions
- Provide constructive feedback
- Focus on what is best for the project and community
- Show empathy towards other community members

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Git
- Access to required API services (see README.md)
- Salesforce developer account (for testing)

### Initial Setup

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork
   git clone git@github.com:YOUR-USERNAME/salesforce_lead_enrichers.git
   cd salesforce_lead_enrichers
   ```

2. **Set up upstream remote**
   ```bash
   git remote add upstream git@github.com:AI-Experts-LLC/salesforce_lead_enrichers.git
   ```

3. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env  # Create from template
   # Edit .env with your API keys
   ```

6. **Test the setup**
   ```bash
   hypercorn main:app --reload
   curl http://localhost:8000/health
   ```

---

## 🔄 Development Workflow

### 1. Sync with upstream

Before starting new work, sync with the main repository:

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

### 2. Create a feature branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
# or
git checkout -b docs/documentation-update
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or updates

### 3. Make your changes

- Write clean, readable code
- Follow existing code style
- Add tests for new functionality
- Update documentation as needed

### 4. Commit your changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "✨ Add feature: Description of feature

- Detailed point 1
- Detailed point 2
- Related to issue #123"
```

**Commit message emojis:**
- ✨ `:sparkles:` - New feature
- 🐛 `:bug:` - Bug fix
- 📚 `:books:` - Documentation
- ♻️ `:recycle:` - Refactoring
- ✅ `:white_check_mark:` - Tests
- 🔧 `:wrench:` - Configuration
- 🚀 `:rocket:` - Performance improvement

### 5. Push to your fork

```bash
git push origin feature/your-feature-name
```

### 6. Open a Pull Request

- Go to your fork on GitHub
- Click "Compare & pull request"
- Fill out the PR template
- Link any related issues

---

## 📝 Coding Standards

### Python Style

Follow [PEP 8](https://pep8.org/) style guidelines:

- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use descriptive variable names
- Add docstrings to all functions/classes

**Example:**
```python
async def enrich_contact(contact_id: str, overwrite: bool = False) -> dict:
    """
    Enrich a Salesforce contact with AI-generated personalized data.

    Args:
        contact_id: Salesforce contact ID (18 characters)
        overwrite: Whether to overwrite existing enriched data

    Returns:
        Dictionary containing enrichment status and data

    Raises:
        HTTPException: If contact not found or enrichment fails
    """
    # Implementation...
```

### Code Organization

- **Services** (`app/services/`) - Business logic and API integrations
- **Enrichers** (`app/enrichers/`) - Specialized enrichment modules
- **Tests** (`tests/`) - Test scripts and examples
- **Utils** (`utils/`) - Utility scripts and helpers
- **Docs** (`docs/`) - Additional documentation

### Error Handling

Always include proper error handling:

```python
try:
    result = await external_api_call()
    if not result.get("success"):
        raise ValueError(f"API call failed: {result.get('error')}")
    return result
except Exception as e:
    logger.error(f"Error in function_name: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Async/Await

Use async/await for all I/O operations:

```python
# ✅ Good
async def fetch_data():
    result = await api_call()
    return result

# ❌ Bad
def fetch_data():
    result = api_call()  # Blocking call
    return result
```

---

## 🧪 Testing

### Running Tests

```bash
# Test single endpoint
python tests/test_three_step_discovery.py

# Test batch processing
python tests/test_batch_three_step.py

# Test enrichment
python tests/test_enrichment_api.py
```

### Writing Tests

Create test scripts in `tests/` directory:

```python
"""
Test prospect discovery for specific hospital
"""
import asyncio
from app.services.three_step_prospect_discovery import three_step_prospect_discovery_service

async def test_hospital():
    result = await three_step_prospect_discovery_service.step1_search_and_filter(
        company_name="Mayo Clinic",
        company_city="Rochester",
        company_state="Minnesota"
    )

    assert result.get("success"), "Step 1 should succeed"
    assert len(result.get("qualified_prospects", [])) > 0, "Should find prospects"

    print(f"✅ Test passed: Found {len(result['qualified_prospects'])} prospects")

if __name__ == "__main__":
    asyncio.run(test_hospital())
```

### Test Coverage

When adding new features:
- ✅ Add at least one test case
- ✅ Test success scenarios
- ✅ Test error handling
- ✅ Test edge cases

---

## 📖 Documentation

### Update Documentation When:

1. **Adding new endpoints** - Update `main.py` docstrings and README.md
2. **Changing API behavior** - Update relevant .md files
3. **Adding environment variables** - Update README.md and CLAUDE.md
4. **Fixing bugs** - Document the fix in commit message
5. **Adding features** - Create/update documentation in `docs/`

### Documentation Files

- `README.md` - Project overview, setup, API reference
- `CLAUDE.md` - Development guide for AI assistants
- `THREE_STEP_PIPELINE.md` - Complete pipeline documentation
- `AUTHENTICATION.md` - API key authentication
- `CONTRIBUTING.md` - This file
- `example_objects/README.md` - Salesforce object structure

### Inline Documentation

Add comprehensive docstrings:

```python
async def discover_prospects_step1(request: dict):
    """
    ✅ RECOMMENDED - Step 1 of 3-Step Pipeline: Search and Filter

    **What it does:**
    - Searches LinkedIn profiles using Serper API
    - Applies basic filters (removes interns, students)
    - Applies AI title relevance scoring
    - Returns filtered prospect URLs ready for scraping

    **Request format:**
    {
        "company_name": "Mayo Clinic",
        "company_city": "Rochester",
        "company_state": "Minnesota"
    }

    **Returns:** Qualified LinkedIn URLs for Step 2
    """
```

---

## 🔍 Pull Request Guidelines

### PR Title Format

```
<emoji> <type>: <description>

Examples:
✨ feat: Add ZoomInfo contact validation
🐛 fix: Resolve company name matching bug
📚 docs: Update API authentication guide
♻️ refactor: Improve prospect filtering logic
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 📚 Documentation update
- [ ] ♻️ Refactoring
- [ ] 🧪 Test update

## Changes Made
- Detailed change 1
- Detailed change 2
- Detailed change 3

## Testing
How was this tested?

## Related Issues
Fixes #123

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
```

### Review Process

1. **Automated checks** - Must pass (if configured)
2. **Code review** - At least one approval required
3. **Documentation review** - Ensure docs are updated
4. **Test verification** - Verify tests pass locally

---

## 🏗️ Architecture Guidelines

### Adding New Services

When adding a new API integration:

1. **Create service file** - `app/services/your_service.py`
2. **Initialize service** - Create service class with connection method
3. **Add to main.py** - Import and create instance
4. **Add endpoint** - Create FastAPI endpoint with documentation
5. **Update README** - Document the new service

**Example Service:**

```python
# app/services/your_service.py
import os
from typing import Dict, Any

class YourService:
    def __init__(self):
        self.api_key = os.getenv("YOUR_API_KEY")
        self.base_url = "https://api.yourservice.com"

    async def your_method(self, param: str) -> Dict[str, Any]:
        """
        Your method description

        Args:
            param: Parameter description

        Returns:
            Result dictionary
        """
        # Implementation
        return {"success": True, "data": {}}

# Create singleton instance
your_service = YourService()
```

### Adding New Enrichers

When adding specialized enrichment:

1. **Create enricher** - `app/enrichers/your_enricher.py`
2. **Inherit base class** - If applicable
3. **Implement interface** - Follow existing patterns
4. **Add to enrichment service** - Integrate with orchestrator
5. **Document fields** - Update example_objects documentation

---

## 🔐 Security Considerations

### API Keys

- ❌ Never commit API keys to the repository
- ✅ Use environment variables
- ✅ Add `.env` to `.gitignore`
- ✅ Provide `.env.example` template

### Data Privacy

- ❌ Don't commit real Salesforce data (except example_objects)
- ✅ Use anonymized data for tests
- ✅ Document which data is sensitive
- ✅ Follow GDPR/data privacy guidelines

### Authentication

- ✅ Use API key authentication for sensitive endpoints
- ✅ Validate all inputs
- ✅ Rate limit API calls
- ✅ Log security events

---

## 💬 Getting Help

- **GitHub Issues** - Report bugs or request features
- **Discussions** - Ask questions or share ideas
- **Documentation** - Check existing docs first
- **Code Comments** - Read inline documentation

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

## 🙏 Thank You!

Thank you for contributing to Salesforce Lead Enrichers! Your contributions help make this project better for everyone.

**Happy coding!** 🚀

---

**Last Updated:** October 21, 2025
