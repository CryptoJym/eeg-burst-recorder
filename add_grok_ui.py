#!/usr/bin/env python3
"""Add Grok export UI to session_recorder_live.html"""

import re

html_file = 'ui/session_recorder_live.html'

# Read the current HTML
with open(html_file, 'r') as f:
    html = f.read()

# 1. Add modal CSS before </style>
modal_css = '''
        /* Grok Export Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal-overlay.show {
            display: flex;
        }

        .modal-content {
            background: #2a2a2a;
            border-radius: 12px;
            width: 90%;
            max-width: 900px;
            max-height: 90vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        }

        .modal-header {
            padding: 20px;
            border-bottom: 2px solid #3a3a3a;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-title {
            font-size: 20px;
            font-weight: 600;
            color: #00C851;
        }

        .modal-close {
            background: none;
            border: none;
            color: #888;
            font-size: 28px;
            cursor: pointer;
            padding: 0;
            width: 32px;
            height: 32px;
        }

        .modal-close:hover {
            color: #fff;
        }

        .modal-body {
            padding: 20px;
            overflow-y: auto;
            flex: 1;
        }

        .modal-footer {
            padding: 15px 20px;
            border-top: 2px solid #3a3a3a;
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }

        .json-display {
            background: #1a1a1a;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 500px;
            overflow-y: auto;
            color: #00C851;
        }

        .session-list {
            background: #1a1a1a;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 10px;
        }

        .session-item {
            padding: 12px;
            border-bottom: 1px solid #3a3a3a;
            cursor: pointer;
            transition: background 0.2s;
        }

        .session-item:hover {
            background: #2a2a2a;
        }

        .session-item.selected {
            background: #004d00;
        }

        .session-item-name {
            font-weight: 600;
            color: #00C851;
        }

        .session-item-meta {
            font-size: 12px;
            color: #888;
            margin-top: 4px;
        }

        .btn-success {
            background: #00C851;
            color: #000;
            font-weight: 600;
        }

        .btn-success:hover {
            background: #00E55C;
        }

        .btn-secondary {
            background: #555;
            color: #fff;
        }

        .btn-secondary:hover {
            background: #666;
        }

        .btn-grok {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            font-weight: 600;
        }

        .btn-grok:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
'''

html = html.replace('    </style>', modal_css + '\n    </style>')

# 2. Add Grok button after Stop button
grok_button = '''                <button class="btn btn-grok" id="grokBtn">
                    🤖 Export for Grok
                </button>
'''

html = html.replace(
    '''                <button class="btn btn-danger hidden" id="stopBtn">
                    ■ Stop Recording
                </button>''',
    '''                <button class="btn btn-danger hidden" id="stopBtn">
                    ■ Stop Recording
                </button>
''' + grok_button
)

# 3. Add modal HTML before </body>
modal_html = '''
    <!-- Grok Export Modal -->
    <div class="modal-overlay" id="grokModal">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title">🤖 Export for Grok AI</div>
                <button class="modal-close" onclick="closeGrokModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div id="sessionSelectorView">
                    <h3 style="color: #ccc; margin-bottom: 10px;">Select Session to Export:</h3>
                    <div class="session-list" id="sessionList">
                        <div style="padding: 20px; text-align: center; color: #888;">
                            Loading sessions...
                        </div>
                    </div>
                </div>
                <div id="jsonView" style="display: none;">
                    <h3 style="color: #ccc; margin-bottom: 10px;">Copy and Paste to Grok:</h3>
                    <div class="json-display" id="jsonDisplay"></div>
                </div>
            </div>
            <div class="modal-footer">
                <span class="copy-feedback" id="copyFeedback">✓ Copied!</span>
                <button class="btn btn-secondary" onclick="closeGrokModal()">Close</button>
                <button class="btn btn-success" id="copyJsonBtn" onclick="copyJsonToClipboard()" style="display: none;">
                    📋 Copy to Clipboard
                </button>
            </div>
        </div>
    </div>

'''

html = html.replace('</body>', modal_html + '</body>')

# 4. Add JavaScript before </script>
grok_js = '''
        // Grok Export Functions
        let selectedSessionId = null;
        let grokJsonData = null;

        async function openGrokModal() {
            document.getElementById('grokModal').classList.add('show');
            document.getElementById('sessionSelectorView').style.display = 'block';
            document.getElementById('jsonView').style.display = 'none';
            document.getElementById('copyJsonBtn').style.display = 'none';
            await loadSessions();
        }

        function closeGrokModal() {
            document.getElementById('grokModal').classList.remove('show');
            selectedSessionId = null;
            grokJsonData = null;
        }

        async function loadSessions() {
            try {
                const response = await fetch('/api/sessions-list');
                const data = await response.json();

                const sessionList = document.getElementById('sessionList');

                if (data.sessions.length === 0) {
                    sessionList.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #888;">
                            No sessions available yet.<br>
                            Record a session first!
                        </div>
                    `;
                    return;
                }

                sessionList.innerHTML = data.sessions.map(session => `
                    <div class="session-item" onclick="selectSession('${session.id}')">
                        <div class="session-item-name">${session.name}</div>
                        <div class="session-item-meta">
                            ${session.burst_count} bursts
                            ${session.started_at ? ' • ' + new Date(session.started_at).toLocaleString() : ''}
                        </div>
                    </div>
                `).join('');

            } catch (error) {
                console.error('Error loading sessions:', error);
                document.getElementById('sessionList').innerHTML = `
                    <div style="padding: 20px; text-align: center; color: #ff4444;">
                        Error loading sessions
                    </div>
                `;
            }
        }

        async function selectSession(sessionId) {
            selectedSessionId = sessionId;

            // Highlight selected
            document.querySelectorAll('.session-item').forEach(item => {
                item.classList.remove('selected');
            });
            event.target.closest('.session-item').classList.add('selected');

            // Fetch Grok export
            try {
                const response = await fetch(`/api/sessions/${sessionId}/grok`);
                const data = await response.json();

                if (data.error) {
                    alert(`Error: ${data.error}`);
                    return;
                }

                grokJsonData = JSON.stringify(data, null, 2);

                // Show JSON view
                document.getElementById('sessionSelectorView').style.display = 'none';
                document.getElementById('jsonView').style.display = 'block';
                document.getElementById('copyJsonBtn').style.display = 'inline-block';
                document.getElementById('jsonDisplay').textContent = grokJsonData;

            } catch (error) {
                console.error('Error exporting for Grok:', error);
                alert('Error exporting session');
            }
        }

        async function copyJsonToClipboard() {
            try {
                await navigator.clipboard.writeText(grokJsonData);
                const feedback = document.getElementById('copyFeedback');
                feedback.classList.add('show');
                setTimeout(() => {
                    feedback.classList.remove('show');
                }, 2000);
            } catch (error) {
                console.error('Error copying to clipboard:', error);
                alert('Failed to copy. Please select and copy manually.');
            }
        }

        // Attach Grok button handler
        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('grokBtn').addEventListener('click', openGrokModal);
        });

'''

# Find the last </script> tag and add JS before it
last_script_pos = html.rfind('</script>')
html = html[:last_script_pos] + grok_js + '\n        ' + html[last_script_pos:]

# Write back
with open(html_file, 'w') as f:
    f.write(html)

print("✅ Grok export UI added to session_recorder_live.html")
print("")
print("Features added:")
print("  - 🤖 'Export for Grok' button in control panel")
print("  - Session selector modal with burst counts")
print("  - JSON preview with syntax highlighting")
print("  - One-click copy to clipboard")
print("")
print("Restart server and hard-refresh browser to see changes!")
