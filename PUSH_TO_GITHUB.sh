#!/bin/bash

echo "🌉 InstaBridge - Push to GitHub"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

echo "📋 Current commits:"
git log --oneline -5
echo ""

echo "🚀 Ready to push InstaBridge to GitHub!"
echo ""
echo "Choose your method:"
echo ""
echo "1. RECOMMENDED: Create via GitHub website first"
echo "   a. Go to: https://github.com/new"
echo "   b. Repository name: InstaBridge"
echo "   c. Description: 🌉 Open-source Instagram to WhatsApp automation - Free alternative to commercial tools"
echo "   d. Public repository"
echo "   e. DON'T initialize (we have files)"
echo "   f. Click 'Create repository'"
echo ""
echo "2. Then run these commands:"
echo ""
echo "   git remote add origin https://github.com/barisegesevgili/InstaBridge.git"
echo "   git push -u origin main"
echo ""
read -p "Have you created the GitHub repository? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Adding remote..."
    git remote add origin https://github.com/barisegesevgili/InstaBridge.git 2>/dev/null || echo "Remote already exists"
    
    echo ""
    echo "Pushing to GitHub..."
    git push -u origin main
    
    echo ""
    echo "✅ SUCCESS! Your project is now on GitHub!"
    echo ""
    echo "📌 Next steps:"
    echo "1. Add topics: instagram-automation, whatsapp-automation, python-automation"
    echo "2. Enable GitHub Actions"
    echo "3. Create v1.0.0 release"
    echo ""
    echo "🌟 Your InstaBridge is live at:"
    echo "   https://github.com/barisegesevgili/InstaBridge"
else
    echo ""
    echo "Please create the repository first, then run this script again."
    echo "Or run these commands manually:"
    echo ""
    echo "  git remote add origin https://github.com/barisegesevgili/InstaBridge.git"
    echo "  git push -u origin main"
fi

echo ""
echo "📖 Full instructions: See GITHUB_SETUP.md"
