#!/usr/bin/env python3
"""
Test runner script for Grantha project.

This script provides different test execution modes:
- Unit tests only
- Integration tests only  
- End-to-end tests only
- Performance tests
- All tests
- Coverage report generation
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description="", exit_on_failure=True):
    """Run a command and handle the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description or cmd}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print(f"\n❌ Command failed: {cmd}")
        if exit_on_failure:
            sys.exit(result.returncode)
        return False
    else:
        print(f"\n✅ Command succeeded: {description or cmd}")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run Grantha tests")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "e2e", "performance", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--parallel",
        action="store_true", 
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Include slow tests"
    )
    parser.add_argument(
        "--network",
        action="store_true",
        help="Include network tests"
    )
    
    args = parser.parse_args()
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        pytest_cmd.append("-v")
    
    if args.fail_fast:
        pytest_cmd.append("-x")
    
    if args.parallel:
        pytest_cmd.extend(["-n", "auto"])
    
    if args.coverage:
        pytest_cmd.extend([
            "--cov=api",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add test markers
    markers = []
    if not args.slow:
        markers.append("not slow")
    if not args.network:
        markers.append("not network")
    
    if markers:
        pytest_cmd.extend(["-m", " and ".join(markers)])
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "TESTING": "1",
        "GOOGLE_API_KEY": "test_key",
        "OPENAI_API_KEY": "test_key", 
        "OPENROUTER_API_KEY": "test_key",
    })
    
    # Run different test types
    success = True
    
    if args.type == "unit":
        cmd = " ".join(pytest_cmd + ["tests/unit"])
        success = run_command(cmd, "Unit Tests", exit_on_failure=False)
        
    elif args.type == "integration":
        cmd = " ".join(pytest_cmd + ["tests/integration"])
        success = run_command(cmd, "Integration Tests", exit_on_failure=False)
        
    elif args.type == "e2e":
        cmd = " ".join(pytest_cmd + ["tests/e2e", "--timeout=300"])
        success = run_command(cmd, "End-to-End Tests", exit_on_failure=False)
        
    elif args.type == "performance":
        cmd = " ".join(pytest_cmd + ["tests/performance", "-m", "performance"])
        success = run_command(cmd, "Performance Tests", exit_on_failure=False)
        
    elif args.type == "all":
        # Run all test types in sequence
        test_types = [
            ("tests/unit", "Unit Tests"),
            ("tests/integration", "Integration Tests"),  
            ("tests/e2e --timeout=300", "End-to-End Tests"),
            ("tests/performance -m performance", "Performance Tests")
        ]
        
        for test_path, description in test_types:
            cmd = " ".join(pytest_cmd + test_path.split())
            if not run_command(cmd, description, exit_on_failure=False):
                success = False
                if args.fail_fast:
                    break
    
    # Generate coverage report if requested
    if args.coverage and success:
        print("\n" + "="*60)
        print("Coverage Report")
        print("="*60)
        
        # Open HTML coverage report
        coverage_html = project_root / "htmlcov" / "index.html"
        if coverage_html.exists():
            print(f"📊 Coverage report available at: {coverage_html}")
            
            # Try to open in browser
            try:
                import webbrowser
                webbrowser.open(f"file://{coverage_html.absolute()}")
                print("📖 Coverage report opened in browser")
            except Exception:
                print("💡 Open the coverage report manually in your browser")
    
    # Summary
    print("\n" + "="*60)
    print("Test Execution Summary")
    print("="*60)
    
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()