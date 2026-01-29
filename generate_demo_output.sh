#!/bin/bash
# Generate screenshot-ready output

echo "🎬 Generating demo output..."

# Run parser with clean output
python3 backend/parsers/multi_file_xbrl_parser.py 2>/dev/null > raw_output.txt

# Apply formatting (if demo_formatter exists)
if [ -f backend/utils/demo_formatter.py ]; then
    python3 backend/utils/demo_formatter.py > demo_output.txt
    echo "✅ Formatted demo output saved to: demo_output.txt"
else
    # Simple emoji injection
    cat raw_output.txt | \
        sed 's/Balance Sheet/📊 BALANCE SHEET/g' | \
        sed 's/Income Statement/💰 INCOME STATEMENT/g' | \
        sed 's/Cash Flow/💵 CASH FLOW/g' | \
        sed 's/PASSED/✅ PASSED/g' | \
        sed 's/Processing time/⚡ Processing time/g' \
        > demo_output.txt
    echo "✅ Simple formatted output saved to: demo_output.txt"
fi

# Display preview
echo ""
echo "📋 Preview (first 30 lines):"
head -30 demo_output.txt

echo ""
echo "💡 Next steps:"
echo "1. Review: cat demo_output.txt"
echo "2. Screenshot: Open in terminal with nice theme"
echo "3. Beautify: Use carbon.now.sh if needed"
