"""
Test integration of all three PhishGuard components
Verifies imports, functions, and basic functionality
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all core modules can be imported"""
    print("[TEST] Verifying module imports...")
    
    try:
        import popup_simple
        print("  ✅ popup_simple imported successfully")
    except Exception as e:
        print(f"  ❌ FAILED to import popup_simple: {e}")
        return False
    
    try:
        import proxy_simple
        print("  ✅ proxy_simple imported successfully")
    except Exception as e:
        print(f"  ❌ FAILED to import proxy_simple: {e}")
        return False
    
    try:
        import launcher
        print("  ✅ launcher imported successfully")
    except Exception as e:
        print(f"  ❌ FAILED to import launcher: {e}")
        return False
    
    return True


def test_popup_functions():
    """Test popup functions exist and have correct signatures"""
    print("\n[TEST] Verifying popup functions...")
    
    try:
        from popup_simple import show_popup_gui, PhishGuardPopup, main
        print("  ✅ show_popup_gui function exists")
        print("  ✅ PhishGuardPopup class exists")
        print("  ✅ main() entry point exists")
        
        # Verify show_popup_gui is callable
        if callable(show_popup_gui):
            print("  ✅ show_popup_gui is callable")
        else:
            print("  ❌ show_popup_gui is not callable")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


def test_proxy_functions():
    """Test proxy addon initialization"""
    print("\n[TEST] Verifying proxy addon structure...")
    
    try:
        import proxy_simple
        
        # Check for addons list
        if hasattr(proxy_simple, 'addons'):
            print("  ✅ proxy_simple.addons exists")
        else:
            print("  ❌ proxy_simple.addons not found")
            return False
        
        # Verify addons is not empty
        if proxy_simple.addons:
            print("  ✅ Addon instances created")
        else:
            print("  ❌ No addon instances")
            return False
        
        # Check Addon class
        addon_instance = proxy_simple.addons[0]
        
        if hasattr(addon_instance, 'show_popup_subprocess'):
            print("  ✅ show_popup_subprocess method exists")
        else:
            print("  ❌ show_popup_subprocess method not found")
            return False
        
        if hasattr(addon_instance, 'normalize_domain'):
            print("  ✅ normalize_domain method exists")
        else:
            print("  ❌ normalize_domain method not found")
            return False
        
        if hasattr(addon_instance, 'popup_shown_domains'):
            print("  ✅ Domain-level caching initialized")
        else:
            print("  ❌ Domain-level caching not found")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_launcher_functions():
    """Test launcher functions exist"""
    print("\n[TEST] Verifying launcher functions...")
    
    try:
        import launcher
        
        required_functions = [
            'start_proxy',
            'start_chrome',
            'start_analyzer',
            'wait_for_proxy_ready',
            'is_port_ready',
            'get_chrome_executable',
            'main'
        ]
        
        for func_name in required_functions:
            if hasattr(launcher, func_name):
                print(f"  ✅ {func_name} exists")
            else:
                print(f"  ❌ {func_name} not found")
                return False
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("PhishGuard Integration Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Module Imports", test_imports()))
    results.append(("Popup Functions", test_popup_functions()))
    results.append(("Proxy Functions", test_proxy_functions()))
    results.append(("Launcher Functions", test_launcher_functions()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
