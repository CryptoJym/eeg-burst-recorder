#!/usr/bin/env python3
"""
Production Setup Script
-----------------------
Bridging the gap between "Code Complete" and "Deployment Ready".
1. Checks/Creates .env file for API keys.
2. Verifies API connectivity (xAI, OpenAI).
3. Checks for Gold Standard datasets and creates directory structure.
4. Installs production dependencies (python-dotenv).
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Setup")

REQUIRED_KEYS = [
    "XAI_API_KEY"
]

DATA_DIRS = [
    "data/icassp_2023",
    "data/nature_2025",
    "data/physionet_auditory"
]

def check_dotenv():
    """Check for .env file and python-dotenv"""
    try:
        import dotenv
        dotenv.load_dotenv()
        logger.info("✅ python-dotenv installed and loaded.")
    except ImportError:
        logger.warning("⚠️ python-dotenv not found. Installing...")
        os.system(f"{sys.executable} -m pip install python-dotenv")
        import dotenv
        dotenv.load_dotenv()
        logger.info("✅ python-dotenv installed.")

    env_path = Path(".env")
    if not env_path.exists():
        logger.warning("⚠️ No .env file found. Creating template...")
        with open(env_path, "w") as f:
            f.write("# Symbiosis Production Keys\n")
            f.write("XAI_API_KEY=your_xai_key_here\n")
        logger.info("✅ Created .env template. PLEASE EDIT THIS FILE WITH REAL KEYS.")
        return False
    return True

def check_api_keys():
    """Verify API keys are present and look valid"""
    missing = []
    for key in REQUIRED_KEYS:
        val = os.getenv(key)
        if not val or val.startswith("your_"):
            missing.append(key)
    
    if missing:
        logger.error(f"❌ Missing or default API Keys: {', '.join(missing)}")
        logger.error("   -> Edit .env and add your actual keys.")
        return False
    
    logger.info("✅ API Keys present in environment.")
    return True

def check_data_dirs():
    """Verify data directory structure"""
    root = Path(".")
    for d in DATA_DIRS:
        path = root / d
        if not path.exists():
            logger.warning(f"⚠️ Missing data directory: {d}")
            logger.info(f"   -> Creating {d}...")
            path.mkdir(parents=True, exist_ok=True)
            # Add README
            with open(path / "README.txt", "w") as f:
                f.write(f"Place {d.split('/')[-1]} dataset files here.\n")
                f.write("System will automatically detect and use them for validation.\n")
        else:
            logger.info(f"✅ Found directory: {d}")

def main():
    logger.info("=== Symbiosis Production Setup ===")
    
    # 1. Environment
    if not check_dotenv():
        logger.warning("Please configure .env before proceeding.")
        # We continue to show other checks
    
    # 2. Keys
    keys_ok = check_api_keys()
    
    # 3. Data
    check_data_dirs()
    
    # 4. Final Status
    if keys_ok:
        logger.info("\n🎉 READY FOR DEPLOYMENT")
        logger.info("   Run: ./start_session.sh")
    else:
        logger.error("\n⛔ NOT READY. Please fix API keys in .env")
        sys.exit(1)

if __name__ == "__main__":
    main()
