"""
Setup script for Multi-Agent Orchestrator

This script installs required dependencies and guides through environment setup.
"""

import subprocess
import sys
import os

def install_packages():
    """Install required Python packages."""
    print("📦 Installing required packages...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def check_environment():
    """Check if environment variables are configured."""
    print("\n🔧 Checking environment configuration...")
    
    required_vars = ["PROJECT_ENDPOINT", "MODEL_DEPLOYMENT_NAME", "BING_CONNECTION_NAME"]
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("\n📝 Please:")
        print("1. Copy .env.template to .env")
        print("2. Fill in your Azure AI Foundry project details")
        print("3. Restart your terminal or run: python-dotenv")
        return False
    else:
        print("✅ All environment variables are configured!")
        return True

def check_azure_auth():
    """Check Azure CLI authentication."""
    print("\n🔐 Checking Azure authentication...")
    
    try:
        result = subprocess.run(["az", "account", "show"], 
                              capture_output=True, text=True, check=True)
        print("✅ Azure CLI authentication is active!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Azure CLI not authenticated or not installed")
        print("\n📝 Please run: az login")
        return False

def main():
    """Main setup function."""
    print("🚀 Multi-Agent Orchestrator Setup\n")
    
    success_count = 0
    
    # Install packages
    if install_packages():
        success_count += 1
    
    # Check environment
    if check_environment():
        success_count += 1
    
    # Check Azure auth
    if check_azure_auth():
        success_count += 1
    
    print(f"\n📊 Setup Status: {success_count}/3 steps completed")
    
    if success_count == 3:
        print("\n🎉 Setup completed successfully!")
        print("\n🚀 You can now run the orchestrator:")
        print("   python src/main.py")
    else:
        print("\n⚠️  Setup incomplete. Please address the issues above.")

if __name__ == "__main__":
    main()
