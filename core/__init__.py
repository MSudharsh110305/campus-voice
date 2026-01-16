"""
Core module for CampusVoice AI

Complaint Processing & Routing System

This module provides the core functionality for intelligent complaint routing,
priority scoring, and authority mapping with pseudo-anonymity support.

Version: 5.0.0 - Production Ready (Async-Compatible)

Main Components:
- Config: Application configuration and constants
- AuthorityMapper: Smart complaint routing with hierarchy and bypass logic
- PriorityScorer: Multi-factor priority calculation with voting and aging

Features:
- Async-ready design (Celery-compatible)
- Production deployment support (Railway, Heroku, etc.)
- Dual Firebase credential modes (file + JSON env var)
- Redis & Celery configuration validation

Usage:
    from core import Config, AuthorityMapper, PriorityScorer
    
    config = Config()
    mapper = AuthorityMapper(config)
    scorer = PriorityScorer(config)

Or use convenience function:
    from core import initialize_core_modules
    
    config, mapper, scorer = initialize_core_modules()
"""

from .config import Config, get_config
from .authority_mapper import AuthorityMapper
from .priority_scorer import PriorityScorer

__version__ = "5.0.0"
__author__ = "CampusVoice Team"
__license__ = "MIT"

__all__ = [
    "Config",
    "get_config",
    "AuthorityMapper",
    "PriorityScorer",
    "__version__"
]


# =================== CONVENIENCE FUNCTIONS ===================

def initialize_core_modules():
    """
    Initialize all core modules with shared config.
    
    Returns:
        tuple: (config, authority_mapper, priority_scorer)
    
    Example:
        >>> from core import initialize_core_modules
        >>> config, mapper, scorer = initialize_core_modules()
        >>> 
        >>> # Use them
        >>> routing = mapper.route_complaint(
        ...     category="academic",
        ...     user_department="CSE",
        ...     complaint_text="Professor not teaching well"
        ... )
        >>> priority = scorer.calculate_priority(
        ...     complaint="Urgent lab equipment broken",
        ...     upvotes=5,
        ...     downvotes=1
        ... )
    """
    config = get_config()
    mapper = AuthorityMapper(config)
    scorer = PriorityScorer(config)
    return config, mapper, scorer


# Add to __all__
__all__.append("initialize_core_modules")


# =================== CONFIGURATION VALIDATION ===================

def check_configuration():
    """
    Validate core module configuration on import.
    
    Checks:
    - Groq API key (if Groq is enabled)
    - Firebase credentials (file path OR JSON env var)
    - Redis URL (for Celery task queue)
    
    Warns if critical settings are missing but doesn't block execution.
    
    Returns:
        bool: True if configuration is valid, False if issues found
    
    Example:
        >>> from core import check_configuration
        >>> if check_configuration():
        ...     print("All good!")
        ... else:
        ...     print("Check your .env file")
    """
    try:
        config = get_config()
        issues = []
        warnings = []
        
        # =================== CHECK GROQ API KEY ===================
        if config.use_groq and not config.groq_api_key:
            issues.append("⚠️  GROQ_API_KEY not configured")
            warnings.append("   → Get your FREE key: https://console.groq.com")
            warnings.append("   → Falling back to rule-based processing")
        
        # =================== CHECK FIREBASE CREDENTIALS ===================
        import os
        
        has_file = os.path.exists(config.firebase_credentials_path)
        has_json = bool(config.firebase_credentials_json)
        
        if not has_file and not has_json:
            issues.append("⚠️  Firebase credentials not found")
            warnings.append(f"   → Expected file: {config.firebase_credentials_path}")
            warnings.append("   → OR set FIREBASE_CREDENTIALS_JSON environment variable")
            warnings.append("   → Database operations will fail without credentials")
        elif has_json:
            # Validate JSON format
            try:
                import json
                json.loads(config.firebase_credentials_json)
            except json.JSONDecodeError:
                issues.append("⚠️  FIREBASE_CREDENTIALS_JSON is invalid JSON")
                warnings.append("   → Check your environment variable format")
        
        # =================== CHECK REDIS (CELERY REQUIREMENT) ===================
        if not config.redis_url:
            issues.append("⚠️  REDIS_URL not configured")
            warnings.append("   → Background task processing requires Redis")
            warnings.append("   → Set REDIS_URL in your .env file")
            warnings.append("   → Local: redis://localhost:6379/0")
            warnings.append("   → Railway: Will be provided automatically")
        
        # =================== CHECK PRODUCTION SETTINGS ===================
        if config.environment == 'production':
            if config.secret_key == 'dev-secret-key-CHANGE-IN-PRODUCTION':
                issues.append("🚨 CRITICAL: Using default SECRET_KEY in production")
                warnings.append("   → Set a secure SECRET_KEY environment variable immediately")
                warnings.append("   → Generate one: python -c 'import secrets; print(secrets.token_hex(32))'")
            
            if '*' in config.cors_origins:
                issues.append("⚠️  CORS allows all origins in production")
                warnings.append("   → Update CORS settings for security")
                warnings.append("   → Set specific frontend URLs only")
        
        # =================== PRINT ISSUES IF ANY ===================
        if issues:
            print("\n" + "="*70)
            print("🔧 CampusVoice Core Module Configuration Issues:")
            print("="*70)
            for issue in issues:
                print(f"  {issue}")
            if warnings:
                print()
                for warning in warnings:
                    print(f"  {warning}")
            print("="*70 + "\n")
            return False
        
        # =================== ALL GOOD ===================
        if config.debug_mode:
            print("✅ Core module configuration validated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        import traceback
        if config.debug_mode:
            traceback.print_exc()
        return False


# =================== UTILITY FUNCTIONS ===================

def get_version():
    """
    Get the current version of the core module.
    
    Returns:
        str: Version string (e.g., "5.0.0")
    """
    return __version__


def get_module_info():
    """
    Get detailed information about the core module.
    
    Returns:
        dict: Module information including version, author, components
    
    Example:
        >>> from core import get_module_info
        >>> info = get_module_info()
        >>> print(f"Version: {info['version']}")
        Version: 5.0.0
    """
    return {
        "name": "CampusVoice Core",
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "components": {
            "Config": "Application configuration and constants",
            "AuthorityMapper": "Smart complaint routing with bypass logic",
            "PriorityScorer": "Multi-factor priority calculation"
        },
        "features": [
            "Async-ready design (Celery-compatible)",
            "Production deployment support",
            "Dual Firebase credential modes",
            "Redis & Celery integration",
            "Intelligent complaint routing",
            "Dynamic priority scoring",
            "Time-based escalation",
            "Capped voting system"
        ]
    }


# Add utility functions to __all__
__all__.extend(["check_configuration", "get_version", "get_module_info"])


# =================== AUTO-CHECK ON IMPORT (OPTIONAL) ===================

# Uncomment the line below if you want automatic configuration check on import
# Useful for development, but may be too verbose for production
# check_configuration()


# =================== MODULE INITIALIZATION MESSAGE ===================

def _print_welcome_message():
    """Print welcome message (only in debug mode)"""
    try:
        config = get_config()
        if config.debug_mode:
            print(f"🚀 CampusVoice Core Module v{__version__} loaded")
            print(f"   Environment: {config.environment}")
            print(f"   LLM: {'Groq (' + config.groq_model + ')' if config.use_groq else 'Rule-based'}")
    except:
        pass  # Silently fail if config not ready


# Print welcome message (only in debug mode)
# _print_welcome_message()  # Uncomment to enable
