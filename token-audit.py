#!/usr/bin/env python3
"""
Token Usage Audit Script for CrossFit Blaze
Scans workspace files, calculates token usage, and generates optimization recommendations.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Configuration
WORKSPACE_DIR = Path.home() / "clawd"
MEMORY_DIR = WORKSPACE_DIR / "memory"
CONTEXT_FILES = [
    "SOUL.md",
    "USER.md",
    "IDENTITY.md",
    "MEMORY.md",
    "AGENTS.md",
    "TOOLS.md",
    "memory/*.md"
]

# Token estimation (rough: ~4 chars per token for English text)
CHARS_PER_TOKEN = 4

class TokenAuditor:
    def __init__(self):
        self.files_data = []
        self.duplicates = []
        self.old_files = []
        self.large_files = []
        self.total_context_tokens = 0
        
    def scan_files(self):
        """Scan all markdown and context files."""
        print("🔍 Scanning workspace files...")
        
        # Scan main context files
        for pattern in ["*.md", "memory/*.md", "**/*.md"]:
            for file_path in WORKSPACE_DIR.glob(pattern):
                if file_path.is_file():
                    self._analyze_file(file_path)
    
    def _analyze_file(self, file_path):
        """Analyze a single file."""
        try:
            stat = file_path.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Read content for duplicate detection
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                content = ""
            
            # Calculate estimated tokens
            estimated_tokens = size // CHARS_PER_TOKEN
            
            file_data = {
                "path": str(file_path.relative_to(WORKSPACE_DIR)),
                "size": size,
                "estimatedTokens": estimated_tokens,
                "modified": modified.isoformat(),
                "isStale": (datetime.now() - modified) > timedelta(days=30),
                "contentHash": hashlib.md5(content.encode()).hexdigest()[:16]
            }
            
            self.files_data.append(file_data)
            self.total_context_tokens += estimated_tokens
            
            # Check if large (>5000 tokens)
            if estimated_tokens > 5000:
                self.large_files.append(file_data)
            
            # Check if stale
            if file_data["isStale"]:
                self.old_files.append(file_data)
                
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
    
    def find_duplicates(self):
        """Find files with duplicate content."""
        print("🔍 Checking for duplicates...")
        
        # Group by content hash
        hash_groups = defaultdict(list)
        for file_data in self.files_data:
            hash_groups[file_data["contentHash"]].append(file_data)
        
        # Find duplicates (same hash, different files)
        for hash_val, files in hash_groups.items():
            if len(files) > 1:
                self.duplicates.append({
                    "hash": hash_val,
                    "files": [f["path"] for f in files]
                })
    
    def generate_report(self):
        """Generate the audit report."""
        print("📊 Generating report...")
        
        # Sort files by size (largest first)
        sorted_files = sorted(self.files_data, key=lambda x: x["size"], reverse=True)
        
        # Get usage stats (mock for now - would come from OpenClaw API)
        today_usage = self._estimate_today_usage()
        
        report = {
            "scanDate": datetime.now().isoformat(),
            "summary": {
                "totalFiles": len(self.files_data),
                "totalContextTokens": self.total_context_tokens,
                "largeFilesCount": len(self.large_files),
                "duplicatesCount": len(self.duplicates),
                "staleFilesCount": len(self.old_files)
            },
            "files": sorted_files[:50],  # Top 50 files
            "largeFiles": self.large_files,
            "duplicates": self.duplicates,
            "oldFiles": self.old_files,
            "todayUsage": today_usage,
            "avgUsage": today_usage * 0.8,  # Estimate
            "contextTokens": self.total_context_tokens
        }
        
        return report
    
    def _estimate_today_usage(self):
        """Estimate today's token usage (would ideally come from API)."""
        # For now, estimate based on context loading
        session_tokens = self.total_context_tokens * 2  # Load + response
        activity_multiplier = 5  # Number of interactions
        return session_tokens * activity_multiplier
    
    def save_dashboard_data(self, report):
        """Save data for dashboard."""
        dashboard_data_path = WORKSPACE_DIR / "token-dashboard-data.json"
        
        with open(dashboard_data_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Dashboard data saved to {dashboard_data_path}")
        
        # Also output to console for immediate viewing
        print("\n" + "="*60)
        print("📊 TOKEN AUDIT REPORT")
        print("="*60)
        print(f"\n📁 Files Scanned: {report['summary']['totalFiles']}")
        print(f"🔢 Total Context Tokens: {report['summary']['totalContextTokens']:,}")
        print(f"⚠️  Large Files (>5K tokens): {report['summary']['largeFilesCount']}")
        print(f"🔄 Duplicates: {report['summary']['duplicatesCount']}")
        print(f"📅 Stale Files (>30 days): {report['summary']['staleFilesCount']}")
        
        if self.large_files:
            print("\n⚠️  Large Files:")
            for f in self.large_files[:5]:
                print(f"   • {f['path']}: {f['estimatedTokens']:,} tokens")
        
        if self.duplicates:
            print("\n🔄 Duplicates Found:")
            for dup in self.duplicates[:3]:
                print(f"   • Same content in: {', '.join(dup['files'])}")
        
        print("\n" + "="*60)
        
        return dashboard_data_path

def main():
    print("🔥 CrossFit Blaze Token Audit")
    print("="*60 + "\n")
    
    auditor = TokenAuditor()
    auditor.scan_files()
    auditor.find_duplicates()
    
    report = auditor.generate_report()
    dashboard_path = auditor.save_dashboard_data(report)
    
    # Update the HTML dashboard with the data
    update_dashboard_html(report)
    
    print(f"\n✅ Audit complete!")
    print(f"🌐 View dashboard: open {WORKSPACE_DIR / 'token-dashboard.html'}")

def update_dashboard_html(report):
    """Update the HTML dashboard with real data."""
    dashboard_path = WORKSPACE_DIR / "token-dashboard.html"
    
    # Read the template
    with open(dashboard_path, 'r') as f:
        html = f.read()
    
    # Inject the data
    data_script = f"""
    <script>
        // Auto-populated by token-audit.py
        const auditData = {json.dumps(report)};
        
        // Populate on page load
        document.addEventListener('DOMContentLoaded', function() {{
            populateDashboard(auditData);
        }});
    </script>
    """
    
    # Insert before closing </body>
    html = html.replace('</body>', data_script + '\n</body>')
    
    with open(dashboard_path, 'w') as f:
        f.write(html)
    
    print(f"✅ Dashboard HTML updated with live data")

if __name__ == "__main__":
    main()
