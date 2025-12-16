#!/bin/bash
# Test sync functionality

echo "=== Testing sync_monthly_data.py ==="
echo ""

# Test with October 2025
echo "Testing October 2025 sync..."
python sync_monthly_data.py --month 10 --year 2025

echo ""
echo "=== Checking downloaded files ==="
echo ""

echo "Basic manpower data:"
ls -lh input_files/basic\ manpower\ data\ october.csv 2>/dev/null || echo "  ❌ Not found"

echo ""
echo "5PRS data:"
ls -lh input_files/5prs\ data\ october.csv 2>/dev/null || echo "  ❌ Not found"

echo ""
echo "Attendance data:"
ls -lh input_files/attendance/original/attendance\ data\ october.csv 2>/dev/null || echo "  ❌ Not found"
ls -lh input_files/attendance/converted/attendance\ data\ october_converted.csv 2>/dev/null || echo "  ❌ Not found"

echo ""
echo "AQL data:"
ls -lh input_files/AQL\ history/*OCTOBER*.csv 2>/dev/null || echo "  ❌ Not found"

echo ""
echo "=== Test complete ==="
