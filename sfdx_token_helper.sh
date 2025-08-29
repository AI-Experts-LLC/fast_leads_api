#!/bin/bash
# Salesforce CLI Helper for Getting Sandbox Security Token

set -e

echo "🔑 SALESFORCE SANDBOX TOKEN HELPER"
echo "=================================="

# Check if SFDX is installed
if ! command -v sfdx &> /dev/null; then
    echo "❌ Salesforce CLI not found"
    echo ""
    echo "📥 Install Salesforce CLI:"
    echo "   npm install -g @salesforce/cli"
    echo "   # OR"
    echo "   brew tap salesforce/salesforce-cli"
    echo "   brew install salesforce-cli"
    echo ""
    echo "📖 More info: https://developer.salesforce.com/tools/sfdxcli"
    exit 1
fi

echo "✅ Salesforce CLI found: $(sfdx --version | head -1)"
echo ""

# Check for existing sandbox auth
echo "🔍 Checking for existing sandbox authentication..."
SANDBOX_ORGS=$(sfdx auth:list --json | jq -r '.result[] | select(.instanceUrl | contains("test.salesforce.com")) | .alias // .username' 2>/dev/null || echo "")

if [ -n "$SANDBOX_ORGS" ]; then
    echo "✅ Found existing sandbox authentication(s):"
    echo "$SANDBOX_ORGS" | while read -r org; do
        echo "   - $org"
    done
    echo ""
    
    # Ask which org to use
    echo "📋 Available commands for existing sandbox:"
    echo "   sfdx org:display --target-org YOUR_SANDBOX_ALIAS"
    echo "   sfdx data:query --query \"SELECT Id, Username, Email FROM User WHERE Id = UserInfo.getUserId()\" --target-org YOUR_SANDBOX_ALIAS"
    echo ""
else
    echo "⚠️  No sandbox authentication found"
    echo ""
    echo "🔐 To authenticate to sandbox:"
    echo "   sfdx auth:web:login --instance-url https://test.salesforce.com --set-default-dev-hub --alias sandbox"
    echo ""
    echo "📋 This will:"
    echo "   1. Open browser to https://test.salesforce.com"
    echo "   2. Login with your sandbox credentials"
    echo "   3. Authorize the CLI"
    echo "   4. Set 'sandbox' as alias"
    echo ""
    
    read -p "🤔 Would you like to authenticate now? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting authentication..."
        sfdx auth:web:login --instance-url https://test.salesforce.com --alias sandbox
        
        if [ $? -eq 0 ]; then
            echo "✅ Authentication successful!"
        else
            echo "❌ Authentication failed"
            exit 1
        fi
    else
        echo "💡 Run authentication manually when ready"
        exit 0
    fi
fi

echo "🔑 SECURITY TOKEN RESET OPTIONS:"
echo "================================"
echo ""

echo "Option 1: Get current user info"
echo "   sfdx data:query --query \"SELECT Id, Username, Email, Name FROM User WHERE Id = UserInfo.getUserId()\" --target-org sandbox"
echo ""

echo "Option 2: Reset password (will also reset security token)"
echo "   sfdx user:password:generate --target-org sandbox"
echo "   ⚠️  This changes your password AND resets security token"
echo ""

echo "Option 3: Use Apex to trigger token reset"
cat << 'EOF'
   sfdx apex:execute --target-org sandbox << 'APEX'
   // This requires custom Apex code and special permissions
   System.resetPassword(UserInfo.getUserId(), true);
   APEX
EOF
echo "   ⚠️  Requires special permissions"
echo ""

echo "Option 4: Manual web interface (RECOMMENDED)"
echo "   1. sfdx org:open --target-org sandbox"
echo "   2. Navigate to: Setup → Users → Your User → Reset Security Token"
echo "   3. Click 'Reset Security Token'"
echo "   4. Check email for new token"
echo ""

# Check if user wants to open sandbox
read -p "🌐 Would you like to open sandbox in browser for manual token reset? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Opening sandbox..."
    sfdx org:open --target-org sandbox
    echo ""
    echo "📋 In the opened browser:"
    echo "   1. Click your profile picture → Settings"
    echo "   2. My Personal Information → Reset My Security Token"
    echo "   3. Click 'Reset Security Token'"
    echo "   4. Check your email for the new token"
    echo ""
    echo "💾 Then update your .env file:"
    echo "   SALESFORCE_SECURITY_TOKEN=YourNewTokenFromEmail"
else
    echo "💡 You can open sandbox later with: sfdx org:open --target-org sandbox"
fi

echo ""
echo "🎯 SUMMARY:"
echo "   ✅ Salesforce CLI provides org management"
echo "   ✅ Can open sandbox directly in browser"
echo "   ✅ Manual token reset is still the easiest method"
echo "   ⚠️  Programmatic token reset requires special setup"
echo ""
echo "📖 More SFDX commands: sfdx commands --help"
