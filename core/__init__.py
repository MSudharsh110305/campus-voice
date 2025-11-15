"""
Core module for CampusVoice AI
Complaint Processing & Routing System

This module provides the core functionality for intelligent complaint routing,
priority scoring, and authority mapping with pseudo-anonymity support.

Version: 4.0.0 - Production Ready

Main Components:
- Config: Application configuration and constants
- AuthorityMapper: Smart complaint routing with hierarchy and bypass logic
- PriorityScorer: Multi-factor priority calculation with voting and aging

Usage:
    from core import Config, AuthorityMapper, PriorityScorer
    
    config = Config()
    mapper = AuthorityMapper(config)
    scorer = PriorityScorer(config)
"""

from .config import Config, get_config
from .authority_mapper import AuthorityMapper
from .priority_scorer import PriorityScorer

__version__ = "4.0.0"
__author__ = "CampusVoice Team"
__license__ = "MIT"

__all__ = [
    "Config",
    "get_config",
    "AuthorityMapper",
    "PriorityScorer",
    "__version__"
]


# Convenience function for quick setup
def initialize_core_modules():
    """
    Initialize all core modules with shared config.
    
    Returns:
        tuple: (config, authority_mapper, priority_scorer)
    
    Example:
        >>> from core import initialize_core_modules
        >>> config, mapper, scorer = initialize_core_modules()
    """
    config = get_config()
    mapper = AuthorityMapper(config)
    scorer = PriorityScorer(config)
    
    return config, mapper, scorer


# Add to __all__
__all__.append("initialize_core_modules")


# Module-level configuration check
def check_configuration():
    """
    Validate core module configuration on import.
    Warns if critical settings are missing.
    
    Returns:
        bool: True if configuration is valid
    """
    try:
        config = get_config()
        
        issues = []
        
        # Check Groq API key if enabled
        if config.use_groq and not config.groq_api_key:
            issues.append("⚠️  GROQ_API_KEY not configured")
        
        # Check Firebase credentials
        import os
        if not os.path.exists(config.firebase_credentials_path):
            issues.append(f"⚠️  Firebase credentials not found: {config.firebase_credentials_path}")
        
        if issues:
            print("\n" + "="*60)
            print("🔧 CampusVoice Core Module Configuration Issues:")
            for issue in issues:
                print(f"   {issue}")
            print("="*60 + "\n")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        return False


# Optional: Run configuration check on import (can be disabled)
# Uncomment the line below if you want auto-check on import
# check_configuration()
