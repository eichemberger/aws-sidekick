import asyncio
from typing import Optional, Dict, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from infrastructure.logging import get_logger


@dataclass
class AccountContext:
    """Cached account context information"""
    alias: str
    is_valid: bool
    last_validated: datetime
    account_id: Optional[str] = None
    region: Optional[str] = None


class AccountContextCache:
    """High-performance cache for AWS account context to avoid redundant validations"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default TTL
        self._cache: Dict[str, AccountContext] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._logger = get_logger(__name__)
        self._validation_locks: Dict[str, asyncio.Lock] = {}
    
    async def get_validated_context(
        self, 
        account_alias: str,
        validator_func
    ) -> AccountContext:
        """Get validated account context with intelligent caching"""
        
        # Check if we have a valid cached entry
        cached = self._get_cached_context(account_alias)
        if cached and self._is_cache_valid(cached):
            self._logger.debug(f"Using cached context for account '{account_alias}'")
            return cached
        
        # Ensure only one validation per account happens at a time
        if account_alias not in self._validation_locks:
            self._validation_locks[account_alias] = asyncio.Lock()
        
        async with self._validation_locks[account_alias]:
            # Double-check cache after acquiring lock (another request might have validated)
            cached = self._get_cached_context(account_alias)
            if cached and self._is_cache_valid(cached):
                return cached
            
            # Validate and cache the context
            try:
                self._logger.debug(f"Validating account context for '{account_alias}'")
                account_info = await validator_func(account_alias)
                
                context = AccountContext(
                    alias=account_alias,
                    is_valid=True,
                    last_validated=datetime.now(),
                    account_id=getattr(account_info, 'account_id', None),
                    region=getattr(account_info, 'region', None)
                )
                
                self._cache[account_alias] = context
                self._logger.debug(f"Cached valid context for account '{account_alias}'")
                return context
                
            except Exception as e:
                # Cache failed validation to avoid immediate retry
                context = AccountContext(
                    alias=account_alias,
                    is_valid=False,
                    last_validated=datetime.now()
                )
                # Cache failed validation for shorter time (1 minute)
                self._cache[account_alias] = context
                self._logger.warning(f"Cached invalid context for account '{account_alias}': {e}")
                raise
    
    def _get_cached_context(self, account_alias: str) -> Optional[AccountContext]:
        """Get cached context if it exists"""
        return self._cache.get(account_alias)
    
    def _is_cache_valid(self, context: AccountContext) -> bool:
        """Check if cached context is still valid"""
        age = datetime.now() - context.last_validated
        # Use shorter TTL for failed validations
        ttl = timedelta(seconds=60) if not context.is_valid else self._ttl
        return age < ttl
    
    def invalidate_account(self, account_alias: str) -> None:
        """Invalidate cached context for an account"""
        if account_alias in self._cache:
            del self._cache[account_alias]
            self._logger.debug(f"Invalidated cache for account '{account_alias}'")
    
    def clear_cache(self) -> None:
        """Clear all cached contexts"""
        self._cache.clear()
        self._logger.debug("Cleared all account context cache")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for monitoring"""
        valid_entries = sum(1 for ctx in self._cache.values() if ctx.is_valid and self._is_cache_valid(ctx))
        invalid_entries = len(self._cache) - valid_entries
        
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "invalid_entries": invalid_entries,
            "locks_active": len(self._validation_locks)
        } 