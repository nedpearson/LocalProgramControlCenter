"""
Test script for Forensic CPA AI API

This script tests all the main endpoints of the application.
Run this after starting the server to verify everything works.
"""

import requests
import json
from pathlib import Path


BASE_URL = "http://localhost:5000"


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_root():
    """Test the root endpoint."""
    print_section("Testing Root Endpoint (GET /)")

    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Application: {data.get('application')}")
            print(f"Version: {data.get('version')}")
            print(f"Supported Formats: {', '.join(data.get('supported_formats', []))}")
            print("✅ Root endpoint working!")
        else:
            print("❌ Root endpoint failed!")

        return response.status_code == 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_health():
    """Test the health check endpoint."""
    print_section("Testing Health Check (GET /health)")

    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Service: {data.get('service')}")
            print(f"Timestamp: {data.get('timestamp')}")
            print("✅ Health check passed!")
        else:
            print("❌ Health check failed!")

        return response.status_code == 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_list_files():
    """Test the list files endpoint."""
    print_section("Testing List Files (GET /api/files)")

    try:
        response = requests.get(f"{BASE_URL}/api/files")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Total Files: {data.get('count', 0)}")

            if data.get('count', 0) > 0:
                print("\nFiles:")
                for file_info in data.get('files', [])[:5]:  # Show first 5
                    print(f"  - {file_info.get('filename')} "
                          f"({file_info.get('size')} bytes, "
                          f"uploaded: {file_info.get('uploaded_at')})")

            print("✅ List files working!")
        else:
            print("❌ List files failed!")

        return response.status_code == 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_upload_file(file_path):
    """Test file upload endpoint."""
    print_section(f"Testing File Upload (POST /api/upload)")

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        print("Skipping upload test...")
        return False

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"File ID: {data.get('file_id')}")
            print(f"Filename: {data.get('filename')}")
            print(f"File Type: {data.get('file_type')}")
            print(f"Processed At: {data.get('processed_at')}")

            # Show summary of results
            results = data.get('results', {})
            if 'metadata' in results:
                print(f"\nMetadata: {json.dumps(results['metadata'], indent=2)}")

            print("✅ File upload working!")
            return True, data.get('file_id')
        else:
            print(f"❌ File upload failed: {response.text}")
            return False, None

    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None


def test_analyze_file(file_id):
    """Test the analyze endpoint."""
    print_section(f"Testing Analyze File (GET /api/analyze/{file_id})")

    if not file_id:
        print("❌ No file ID provided")
        return False

    try:
        response = requests.get(f"{BASE_URL}/api/analyze/{file_id}")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Analysis results retrieved successfully!")

            # Show a summary
            if 'metadata' in data:
                print(f"Metadata: {json.dumps(data['metadata'], indent=2)}")

            if 'text' in data:
                print(f"Text entries: {len(data.get('text', []))}")

            if 'tables' in data:
                print(f"Tables found: {len(data.get('tables', []))}")

            if 'sheets' in data:
                print(f"Sheets: {len(data.get('sheets', []))}")

            if 'paragraphs' in data:
                print(f"Paragraphs: {len(data.get('paragraphs', []))}")

            print("✅ Analyze endpoint working!")
        else:
            print(f"❌ Analyze failed: {response.text}")

        return response.status_code == 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Forensic CPA AI - API Test Suite" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")

    print(f"\nTesting server at: {BASE_URL}")
    print("Make sure the server is running (python main.py)\n")

    results = []

    # Test basic endpoints
    results.append(("Root Endpoint", test_root()))
    results.append(("Health Check", test_health()))
    results.append(("List Files", test_list_files()))

    # Test file upload (if a sample file exists)
    sample_files = [
        "sample.pdf",
        "sample.xlsx",
        "sample.docx",
        "../sample_data/sample.pdf"
    ]

    file_id = None
    for sample_file in sample_files:
        if Path(sample_file).exists():
            success, file_id = test_upload_file(sample_file)
            results.append(("File Upload", success))
            break
    else:
        print_section("File Upload Test")
        print("ℹ️  No sample file found. Skipping upload test.")
        print("   To test upload, create a sample file and run again.")

    # Test analyze if we have a file_id
    if file_id:
        results.append(("Analyze File", test_analyze_file(file_id)))

    # Print summary
    print_section("Test Summary")
    total = len(results)
    passed = sum(1 for _, success in results if success)

    print(f"\nResults: {passed}/{total} tests passed\n")

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print("\n" + "=" * 70)

    if passed == total:
        print("\n🎉 All tests passed! The API is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")

    print()


if __name__ == "__main__":
    run_all_tests()
