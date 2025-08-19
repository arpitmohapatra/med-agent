#!/usr/bin/env python3
"""
MedQuery Setup Script
Automated setup for the MedQuery MVP application
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a shell command and handle errors."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Exit code: {e.returncode}")
        print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check Node.js
    try:
        result = run_command("node --version", check=False)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
        else:
            print("❌ Node.js is required for the frontend")
            print("Please install Node.js from https://nodejs.org/")
            sys.exit(1)
    except:
        print("❌ Node.js not found")
        sys.exit(1)
    
    # Check npm
    try:
        result = run_command("npm --version", check=False)
        if result.returncode == 0:
            print(f"✅ npm {result.stdout.strip()}")
        else:
            print("❌ npm is required")
            sys.exit(1)
    except:
        print("❌ npm not found")
        sys.exit(1)

def setup_backend():
    """Set up the backend environment."""
    print("\n🐍 Setting up backend...")
    
    backend_dir = Path("backend")
    
    # Create virtual environment
    print("Creating virtual environment...")
    run_command("python -m venv venv", cwd=backend_dir)
    
    # Determine activation script
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate.bat"
        pip_command = "venv\\Scripts\\pip"
    else:  # Unix/Linux/MacOS
        activate_script = "source venv/bin/activate"
        pip_command = "venv/bin/pip"
    
    # Install dependencies
    print("Installing Python dependencies...")
    run_command(f"{pip_command} install --upgrade pip", cwd=backend_dir)
    run_command(f"{pip_command} install -r requirements.txt", cwd=backend_dir)
    
    # Create .env file if it doesn't exist
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("Creating .env file...")
        env_example = backend_dir / "env.example"
        if env_example.exists():
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Created .env file from template")
            print("⚠️  Please update .env with your API keys and configuration")
        else:
            # Create basic .env
            with open(env_file, 'w') as f:
                f.write("""# MedQuery Configuration
JWT_SECRET_KEY=change-this-secret-key-in-production
OPENAI_API_KEY=your-openai-api-key-here
ELASTICSEARCH_URL=http://localhost:9200
DEBUG=true
""")
            print("✅ Created basic .env file")
    
    print("✅ Backend setup complete!")

def setup_frontend():
    """Set up the frontend environment."""
    print("\n⚛️  Setting up frontend...")
    
    frontend_dir = Path("frontend")
    
    # Install dependencies
    print("Installing Node.js dependencies...")
    run_command("npm install", cwd=frontend_dir)
    
    print("✅ Frontend setup complete!")

def check_elasticsearch():
    """Check if Elasticsearch is running."""
    print("\n🔍 Checking Elasticsearch...")
    
    try:
        import requests
        response = requests.get("http://localhost:9200", timeout=5)
        if response.status_code == 200:
            print("✅ Elasticsearch is running")
            return True
        else:
            print("❌ Elasticsearch returned non-200 status")
            return False
    except:
        print("❌ Elasticsearch is not running on localhost:9200")
        print("💡 Start Elasticsearch or update ELASTICSEARCH_URL in .env")
        return False

def create_demo_user():
    """Create a demo user for testing."""
    print("\n👤 Creating demo user...")
    
    backend_dir = Path("backend")
    script_content = '''
import asyncio
import sys
sys.path.append(".")

from app.services.auth import AuthService
from app.models.user import UserCreate

async def create_demo_user():
    auth_service = AuthService()
    
    # Check if demo user already exists
    existing_user = auth_service.get_user_by_username("demo")
    if existing_user:
        print("Demo user already exists")
        return
    
    # Create demo user
    demo_user = UserCreate(
        username="demo",
        email="demo@medquery.app",
        password="password123",
        full_name="Demo User"
    )
    
    try:
        user = auth_service.create_user(demo_user)
        print(f"Created demo user: {user.username}")
    except Exception as e:
        print(f"Error creating demo user: {e}")

if __name__ == "__main__":
    asyncio.run(create_demo_user())
'''
    
    script_file = backend_dir / "create_demo_user.py"
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    # Run the script
    if os.name == 'nt':
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    run_command(f"{python_cmd} create_demo_user.py", cwd=backend_dir, check=False)
    
    # Clean up
    script_file.unlink()

def print_next_steps():
    """Print next steps for the user."""
    print("\n🎉 Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Start Elasticsearch (if not already running)")
    print("   - Download from: https://www.elastic.co/downloads/elasticsearch")
    print("   - Or use Docker: docker run -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.11.0")
    print()
    print("2. Update configuration:")
    print("   - Edit backend/.env with your API keys")
    print("   - Add your OpenAI or Azure OpenAI credentials")
    print()
    print("3. Start the backend:")
    print("   cd backend")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python main.py")
    print()
    print("4. Start the frontend (in a new terminal):")
    print("   cd frontend")
    print("   npm start")
    print()
    print("5. Ingest sample data:")
    print("   cd backend")
    if os.name == 'nt':
        print("   venv\\Scripts\\python scripts/ingest_data.py --sample")
    else:
        print("   venv/bin/python scripts/ingest_data.py --sample")
    print()
    print("6. Open http://localhost:3000 and login with:")
    print("   Username: demo")
    print("   Password: password123")
    print()
    print("📚 Documentation: README.md")
    print("🐛 Issues: https://github.com/your-repo/medquery/issues")

def main():
    """Main setup function."""
    print("🏥 MedQuery MVP Setup")
    print("=" * 50)
    
    # Check prerequisites
    check_prerequisites()
    
    # Setup backend
    setup_backend()
    
    # Setup frontend
    setup_frontend()
    
    # Check Elasticsearch
    check_elasticsearch()
    
    # Create demo user
    create_demo_user()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
