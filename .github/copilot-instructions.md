# MemoryBridge AI Agent Instructions

## Architecture Overview

MemoryBridge is a cross-agent memory sharing platform with a layered architecture:

- **CLI Layer** (`src/memorybridge/cli/`): Typer-based command-line interface with 10 commands
- **Core Layer** (`src/memorybridge/core/`): Memory data models and abstract service interfaces
- **Storage Layer** (`src/memorybridge/storage/`): Pluggable backends (SQLite primary, MongoDB planned)
- **Skills Layer** (`src/memorybridge/skill_tools.py` + `skills/memorybridge/`): OpenClaw integration with 9 tools

## Key Design Patterns

### Memory Model
```python
# Core data structure - always use dataclasses for consistency
@dataclass
class Memory:
    content: str
    memory_type: MemoryType = MemoryType.LONG_TERM  # session/long_term
    priority: MemoryPriority = MemoryPriority.P1     # p0/p1/p2/p3
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Storage Abstraction
```python
# All storage backends implement MemoryService interface
class SQLiteStorage(MemoryService):
    # Uses JSON fields in SQLite for flexible metadata/tags/embedding
    # Database: ~/.memorybridge/memories.db
```

### CLI Commands
```python
# Use Typer with lazy-loaded global storage instance
@app.command()
def add(content: str, type: str = "long_term", priority: str = "p1"):
    storage = get_storage()  # Global SQLiteStorage instance
```

## Development Workflows

### Testing
```bash
# Run full test suite with coverage
pytest tests/ -v --cov=src/memorybridge --cov-report=term-missing

# Key test patterns:
# - Use tmp_path fixture for isolated test databases
# - Test both CLI commands and core service methods
# - 27 test cases covering all major functionality
```

### Installation & Setup
```bash
# Development install
pip3 install -e . --break-system-packages

# Skill installation for OpenClaw
bash install-skill.sh  # Installs to ~/.openclaw/workspace/skills/
```

### CLI Usage Examples
```bash
# Add memory with metadata
memorybridge add "Python is a programming language" --type long_term --priority p1 --tags "python,language"

# Search with filters
memorybridge search "Python" --limit 5

# Export/import for backup
memorybridge export -o backup.json
memorybridge import -i backup.json
```

## Code Conventions

### Imports
```python
# Relative imports within package
from ..core.memory import Memory, MemoryType
from ..storage.sqlite import SQLiteStorage

# External dependencies (minimal set)
import typer, sqlite3, json, networkx
```

### Error Handling
```python
# CLI validation with typer.Exit
try:
    memory_type = MemoryType(type_arg)
except ValueError:
    typer.echo(f"❌ Invalid type: {type_arg}")
    raise typer.Exit(1)
```

### JSON Storage Pattern
```python
# SQLite stores complex data as JSON strings
metadata_json = json.dumps(memory.metadata)
tags_json = json.dumps(memory.tags)

# Retrieval converts back to Python objects
metadata = json.loads(row[4])
tags = json.loads(row[5])
```

## Skill Integration

### OpenClaw Tools
- `memory_add()` - Add memories with full parameter support
- `memory_search()` - Semantic search with filters
- `memory_list()` - Paginated listing
- `memory_get()` - Retrieve by ID
- `memory_update()` - Modify existing memories
- `memory_delete()` - Remove memories
- `memory_export()` - JSON export
- `memory_import()` - JSON import
- `memory_status()` - System statistics

### Tool Function Signatures
```python
def memory_add(
    content: str,
    type: str = "long_term",
    priority: str = "p1",
    tags: Optional[str] = None,  # Comma-separated string
    db_path: Optional[str] = None
) -> dict:
    # Returns {"success": bool, "memory": dict, "error": str}
```

## File Organization

- `src/memorybridge/core/memory.py` - Data models and enums
- `src/memorybridge/core/service.py` - Abstract service interface
- `src/memorybridge/storage/sqlite.py` - Primary storage backend
- `src/memorybridge/cli/main.py` - CLI command definitions
- `src/memorybridge/skill_tools.py` - OpenClaw tool implementations
- `skills/memorybridge/` - OpenClaw skill packaging
- `tests/` - pytest test suite with fixtures in conftest.py

## Current Project State

- **Phase 1 Complete**: Core memory service, CLI, SQLite storage, OpenClaw skills
- **Phase 2 Planned**: Knowledge graph with NetworkX, visualization with PyVis
- **Phase 3 Planned**: MongoDB backend, OSS backup
- **Phase 4 Planned**: Additional agent integrations

Focus new features on extending the MemoryService interface rather than modifying existing patterns.</content>
<parameter name="filePath">/Users/shmily/workspace/MemoryBridge/.github/copilot-instructions.md