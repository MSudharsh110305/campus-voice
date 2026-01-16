"""
CampusVoice v5.0.0 - System Test Suite
Comprehensive testing before deployment
"""

import os
import sys
from datetime import datetime, timezone
from colorama import init, Fore, Style
import json

# Initialize colorama for colored output
init(autoreset=True)

def print_header(text):
    """Print colored header."""
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}{text.center(70)}")
    print(f"{Fore.CYAN}{'=' * 70}\n")

def print_success(text):
    """Print success message."""
    print(f"{Fore.GREEN}✅ {text}")

def print_error(text):
    """Print error message."""
    print(f"{Fore.RED}❌ {text}")

def print_warning(text):
    """Print warning message."""
    print(f"{Fore.YELLOW}⚠️  {text}")

def print_info(text):
    """Print info message."""
    print(f"{Fore.BLUE}ℹ️  {text}")

def test_imports():
    """Test all required imports."""
    print_header("TESTING IMPORTS")
    
    required_modules = [
        ('flask', 'Flask'),
        ('flask_cors', 'Flask-CORS'),
        ('firebase_admin', 'Firebase Admin SDK'),
        ('groq', 'Groq SDK'),
        ('python-dotenv', 'Python Dotenv'),
        ('PIL', 'Pillow (Image Processing)'),
        ('colorama', 'Colorama (Terminal Colors)'),
    ]
    
    all_passed = True
    
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print_success(f"{display_name}: Installed")
        except ImportError:
            print_error(f"{display_name}: NOT INSTALLED")
            print(f"   Install with: pip install {module_name}")
            all_passed = False
    
    return all_passed

def test_environment_variables():
    """Test required environment variables."""
    print_header("TESTING ENVIRONMENT VARIABLES")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'GROQ_API_KEY': 'Groq API Key (for LLM)',
        'FIREBASE_CREDENTIALS_PATH': 'Firebase Credentials Path',
    }
    
    optional_vars = {
        'API_HOST': 'API Host (default: 0.0.0.0)',
        'API_PORT': 'API Port (default: 5000)',
        'DEBUG': 'Debug Mode (default: false)',
        'WORKERS': 'Worker Processes (default: 4)',
    }
    
    all_passed = True
    
    print("📋 Required Variables:")
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            print_success(f"{var}: Configured")
            print(f"   {desc}")
        else:
            print_error(f"{var}: NOT SET")
            print(f"   {desc}")
            all_passed = False
    
    print("\n📋 Optional Variables:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            print_success(f"{var}: {value}")
        else:
            print_info(f"{var}: Using default")
        print(f"   {desc}")
    
    return all_passed

def test_file_structure():
    """Test project file structure."""
    print_header("TESTING FILE STRUCTURE")
    
    required_files = [
        'main.py',
        'requirements.txt',
        '.env',
    ]
    
    required_dirs = [
        'core',
        'api',
        'logs',
    ]
    
    core_files = [
        'core/__init__.py',
        'core/config.py',
        'core/authority_mapper.py',
        'core/priority_scorer.py',
    ]
    
    api_files = [
        'api/__init__.py',
        'api/routes.py',
        'api/models.py',
        'api/validators.py',
        'api/firebase_service.py',
        'api/intelligent_llm_engine.py',
        'api/complaint_processor.py',
        'api/response_formatter.py',
        'api/api_config.py',
    ]
    
    all_passed = True
    
    print("📁 Root Files:")
    for file in required_files:
        if os.path.exists(file):
            print_success(f"{file}")
        else:
            print_error(f"{file}: MISSING")
            all_passed = False
    
    print("\n📁 Directories:")
    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print_success(f"{dir_name}/")
        else:
            print_error(f"{dir_name}/: MISSING")
            all_passed = False
    
    print("\n📁 Core Module:")
    for file in core_files:
        if os.path.exists(file):
            print_success(f"{file}")
        else:
            print_error(f"{file}: MISSING")
            all_passed = False
    
    print("\n📁 API Module:")
    for file in api_files:
        if os.path.exists(file):
            print_success(f"{file}")
        else:
            print_error(f"{file}: MISSING")
            all_passed = False
    
    return all_passed

def test_firebase_credentials():
    """Test Firebase credentials."""
    print_header("TESTING FIREBASE CREDENTIALS")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-key.json')
    
    if not os.path.exists(creds_path):
        print_error(f"Firebase credentials file not found: {creds_path}")
        print("   Make sure firebase-key.json exists in the project root")
        return False
    
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds]
        
        if missing_fields:
            print_error(f"Missing fields in Firebase credentials: {', '.join(missing_fields)}")
            return False
        
        print_success(f"Firebase credentials file: {creds_path}")
        print(f"   Project ID: {creds.get('project_id')}")
        print(f"   Client Email: {creds.get('client_email')}")
        return True
        
    except json.JSONDecodeError:
        print_error(f"Invalid JSON in Firebase credentials file")
        return False
    except Exception as e:
        print_error(f"Error reading Firebase credentials: {str(e)}")
        return False

