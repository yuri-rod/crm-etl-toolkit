#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRM ETL Test Runner
===================

Test runner script to ensure green tests before deployment.
Provides comprehensive test execution with clear reporting.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --quick           # Run only quick tests
    python run_tests.py --smoke           # Run only smoke tests
    python run_tests.py --backend         # Run only backend tests
    python run_tests.py --etl             # Run only ETL tests
    python run_tests.py --frontend        # Run only frontend tests

Developed for CRM ETL
"""

import sys
import subprocess
import argparse
import time
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json


class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


class TestRunner:
    """Comprehensive test runner for CRM ETL system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tests_dir = self.project_root / "tests"
        self.results = {}
        self.total_start_time = time.time()
        
    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{Color.CYAN}{Color.BOLD}{'='*60}{Color.END}")
        print(f"{Color.CYAN}{Color.BOLD}{title:^60}{Color.END}")
        print(f"{Color.CYAN}{Color.BOLD}{'='*60}{Color.END}\n")
        
    def print_step(self, step: str):
        """Print formatted step"""
        print(f"{Color.BLUE}🔧 {step}{Color.END}")
        
    def print_success(self, message: str):
        """Print success message"""
        print(f"{Color.GREEN}✅ {message}{Color.END}")
        
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Color.YELLOW}⚠️ {message}{Color.END}")
        
    def print_error(self, message: str):
        """Print error message"""
        print(f"{Color.RED}❌ {message}{Color.END}")
        
    def check_dependencies(self) -> bool:
        """Check if required test dependencies are installed"""
        self.print_step("Checking test dependencies...")
        
        required_packages = [
            "pytest",
            "pytest-asyncio", 
            "httpx",
            "pandas",
            "numpy"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.print_error(f"Missing required packages: {', '.join(missing_packages)}")
            print(f"\nInstall with: {Color.CYAN}pip install {' '.join(missing_packages)}{Color.END}")
            return False
        
        self.print_success("All required dependencies are installed")
        return True
    
    def check_optional_dependencies(self):
        """Check optional dependencies and warn if missing"""
        optional_packages = {
            "playwright": "Frontend testing with browser automation",
            "pytest_playwright": "Playwright pytest integration", 
            "pytest_cov": "Code coverage reporting",
            "pytest_html": "HTML test reports"
        }
        
        missing_optional = []
        
        for package, description in optional_packages.items():
            try:
                __import__(package)
            except ImportError:
                missing_optional.append((package, description))
        
        if missing_optional:
            self.print_warning("Optional dependencies missing:")
            for package, desc in missing_optional:
                print(f"  • {package}: {desc}")
            print(f"\nInstall with: {Color.CYAN}pip install -r tests/requirements-test.txt{Color.END}")
    
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """Run command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out after 5 minutes"
        except Exception as e:
            return 1, "", str(e)
    
    def run_pytest(self, test_pattern: str, test_name: str, extra_args: List[str] = None) -> Dict:
        """Run pytest with specific pattern and return results"""
        start_time = time.time()
        
        cmd = ["python", "-m", "pytest", test_pattern, "-v", "--tb=short"]
        if extra_args:
            cmd.extend(extra_args)
        
        self.print_step(f"Running {test_name}...")
        print(f"Command: {Color.CYAN}{' '.join(cmd)}{Color.END}")
        
        exit_code, stdout, stderr = self.run_command(cmd)
        duration = time.time() - start_time
        
        # Parse pytest output for test counts
        passed = stdout.count(" PASSED")
        failed = stdout.count(" FAILED") 
        skipped = stdout.count(" SKIPPED")
        errors = stdout.count(" ERROR")
        
        result = {
            "name": test_name,
            "exit_code": exit_code,
            "duration": duration,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "stdout": stdout,
            "stderr": stderr
        }
        
        if exit_code == 0:
            self.print_success(f"{test_name} completed successfully ({duration:.1f}s)")
            if passed > 0:
                print(f"  📊 {passed} passed, {skipped} skipped")
        else:
            self.print_error(f"{test_name} failed ({duration:.1f}s)")
            print(f"  📊 {passed} passed, {failed} failed, {skipped} skipped, {errors} errors")
            
            # Show first few lines of error output
            if stderr:
                print(f"\n{Color.RED}Error output:{Color.END}")
                print(stderr[:500] + "..." if len(stderr) > 500 else stderr)
        
        self.results[test_name.lower().replace(" ", "_")] = result
        return result
    
    def run_smoke_tests(self):
        """Run smoke tests - quick validation of core functionality"""
        self.print_header("SMOKE TESTS")
        
        # Backend API smoke test
        if (self.tests_dir / "test_backend_endpoints.py").exists():
            self.run_pytest(
                "tests/test_backend_endpoints.py::test_server_availability",
                "Backend Smoke Test"
            )
        
        # ETL pipeline basic test
        if (self.tests_dir / "test_etl_pipeline.py").exists():
            self.run_pytest(
                "tests/test_etl_pipeline.py::TestETLPipeline::test_csv_extraction",
                "ETL Smoke Test"
            )
        
        # Frontend basic test  
        if (self.tests_dir / "test_frontend_links.py").exists():
            self.run_pytest(
                "tests/test_frontend_links.py::TestFrontendBasic",
                "Frontend Smoke Test"
            )
    
    def run_backend_tests(self):
        """Run backend API endpoint tests"""
        self.print_header("BACKEND API TESTS")
        
        if (self.tests_dir / "test_backend_endpoints.py").exists():
            self.run_pytest(
                "tests/test_backend_endpoints.py",
                "Backend API Tests",
                ["--maxfail=3"]  # Stop after 3 failures
            )
        else:
            self.print_warning("Backend test file not found")
    
    def run_etl_tests(self):
        """Run ETL pipeline tests"""
        self.print_header("ETL PIPELINE TESTS")
        
        if (self.tests_dir / "test_etl_pipeline.py").exists():
            self.run_pytest(
                "tests/test_etl_pipeline.py",
                "ETL Pipeline Tests"
            )
        else:
            self.print_warning("ETL test file not found")
    
    def run_frontend_tests(self):
        """Run frontend tests"""
        self.print_header("FRONTEND TESTS")
        
        if (self.tests_dir / "test_frontend_links.py").exists():
            # Run basic tests first (no Playwright required)
            self.run_pytest(
                "tests/test_frontend_links.py::TestFrontendBasic",
                "Frontend Basic Tests"
            )
            
            # Try Playwright tests if available
            try:
                import playwright
                self.run_pytest(
                    "tests/test_frontend_links.py::TestFrontendLinks",
                    "Frontend Playwright Tests",
                    ["--maxfail=5"]  # More lenient for browser tests
                )
            except ImportError:
                self.print_warning("Playwright not available, skipping browser tests")
        else:
            self.print_warning("Frontend test file not found")
    
    def run_unit_tests(self):
        """Run existing unit tests"""
        self.print_header("UNIT TESTS")
        
        if (self.tests_dir / "test_extractors.py").exists():
            self.run_pytest(
                "tests/test_extractors.py",
                "Extractor Unit Tests"
            )
        else:
            self.print_warning("Unit test file not found")
    
    def run_integration_tests(self):
        """Run integration tests"""
        self.print_header("INTEGRATION TESTS")
        
        # Run tests marked as integration
        self.run_pytest(
            "tests/ -m integration",
            "Integration Tests",
            ["--tb=line"]
        )
    
    def run_all_tests(self):
        """Run complete test suite"""
        self.print_header("COMPLETE TEST SUITE")
        
        self.run_pytest(
            "tests/",
            "All Tests",
            ["--maxfail=10", "--tb=short"]
        )
    
    def check_server_status(self):
        """Check if backend server is running"""
        self.print_step("Checking backend server status...")
        
        try:
            import httpx
            response = httpx.get("http://localhost:8000", timeout=2.0)
            if response.status_code < 400:
                self.print_success("Backend server is running")
                return True
        except Exception:
            pass
        
        self.print_warning("Backend server not running - API tests may fail")
        print(f"Start server with: {Color.CYAN}python BETA/backend/api_server.py{Color.END}")
        return False
    
    def generate_report(self):
        """Generate comprehensive test report"""
        total_duration = time.time() - self.total_start_time
        
        self.print_header("TEST SUMMARY REPORT")
        
        total_passed = sum(r.get("passed", 0) for r in self.results.values())
        total_failed = sum(r.get("failed", 0) for r in self.results.values())
        total_skipped = sum(r.get("skipped", 0) for r in self.results.values())
        total_errors = sum(r.get("errors", 0) for r in self.results.values())
        
        print(f"📊 {Color.BOLD}Overall Results:{Color.END}")
        print(f"   • Total Tests: {total_passed + total_failed}")
        print(f"   • {Color.GREEN}Passed: {total_passed}{Color.END}")
        print(f"   • {Color.RED}Failed: {total_failed}{Color.END}")
        print(f"   • {Color.YELLOW}Skipped: {total_skipped}{Color.END}")
        print(f"   • {Color.RED}Errors: {total_errors}{Color.END}")
        print(f"   • ⏱️ Total Time: {total_duration:.1f}s")
        
        print(f"\n📋 {Color.BOLD}Test Suite Details:{Color.END}")
        for test_name, result in self.results.items():
            status = "✅ PASS" if result["exit_code"] == 0 else "❌ FAIL"
            duration = result["duration"]
            passed = result.get("passed", 0)
            failed = result.get("failed", 0)
            
            print(f"   • {status} {result['name']} ({duration:.1f}s) - {passed}✅ {failed}❌")
        
        # Determine overall status
        all_critical_passed = True
        critical_tests = ["etl_pipeline_tests", "backend_api_tests"]
        
        for test in critical_tests:
            if test in self.results and self.results[test]["exit_code"] != 0:
                all_critical_passed = False
                break
        
        print(f"\n🎯 {Color.BOLD}Deployment Status:{Color.END}")
        if total_failed == 0 and total_errors == 0:
            print(f"   {Color.GREEN}🚀 ALL TESTS PASS - READY FOR DEPLOYMENT{Color.END}")
            return 0
        elif all_critical_passed:
            print(f"   {Color.YELLOW}⚠️ CRITICAL TESTS PASS - DEPLOYMENT WITH CAUTION{Color.END}")
            return 0
        else:
            print(f"   {Color.RED}🛑 CRITICAL TESTS FAIL - DO NOT DEPLOY{Color.END}")
            return 1
    
    def save_results_json(self):
        """Save test results to JSON file"""
        results_file = self.project_root / "test-results.json"
        
        summary = {
            "timestamp": time.time(),
            "total_duration": time.time() - self.total_start_time,
            "results": self.results,
            "summary": {
                "total_passed": sum(r.get("passed", 0) for r in self.results.values()),
                "total_failed": sum(r.get("failed", 0) for r in self.results.values()),
                "total_skipped": sum(r.get("skipped", 0) for r in self.results.values()),
                "total_errors": sum(r.get("errors", 0) for r in self.results.values())
            }
        }
        
        try:
            with open(results_file, 'w') as f:
                json.dump(summary, f, indent=2)
            self.print_success(f"Test results saved to {results_file}")
        except Exception as e:
            self.print_warning(f"Could not save test results: {e}")


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="CRM ETL Test Runner")
    parser.add_argument("--quick", action="store_true", help="Run only quick tests")
    parser.add_argument("--smoke", action="store_true", help="Run only smoke tests")
    parser.add_argument("--backend", action="store_true", help="Run only backend tests")
    parser.add_argument("--etl", action="store_true", help="Run only ETL tests")
    parser.add_argument("--frontend", action="store_true", help="Run only frontend tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--no-deps-check", action="store_true", help="Skip dependency check")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Print welcome banner
    runner.print_header("CRM ETL TEST RUNNER")
    print(f"{Color.CYAN}Testing environment for CRM ETL{Color.END}")
    print(f"{Color.CYAN}Ensuring code quality before deployment{Color.END}\n")
    
    # Check dependencies unless skipped
    if not args.no_deps_check:
        if not runner.check_dependencies():
            return 1
        runner.check_optional_dependencies()
    
    # Check server status
    runner.check_server_status()
    
    try:
        # Run tests based on arguments
        if args.smoke:
            runner.run_smoke_tests()
        elif args.backend:
            runner.run_backend_tests()
        elif args.etl:
            runner.run_etl_tests()
        elif args.frontend:
            runner.run_frontend_tests()
        elif args.unit:
            runner.run_unit_tests()
        elif args.integration:
            runner.run_integration_tests()
        elif args.all:
            runner.run_all_tests()
        elif args.quick:
            runner.run_smoke_tests()
            runner.run_etl_tests()
        else:
            # Default: run core test suite
            runner.run_smoke_tests()
            runner.run_etl_tests()
            runner.run_backend_tests()
            runner.run_unit_tests()
        
        # Generate final report
        exit_code = runner.generate_report()
        runner.save_results_json()
        
        return exit_code
        
    except KeyboardInterrupt:
        runner.print_error("Tests interrupted by user")
        return 1
    except Exception as e:
        runner.print_error(f"Test runner error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
