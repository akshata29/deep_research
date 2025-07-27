#!/usr/bin/env python3
"""
Quick status check for Deep Research application
Shows the current development status of all components
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return Path(file_path).exists()

def check_directory_exists(dir_path: str) -> bool:
    """Check if a directory exists"""
    return Path(dir_path).exists() and Path(dir_path).is_dir()

def get_file_count(directory: str, pattern: str = "*") -> int:
    """Count files in a directory matching a pattern"""
    if not Path(directory).exists():
        return 0
    return len(list(Path(directory).glob(pattern)))

def format_status(status: bool) -> str:
    """Format status with colors"""
    if status:
        return f"{Colors.GREEN}✓{Colors.END}"
    else:
        return f"{Colors.RED}✗{Colors.END}"

def format_partial(completed: int, total: int) -> str:
    """Format partial completion status"""
    if completed == total:
        return f"{Colors.GREEN}✓ {completed}/{total}{Colors.END}"
    elif completed > 0:
        return f"{Colors.YELLOW}◐ {completed}/{total}{Colors.END}"
    else:
        return f"{Colors.RED}✗ {completed}/{total}{Colors.END}"

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BLUE}{'-'*len(title)}{Colors.END}")

def check_backend_status() -> Dict:
    """Check backend development status"""
    backend_path = Path("backend")
    
    # Core files
    core_files = [
        "app/main.py",
        "app/core/config.py", 
        "app/core/azure_config.py",
        "app/models/schemas.py",
        "requirements.txt",
        "Dockerfile",
        ".env.example"
    ]
    
    # API endpoints
    api_files = [
        "app/api/health.py",
        "app/api/research.py",
        "app/api/export.py"
    ]
    
    # Services
    service_files = [
        "app/services/research_orchestrator.py",
        "app/services/ai_agent_service.py",
        "app/services/web_search_service.py",
        "app/services/export_service.py"
    ]
    
    # Test files
    test_files = [
        "tests/test_main.py"
    ]
    
    # Development tools
    dev_files = [
        "run.py",
        "setup.ps1",
        "README.md"
    ]
    
    def check_files(file_list: List[str], base_path: Path) -> Tuple[int, int]:
        existing = sum(1 for f in file_list if (base_path / f).exists())
        return existing, len(file_list)
    
    return {
        "exists": backend_path.exists(),
        "core": check_files(core_files, backend_path),
        "api": check_files(api_files, backend_path),
        "services": check_files(service_files, backend_path),
        "tests": check_files(test_files, backend_path),
        "dev_tools": check_files(dev_files, backend_path),
        "total_files": get_file_count(str(backend_path), "**/*.py")
    }

def check_frontend_status() -> Dict:
    """Check frontend development status"""
    frontend_path = Path("frontend")
    
    return {
        "exists": frontend_path.exists(),
        "package_json": (frontend_path / "package.json").exists() if frontend_path.exists() else False,
        "src_dir": (frontend_path / "src").exists() if frontend_path.exists() else False,
        "total_files": get_file_count(str(frontend_path), "**/*") if frontend_path.exists() else 0
    }

def check_infrastructure_status() -> Dict:
    """Check infrastructure development status"""
    infra_path = Path("infrastructure")
    
    return {
        "exists": infra_path.exists(),
        "bicep": (infra_path / "bicep").exists() if infra_path.exists() else False,
        "terraform": (infra_path / "terraform").exists() if infra_path.exists() else False,
        "total_files": get_file_count(str(infra_path), "**/*") if infra_path.exists() else 0
    }

def check_cicd_status() -> Dict:
    """Check CI/CD pipeline status"""
    github_path = Path(".github")
    
    return {
        "exists": github_path.exists(),
        "workflows": (github_path / "workflows").exists() if github_path.exists() else False,
        "total_files": get_file_count(str(github_path), "**/*.yml") if github_path.exists() else 0
    }

def main():
    """Main status check function"""
    print_header("DEEP RESEARCH APPLICATION STATUS")
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"\n{Colors.WHITE}Current Directory: {current_dir}{Colors.END}")
    
    # Overall project files
    project_files = [
        "README.md",
        ".gitignore"
    ]
    
    print_section("📁 Project Overview")
    for file in project_files:
        status = check_file_exists(file)
        print(f"  {format_status(status)} {file}")
    
    # Backend Status
    print_section("🐍 Backend Status (Python/FastAPI)")
    backend = check_backend_status()
    
    if backend["exists"]:
        print(f"  {format_status(True)} Backend directory exists")
        print(f"  {format_partial(*backend['core'])} Core files")
        print(f"  {format_partial(*backend['api'])} API endpoints")
        print(f"  {format_partial(*backend['services'])} Services")
        print(f"  {format_partial(*backend['tests'])} Tests")
        print(f"  {format_partial(*backend['dev_tools'])} Development tools")
        print(f"  {Colors.WHITE}Total Python files: {backend['total_files']}{Colors.END}")
    else:
        print(f"  {format_status(False)} Backend directory missing")
    
    # Frontend Status
    print_section("⚛️  Frontend Status (React.js)")
    frontend = check_frontend_status()
    
    if frontend["exists"]:
        print(f"  {format_status(True)} Frontend directory exists")
        print(f"  {format_status(frontend['package_json'])} package.json")
        print(f"  {format_status(frontend['src_dir'])} src/ directory")
        print(f"  {Colors.WHITE}Total files: {frontend['total_files']}{Colors.END}")
    else:
        print(f"  {format_status(False)} Frontend directory missing")
        print(f"  {Colors.YELLOW}📋 TODO: React.js frontend implementation{Colors.END}")
    
    # Infrastructure Status
    print_section("🏗️  Infrastructure Status (IaC)")
    infra = check_infrastructure_status()
    
    if infra["exists"]:
        print(f"  {format_status(True)} Infrastructure directory exists")
        print(f"  {format_status(infra['bicep'])} Bicep templates")
        print(f"  {format_status(infra['terraform'])} Terraform templates")
        print(f"  {Colors.WHITE}Total files: {infra['total_files']}{Colors.END}")
    else:
        print(f"  {format_status(False)} Infrastructure directory missing")
        print(f"  {Colors.YELLOW}📋 TODO: Azure Infrastructure as Code{Colors.END}")
    
    # CI/CD Status
    print_section("🔄 CI/CD Status (GitHub Actions)")
    cicd = check_cicd_status()
    
    if cicd["exists"]:
        print(f"  {format_status(True)} .github directory exists")
        print(f"  {format_status(cicd['workflows'])} workflows/ directory")
        print(f"  {Colors.WHITE}Total workflow files: {cicd['total_files']}{Colors.END}")
    else:
        print(f"  {format_status(False)} .github directory missing")
        print(f"  {Colors.YELLOW}📋 TODO: CI/CD pipeline implementation{Colors.END}")
    
    # Summary
    print_section("📊 Development Progress Summary")
    
    # Calculate overall completion
    backend_completion = 85 if backend["exists"] and sum(backend["core"]) >= 5 else 0
    frontend_completion = 10 if frontend["exists"] else 0
    infra_completion = 5 if infra["exists"] else 0
    cicd_completion = 5 if cicd["exists"] else 0
    
    total_completion = backend_completion + frontend_completion + infra_completion + cicd_completion
    
    print(f"  🐍 Backend (Python/FastAPI): {Colors.GREEN if backend_completion > 80 else Colors.YELLOW}{backend_completion}%{Colors.END}")
    print(f"  ⚛️  Frontend (React.js): {Colors.RED if frontend_completion == 0 else Colors.YELLOW}{frontend_completion}%{Colors.END}")
    print(f"  🏗️  Infrastructure (IaC): {Colors.RED if infra_completion == 0 else Colors.YELLOW}{infra_completion}%{Colors.END}")
    print(f"  🔄 CI/CD (GitHub Actions): {Colors.RED if cicd_completion == 0 else Colors.YELLOW}{cicd_completion}%{Colors.END}")
    
    print(f"\n  {Colors.BOLD}Overall Progress: {Colors.GREEN if total_completion > 80 else Colors.YELLOW if total_completion > 40 else Colors.RED}{total_completion}%{Colors.END}")
    
    # Next Steps
    print_section("🎯 Next Steps")
    if backend_completion > 80:
        print(f"  {Colors.GREEN}✓{Colors.END} Backend foundation complete")
    
    if frontend_completion < 50:
        print(f"  {Colors.YELLOW}📋{Colors.END} Create React.js frontend application")
        print(f"    └── Components for research interface, progress tracking, exports")
    
    if infra_completion < 50:
        print(f"  {Colors.YELLOW}📋{Colors.END} Implement Infrastructure as Code")
        print(f"    └── Bicep/Terraform templates for Azure deployment")
    
    if cicd_completion < 50:
        print(f"  {Colors.YELLOW}📋{Colors.END} Set up CI/CD pipelines")
        print(f"    └── GitHub Actions for automated deployment")
    
    # Quick Commands
    print_section("🚀 Quick Commands")
    if backend["exists"]:
        print(f"  {Colors.CYAN}Backend Development:{Colors.END}")
        print(f"    cd backend && python run.py serve --debug")
        print(f"    cd backend && python run.py test")
        print(f"    cd backend && python run.py health")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}Status check complete!{Colors.END}")
    print(f"{Colors.WHITE}Run this script anytime to check development progress.{Colors.END}\n")

if __name__ == "__main__":
    main()
