#!/usr/bin/env python3
"""
Test runner for case_in.py integration tests.

This script:
1. Starts Firebase emulators
2. Runs comprehensive integration tests
3. Validates results
4. Cleans up
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_DIR = Path(__file__).parent.parent
FUNCTIONS_DIR = PROJECT_DIR / "functions"
EMULATOR_TIMEOUT = 90  # seconds


class EmulatorManager:
    """Manages Firebase emulators for testing."""
    
    def __init__(self):
        self.process = None
    
    def start(self):
        """Start Firebase emulators."""
        logger.info("Starting Firebase emulators...")
        
        # Change to project directory
        os.chdir(PROJECT_DIR)
        
        # Start emulators in background
        cmd = "firebase emulators:start"
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        
        # Wait for emulators to start and check for errors
        try:
            stdout, stderr = self.process.communicate(timeout=EMULATOR_TIMEOUT)
            if self.process.returncode != 0:
                logger.error("Failed to start emulators.")
                logger.error(f"Return Code: {self.process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.info("Emulators started successfully and are running in the background.")
            return True
        except Exception as e:
            logger.error(f"An unexpected error occurred while starting emulators: {e}")
            return False

        logger.info("Emulator process finished unexpectedly. Check logs for details.")
        return False
    
    def stop(self):
        """Stop Firebase emulators."""
        if self.process:
            logger.info("Stopping emulators...")
            self.process.terminate()
            self.process.wait()
            logger.info("Emulators stopped")


def run_tests():
    """Run the integration tests."""
    logger.info("Starting integration tests...")

    # Load environment variables from .env.test
    dotenv_path = FUNCTIONS_DIR / '.env.test'
    if dotenv_path.is_file():
        load_dotenv(dotenv_path)
        logger.info(f"Loaded environment variables from {dotenv_path}")
    
    # Check for required environment variables
    required_vars = ["GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.warning("Tests will skip Gemini API calls")
    
    # Change to functions directory
    os.chdir(FUNCTIONS_DIR)
    
    # Run pytest
    cmd = [
        "python", "-m", "pytest",
        "test_case_in.py",
        "-v",
        "--tb=short",
        "--log-cli-level=INFO"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False


def main():
    """Main test runner."""
    logger.info("=== Case In Integration Test Runner ===")
    
    # Start emulators
    emulator_manager = EmulatorManager()
    
    try:
        if not emulator_manager.start():
            logger.error("Failed to start emulators")
            return 1
        
        # Wait for emulators to be fully ready
        logger.info("Waiting for emulators to initialize...")
        time.sleep(10)
        
        # Run tests
        success = run_tests()
        
        if success:
            logger.info("✅ All tests passed successfully")
        else:
            logger.error("❌ Some tests failed")
        
        return 0 if success else 1
        
    finally:
        emulator_manager.stop()


if __name__ == "__main__":
    sys.exit(main())