def test_core_modules():
    """Test core modules can be imported."""
    print_header("TESTING CORE MODULES")
    
    modules = [
        ('core.config', 'Configuration Module'),
        ('core.authority_mapper', 'Authority Mapper'),
        ('core.priority_scorer', 'Priority Scorer'),
    ]
    
    all_passed = True
    
    for module_path, display_name in modules:
        try:
            __import__(module_path)
            print_success(f"{display_name}")
        except Exception as e:
            print_error(f"{display_name}: FAILED")
            print(f"   Error: {str(e)}")
            all_passed = False
    
    return all_passed

def test_api_modules():
    """Test API modules can be imported."""
    print_header("TESTING API MODULES")
    
    modules = [
        ('api.models', 'Data Models'),
        ('api.validators', 'Validators'),
        ('api.firebase_service', 'Firebase Service'),
        ('api.intelligent_llm_engine', 'LLM Engine'),
        ('api.complaint_processor', 'Complaint Processor'),
        ('api.response_formatter', 'Response Formatter'),
        ('api.routes', 'API Routes'),
        ('api.api_config', 'API Configuration'),
    ]
    
    all_passed = True
    
    for module_path, display_name in modules:
        try:
            __import__(module_path)
            print_success(f"{display_name}")
        except Exception as e:
            print_error(f"{display_name}: FAILED")
            print(f"   Error: {str(e)}")
            all_passed = False
    
    return all_passed

def test_flask_app():
    """Test Flask app can be created."""
    print_header("TESTING FLASK APP")
    
    try:
        # Temporarily disable Firebase for quick test
        os.environ['SKIP_FIREBASE_INIT'] = 'true'
        
        from main import create_app
        app = create_app()
        
        print_success("Flask app created successfully")
        print(f"   Version: 5.0.0")
        print(f"   API Prefix: {app.config.get('API_PREFIX', '/api/v1')}")
        
        # Test routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        print(f"\n📍 Registered Routes ({len(routes)} total):")
        for route in sorted(routes)[:10]:  # Show first 10
            print(f"   • {route}")
        if len(routes) > 10:
            print(f"   ... and {len(routes) - 10} more")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to create Flask app")
        print(f"   Error: {str(e)}")
        import traceback
        print(f"\n{traceback.format_exc()}")
        return False

def test_timezone_awareness():
    """Test timezone-aware datetime handling."""
    print_header("TESTING TIMEZONE AWARENESS")
    
    try:
        # Test timezone-aware datetime
        now = datetime.now(timezone.utc)
        print_success(f"Timezone-aware datetime: {now.isoformat()}")
        
        # Verify it's actually timezone-aware
        if now.tzinfo is not None and now.tzinfo.utcoffset(now) is not None:
            print_success("Datetime is timezone-aware (UTC)")
            return True
        else:
            print_error("Datetime is NOT timezone-aware!")
            return False
            
    except Exception as e:
        print_error(f"Timezone test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and return overall status."""
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║        CAMPUSVOICE v5.0.0 - SYSTEM TEST SUITE                    ║
║                                                                   ║
║        Testing all components before deployment...                ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")
    
    results = {
        'imports': test_imports(),
        'environment': test_environment_variables(),
        'file_structure': test_file_structure(),
        'firebase_creds': test_firebase_credentials(),
        'core_modules': test_core_modules(),
        'api_modules': test_api_modules(),
        'timezone': test_timezone_awareness(),
        'flask_app': test_flask_app(),
    }
    
    print_header("TEST RESULTS SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    for test_name, result in results.items():
        display_name = test_name.replace('_', ' ').title()
        if result:
            print_success(f"{display_name}")
        else:
            print_error(f"{display_name}")
    
    print(f"\n{'=' * 70}")
    print(f"Total Tests: {total_tests}")
    print(f"{Fore.GREEN}Passed: {passed_tests}")
    print(f"{Fore.RED}Failed: {failed_tests}")
    print(f"{'=' * 70}\n")
    
    if failed_tests == 0:
        print(f"{Fore.GREEN}{Style.BRIGHT}")
        print("🎉 ALL TESTS PASSED! System is ready to run!")
        print(f"{Style.RESET_ALL}")
        print("\nNext steps:")
        print("  1. Run development server: python main.py")
        print("  2. Or production server: gunicorn -c gunicorn_config.py main:app")
        return True
    else:
        print(f"{Fore.RED}{Style.BRIGHT}")
        print("❌ SOME TESTS FAILED! Please fix the issues before running.")
        print(f"{Style.RESET_ALL}")
        return False

if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error during testing: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
