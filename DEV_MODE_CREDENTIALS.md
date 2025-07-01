# Development Mode Credential Persistence

## Overview

For development convenience, AWS credentials can persist across application restarts when running in development mode.

## How It Works

### Production Mode (Default - Secure)
- ✅ **Credentials stored in memory only**
- ✅ **No disk persistence**
- ❌ **Credentials lost on restart** (security feature)

### Development Mode (Convenience)
- ✅ **Credentials stored in memory**
- ⚠️ **Also persisted to local file for convenience**
- ✅ **Credentials survive restarts**
- ⚠️ **Less secure - for development only**

## Enabling Development Mode

Development mode is automatically detected when:

1. **Environment variable**: `ENVIRONMENT=development` (or `dev`, `local`)
2. **Debug flag**: `DEBUG=true`
3. **Config setting**: `debug: true` in configuration

## Credential Storage Location

In development mode, credentials are stored at:
```
~/.aws-agent-dev/credentials.json
```

**Security Notes:**
- File permissions set to `0o600` (owner only)
- Stored in plain JSON for simplicity
- **Never commit this file to version control**
- **Only use in trusted development environments**

## File Format

```json
{
  "my-dev-account": {
    "access_key_id": "AKIA...",
    "secret_access_key": "xyz123...",
    "session_token": null,
    "region": "us-east-1", 
    "profile": null
  },
  "my-prod-account": {
    "access_key_id": null,
    "secret_access_key": null,
    "session_token": null,
    "region": "us-west-2",
    "profile": "production"
  }
}
```

## Usage

1. **Register account with credentials** via the UI
2. **Restart the application**
3. **Credentials automatically loaded** from dev storage
4. **Select your account** - it will have credentials available

## Checking Status

Visit the debug endpoint to check credential status:
```
http://localhost:8000/debug/credentials-status
```

Or run the debug script:
```bash
python debug_credentials.py
```

## Security Considerations

### ✅ Safe for Development
- Local development environment
- Trusted machine/VM
- No shared access
- Convenience over security

### ❌ Never in Production
- Production servers
- Shared environments  
- CI/CD pipelines
- Public repositories

## Cleanup

To remove stored dev credentials:
```bash
rm -rf ~/.aws-agent-dev/
```

Or use the clear all credentials function in the UI.

## Environment Variables

```bash
# Enable development mode
export ENVIRONMENT=development
export DEBUG=true

# Start the application
python src/main.py
```

## Production Deployment

In production, ensure:
```bash
export ENVIRONMENT=production
export DEBUG=false
```

This will automatically disable credential persistence and use secure memory-only storage. 