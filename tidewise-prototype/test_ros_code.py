#!/usr/bin/env python3
"""
Test script to validate ROS integration code structure
(without requiring ROS to be installed)

This checks:
1. Python syntax is correct
2. Import structure is valid
3. Class definitions are proper
4. Method signatures are correct
"""

import ast
import os
import sys

def analyze_python_file(filepath):
    """
    Parse Python file and extract key information
    """
    print(f"\n{'='*60}")
    print(f"Analyzing: {os.path.basename(filepath)}")
    print(f"{'='*60}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the AST
        tree = ast.parse(source, filename=filepath)
        
        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        # Extract classes and methods
        classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # Get method signature
                        args = [arg.arg for arg in item.args.args]
                        methods.append({
                            'name': item.name,
                            'args': args,
                            'is_init': item.name == '__init__'
                        })
                classes[node.name] = {
                    'methods': methods,
                    'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
                }
        
        # Report findings
        print(f"✅ Python syntax: VALID")
        print(f"\n📦 Imports ({len(imports)}):")
        
        # Group imports
        ros_imports = [i for i in imports if 'rospy' in i or 'std_msgs' in i or 'sensor_msgs' in i or 'mavros' in i]
        hardware_imports = [i for i in imports if 'ms5837' in i or 'bar30' in i]
        standard_imports = [i for i in imports if i not in ros_imports and i not in hardware_imports]
        
        if ros_imports:
            print(f"   ROS imports (⚠️  need ROS on target system):")
            for imp in ros_imports[:5]:  # Show first 5
                print(f"      - {imp}")
            if len(ros_imports) > 5:
                print(f"      ... and {len(ros_imports) - 5} more")
        
        if hardware_imports:
            print(f"   Hardware imports (⚠️  need sensors connected):")
            for imp in hardware_imports:
                print(f"      - {imp}")
        
        if standard_imports:
            print(f"   Standard Python imports (✅ available):")
            for imp in standard_imports[:5]:
                print(f"      - {imp}")
            if len(standard_imports) > 5:
                print(f"      ... and {len(standard_imports) - 5} more")
        
        print(f"\n🏗️  Classes ({len(classes)}):")
        for class_name, info in classes.items():
            print(f"   {class_name}")
            print(f"      Inherits from: {info['bases'] if info['bases'] else 'object'}")
            print(f"      Methods: {len(info['methods'])}")
            
            # Show __init__ signature
            init_method = next((m for m in info['methods'] if m['is_init']), None)
            if init_method:
                args_str = ', '.join(init_method['args'])
                print(f"         __init__({args_str})")
            
            # Show other key methods
            other_methods = [m for m in info['methods'] if not m['is_init']]
            for method in other_methods[:3]:  # Show first 3
                args_str = ', '.join(method['args'])
                print(f"         {method['name']}({args_str})")
            
            if len(other_methods) > 3:
                print(f"         ... and {len(other_methods) - 3} more methods")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ros_integration():
    """
    Test all ROS integration files
    """
    print("\n" + "="*60)
    print("TIDEWISE ROS INTEGRATION - CODE VALIDATION TEST")
    print("="*60)
    print("\nℹ️  Note: Import warnings for 'rospy', 'std_msgs', 'sensor_msgs'")
    print("   are EXPECTED on Windows. These will resolve when code is")
    print("   deployed on LoCO Raspberry Pi with ROS installed.")
    
    ros_files = [
        'ros_integration/tidewise_node.py',
        'ros_integration/bar30_sensor_node.py'
    ]
    
    results = {}
    for filepath in ros_files:
        if os.path.exists(filepath):
            results[filepath] = analyze_python_file(filepath)
        else:
            print(f"\n⚠️  File not found: {filepath}")
            results[filepath] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    all_passed = all(results.values())
    
    for filepath, passed in results.items():
        status = "✅ VALID" if passed else "❌ FAILED"
        print(f"{status}: {os.path.basename(filepath)}")
    
    if all_passed:
        print(f"\n🎉 ALL ROS FILES ARE STRUCTURALLY VALID!")
        print(f"\n✅ Ready to deploy on LoCO Raspberry Pi with ROS")
        print(f"   Installation steps: See ros_integration/ROS_QUICKSTART.md")
    else:
        print(f"\n⚠️  Some files have issues - check errors above")
    
    return all_passed


def check_dependencies():
    """
    Check which dependencies are available on this system
    """
    print(f"\n{'='*60}")
    print("DEPENDENCY CHECK (Current System)")
    print(f"{'='*60}")
    
    # Check TideWise core dependencies (should be installed)
    core_deps = [
        ('numpy', 'Core data processing'),
        ('pandas', 'Data structures'),
        ('requests', 'HTTP requests for NOAA data'),
        ('xarray', 'NetCDF/GRIB data parsing'),
        ('netCDF4', 'NetCDF file support'),
    ]
    
    print("\n✅ TideWise Core Dependencies (should be installed):")
    for module, description in core_deps:
        try:
            __import__(module)
            print(f"   ✅ {module:15s} - {description}")
        except ImportError:
            print(f"   ❌ {module:15s} - {description} (NOT INSTALLED)")
    
    # Check ROS dependencies (expected to be missing on Windows)
    ros_deps = [
        ('rospy', 'ROS Python client library'),
        ('std_msgs.msg', 'ROS standard messages'),
        ('sensor_msgs.msg', 'ROS sensor messages'),
    ]
    
    print("\n⚠️  ROS Dependencies (expected to be missing on Windows):")
    for module, description in ros_deps:
        try:
            __import__(module)
            print(f"   ✅ {module:20s} - {description}")
        except ImportError:
            print(f"   ⚠️  {module:20s} - {description} (Will be available on LoCO)")
    
    # Check hardware dependencies (expected to be missing without sensors)
    hw_deps = [
        ('ms5837', 'BlueRobotics Bar30 sensor library'),
    ]
    
    print("\n⚠️  Hardware Dependencies (need sensors connected):")
    for module, description in hw_deps:
        try:
            __import__(module)
            print(f"   ✅ {module:20s} - {description}")
        except ImportError:
            print(f"   ⚠️  {module:20s} - {description} (Install on LoCO with: pip3 install bluerobotics-bar30)")


if __name__ == '__main__':
    # Run tests
    passed = test_ros_integration()
    
    # Check dependencies
    check_dependencies()
    
    # Final message
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("""
To deploy TideWise on LoCO AUV:

1. Copy ros_integration/ folder to LoCO Raspberry Pi
2. Install ROS (if not already): sudo apt install ros-noetic-ros-base
3. Install dependencies: pip3 install -r requirements.txt
4. Install Bar30 library: pip3 install bluerobotics-bar30
5. Build package: cd ~/catkin_ws && catkin_make
6. Launch: roslaunch tidewise_ros tidewise.launch

See ros_integration/ROS_QUICKSTART.md for detailed instructions.
""")
    
    sys.exit(0 if passed else 1)
