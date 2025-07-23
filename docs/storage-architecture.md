# Storage Architecture

## Overview

The ContextManager has been refactored to use a pluggable storage backend architecture. This design allows for easy extension to support different storage mechanisms while maintaining backward compatibility.

## Architecture

### Storage Abstraction

The storage system consists of:

1. **StorageBackend (Abstract Base Class)**
   - Defines the interface that all storage implementations must follow
   - Located in `src/contextr/storage/base.py`
   - Methods: `save()`, `load()`, `exists()`, `delete()`, `list_keys()`

2. **JsonStorage (Default Implementation)**
   - File-based storage using JSON format
   - Located in `src/contextr/storage/json_storage.py`
   - Maintains backward compatibility with existing state.json format
   - Supports nested key structures (e.g., "states/my_state")

### Integration with ContextManager

The ContextManager accepts an optional `storage` parameter in its constructor:

```python
manager = ContextManager()  # Uses default JsonStorage
manager = ContextManager(storage=custom_storage)  # Uses custom storage
```

## Benefits

1. **Extensibility**: Easy to add new storage backends (e.g., SQLite, Redis, Cloud)
2. **Testability**: Storage can be mocked for unit testing
3. **Backward Compatibility**: Default behavior unchanged
4. **Separation of Concerns**: Storage logic separated from business logic

## Future Extensions

This architecture enables future features such as:
- Profile support (different storage locations per profile)
- Cloud-based storage for team collaboration
- Database backends for better performance with large contexts
- Encrypted storage for sensitive codebases

## Implementation Details

### Key Structure

Storage keys follow a hierarchical structure:
- `"state"` - Current context state
- `"states/{name}"` - Saved named states

### Data Format

The stored data maintains the original JSON structure:
```json
{
    "files": ["relative/path/to/file.py"],
    "watched_patterns": ["src/**/*.py"],
    "ignore_patterns": ["*.pyc"],
    "negation_patterns": []
}
```