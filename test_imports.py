"""Test script to debug imports."""
import os
import sys

print("Python path:")
print("\n".join(sys.path))

print("\nTrying to import schwab_trader...")
try:
    import schwab_trader
    print(f"schwab_trader.__file__: {schwab_trader.__file__}")
    print(f"schwab_trader.__path__: {schwab_trader.__path__}")
    print(f"schwab_trader.__package__: {schwab_trader.__package__}")
    
    print("\nTrying to import create_app...")
    try:
        from schwab_trader import create_app
        print("Successfully imported create_app")
    except ImportError as e:
        print(f"Failed to import create_app: {e}")
except ImportError as e:
    print(f"Failed to import schwab_trader: {e}")

print("\nListing directory contents:")
print(os.listdir(".")) 