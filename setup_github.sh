#!/bin/bash
# Script to set up GitHub repository

cd "/home/kali/Desktop/AWS delivery project"

echo "🚀 Setting up GitHub Repository..."
echo ""

# Check if remote exists
if git remote | grep -q origin; then
    echo "✅ Remote 'origin' already exists"
    git remote -v
else
    echo "📋 To create the repository, run these commands:"
    echo ""
    echo "1. Go to: https://github.com/new"
    echo "2. Repository name: courier-delivery-system"
    echo "3. Description: Courier Delivery System with Flask, AWS, and CI/CD"
    echo "4. Choose: Public"
    echo "5. DO NOT initialize with README (we already have one)"
    echo "6. Click 'Create repository'"
    echo ""
    echo "Then run:"
    echo "  git remote add origin https://github.com/YOUR_USERNAME/courier-delivery-system.git"
    echo "  git branch -M main"
    echo "  git push -u origin main"
    echo ""
fi

# Show current status
echo ""
echo "📊 Current Git Status:"
git status --short | head -10

echo ""
echo "✅ Ready to push to GitHub!"

