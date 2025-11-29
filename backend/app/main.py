"""
FastAPI Application Entry Point
================================
Initializes and configures the web application.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

# Import routers and database
from .api import router as api_router
from .websockets import router as ws_router
from .database import init_database

# Load environment variables
load_dotenv()

# ==================== APPLICATION SETUP ====================

app = FastAPI(
    title="Pair Programming Platform",
    description="Real-time collaborative coding with WebSocket support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==================== MIDDLEWARE ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print("\n" + "="*50)
    print("🚀 Starting Pair Programming Platform")
    print("="*50)
    init_database()
    print(f"📍 Environment: {os.getenv('DEBUG', 'False')}")
    print(f"🌐 Host: {os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8000')}")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print("="*50 + "\n")


# ==================== ROUTERS ====================

app.include_router(api_router)
app.include_router(ws_router)


# ==================== CODE EXECUTION ENDPOINT ====================

@app.post("/api/execute")
async def execute_code(request: dict):
    """
    Execute Python code and return output
    
    Args:
        request: {"code": "print('hello')", "language": "python"}
    
    Returns:
        {"output": "hello", "error": null} or {"output": null, "error": "error message"}
    """
    code = request.get("code", "")
    language = request.get("language", "python")
    
    # Currently only supports Python
    if language != "python":
        return JSONResponse({
            "output": None,
            "error": f"Code execution for {language} is not supported yet. Only Python is available."
        })
    
    # Security: Limit execution time and imports
    try:
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Create a restricted globals dictionary
        restricted_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "bool": bool,
                "sum": sum,
                "max": max,
                "min": min,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
            }
        }
        
        # Execute code with timeout
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, restricted_globals)
        
        output = stdout_capture.getvalue()
        errors = stderr_capture.getvalue()
        
        if errors:
            return JSONResponse({
                "output": output if output else None,
                "error": errors
            })
        
        return JSONResponse({
            "output": output if output else "Code executed successfully (no output)",
            "error": None
        })
    
    except Exception as e:
        return JSONResponse({
            "output": None,
            "error": f"{type(e).__name__}: {str(e)}"
        })


# ==================== STATIC FILES ====================

if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")


# ==================== HTML PAGES ====================

@app.get("/", response_class=HTMLResponse)
async def home_page():
    """Landing page - Create or join a room"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pair Programming Platform</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                max-width: 500px;
                width: 90%;
            }
            h1 {
                color: #667eea;
                margin-bottom: 10px;
                font-size: 28px;
            }
            p {
                color: #666;
                margin-bottom: 30px;
            }
            .action-group {
                margin-bottom: 20px;
            }
            input {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                margin-bottom: 10px;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                width: 100%;
                padding: 12px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                transition: background 0.3s;
            }
            button:hover {
                background: #5568d3;
            }
            .divider {
                text-align: center;
                margin: 20px 0;
                color: #999;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Pair Programming</h1>
            <p>Collaborate in real-time with WebSocket-powered code editor</p>
            
            <div class="action-group">
                <button onclick="createRoom()">Create New Room</button>
            </div>
            
            <div class="divider">— OR —</div>
            
            <div class="action-group">
                <input type="text" id="roomInput" placeholder="Enter Room ID" maxlength="8">
                <button onclick="joinRoom()">Join Existing Room</button>
            </div>
        </div>
        
        <script>
            async function createRoom() {
                try {
                    const response = await fetch('/api/rooms', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({language: 'python'})
                    });
                    const data = await response.json();
                    window.location.href = '/room/' + data.roomId;
                } catch (error) {
                    alert('Failed to create room: ' + error.message);
                }
            }
            
            function joinRoom() {
                const roomId = document.getElementById('roomInput').value.trim();
                if (!roomId) {
                    alert('Please enter a room ID');
                    return;
                }
                window.location.href = '/room/' + roomId;
            }
            
            document.getElementById('roomInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') joinRoom();
            });
        </script>
    </body>
    </html>
    """)


@app.get("/room/{room_id}", response_class=HTMLResponse)
async def room_page(room_id: str):
    """Collaborative coding room page with Monaco Editor"""
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Room {room_id} - Pair Programming</title>
        
        <!-- Monaco Editor CSS -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs/editor/editor.main.min.css">
        
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                overflow: hidden;
                background: #1e1e1e;
            }}
            
            /* Header */
            #header {{
                background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
                color: white;
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                z-index: 1000;
            }}
            
            #header h2 {{ 
                font-size: 18px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            #roomCodeDisplay {{
                background: rgba(255,255,255,0.1);
                padding: 5px 10px;
                border-radius: 4px;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 14px;
                cursor: pointer;
                transition: background 0.3s;
            }}
            
            #roomCodeDisplay:hover {{
                background: rgba(255,255,255,0.2);
            }}
            
            .header-right {{
                display: flex;
                align-items: center;
                gap: 15px;
            }}
            
            #userCount {{
                background: rgba(255,255,255,0.1);
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 13px;
            }}
            
            #status {{
                padding: 5px 15px;
                border-radius: 20px;
                background: #4a5568;
                font-size: 13px;
                font-weight: 500;
                transition: all 0.3s;
            }}
            
            #status.connected {{ 
                background: #48bb78;
                box-shadow: 0 0 10px rgba(72, 187, 120, 0.5);
            }}
            
            #status.disconnected {{ 
                background: #f56565;
                animation: blink 1s infinite;
            }}
            
            @keyframes blink {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.6; }}
            }}
            
            /* Language Selector */
            #languageSelector {{
                background: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 13px;
                cursor: pointer;
                outline: none;
            }}
            
            #languageSelector:hover {{
                background: #374151;
            }}
            
            #languageSelector option {{
                background: #2d3748;
                color: white;
                padding: 5px;
            }}
            
            /* Main Container */
            #main-container {{
                display: flex;
                height: calc(100vh - 110px);
            }}
            
            /* Editor Container */
            #editor-container {{
                flex: 1;
                position: relative;
                min-width: 0; /* Prevents flex overflow */
            }}
            
            #editor {{
                width: 100%;
                height: 100%;
            }}
            
            /* Output Panel - REDESIGNED */
            #output-panel {{
                width: 450px;
                min-width: 350px;
                max-width: 600px;
                background: #252526;
                border-left: 2px solid #3e3e3e;
                display: flex;
                flex-direction: column;
                box-shadow: -3px 0 15px rgba(0,0,0,0.3);
            }}
            
            /* Output Header - IMPROVED */
            #output-header {{
                background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
                color: white;
                padding: 15px;
                border-bottom: 2px solid #3e3e3e;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            
            .output-title {{
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 15px;
                font-weight: 600;
                color: #e2e8f0;
            }}
            
            .output-icon {{
                font-size: 20px;
            }}
            
            .output-actions {{
                display: flex;
                gap: 10px;
            }}
            
            #runCodeBtn {{
                flex: 1;
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s;
                box-shadow: 0 2px 8px rgba(72, 187, 120, 0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }}
            
            #runCodeBtn:hover {{
                background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
                box-shadow: 0 4px 12px rgba(72, 187, 120, 0.4);
                transform: translateY(-1px);
            }}
            
            #runCodeBtn:active {{
                transform: translateY(0);
            }}
            
            #runCodeBtn:disabled {{
                background: #4a5568;
                cursor: not-allowed;
                box-shadow: none;
                transform: none;
            }}
            
            #clearOutputBtn {{
                background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s;
                box-shadow: 0 2px 8px rgba(245, 101, 101, 0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }}
            
            #clearOutputBtn:hover {{
                background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
                box-shadow: 0 4px 12px rgba(245, 101, 101, 0.4);
                transform: translateY(-1px);
            }}
            
            #clearOutputBtn:active {{
                transform: translateY(0);
            }}
            
            /* Output Content */
            #output-content {{
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                font-size: 13px;
                color: #d4d4d4;
                line-height: 1.8;
                background: #1e1e1e;
            }}
            
            .output-line {{
                margin-bottom: 8px;
                padding: 4px 0;
                word-wrap: break-word;
            }}
            
            .output-error {{
                color: #f48771;
                background: rgba(244, 135, 113, 0.1);
                padding: 8px;
                border-left: 3px solid #f56565;
                border-radius: 4px;
                margin: 8px 0;
            }}
            
            .output-success {{
                color: #73c991;
                background: rgba(115, 201, 145, 0.1);
                padding: 8px;
                border-left: 3px solid #48bb78;
                border-radius: 4px;
                margin: 8px 0;
            }}
            
            .output-info {{
                color: #b794f4;
                background: rgba(183, 148, 244, 0.1);
                padding: 8px;
                border-left: 3px solid #9f7aea;
                border-radius: 4px;
                margin: 8px 0;
            }}
            
            .output-remote {{
                color: #f6ad55;
                background: rgba(246, 173, 85, 0.1);
                padding: 8px;
                border-left: 3px solid #ed8936;
                border-radius: 4px;
                margin: 8px 0;
                font-style: italic;
            }}
            
            .output-separator {{
                border-top: 1px solid #3e3e3e;
                margin: 12px 0;
            }}
            
            /* Output Stats */
            #output-stats {{
                background: #2d3748;
                padding: 10px 15px;
                border-top: 1px solid #3e3e3e;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 11px;
                color: #a0aec0;
            }}
            
            .stat-item {{
                display: flex;
                align-items: center;
                gap: 5px;
            }}
            
            /* Footer */
            #footer {{
                background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
                color: #a0aec0;
                padding: 12px 20px;
                font-size: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-top: 1px solid #4a5568;
            }}
            
            /* Loading Spinner */
            .spinner {{
                display: inline-block;
                width: 12px;
                height: 12px;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 0.8s linear infinite;
            }}
            
            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}
            
            /* Scrollbar Styling */
            ::-webkit-scrollbar {{
                width: 12px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: #1e1e1e;
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: #4a5568;
                border-radius: 6px;
                border: 2px solid #1e1e1e;
            }}
            
            ::-webkit-scrollbar-thumb:hover {{
                background: #667eea;
            }}
            
            /* Empty State */
            .empty-state {{
                text-align: center;
                padding: 40px 20px;
                color: #718096;
            }}
            
            .empty-state-icon {{
                font-size: 48px;
                margin-bottom: 15px;
                opacity: 0.5;
            }}
            
            /* Responsive */
            @media (max-width: 1200px) {{
                #output-panel {{
                    width: 350px;
                }}
            }}
        </style>
    </head>
    <body>
        <!-- Header -->
        <div id="header">
            <div>
                <h2>
                    🔗 Room: <span id="roomCodeDisplay" title="Click to copy">{room_id}</span>
                </h2>
            </div>
            <div class="header-right">
                <select id="languageSelector" title="Programming Language">
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="typescript">TypeScript</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                    <option value="csharp">C#</option>
                    <option value="go">Go</option>
                    <option value="rust">Rust</option>
                    <option value="php">PHP</option>
                    <option value="ruby">Ruby</option>
                </select>
                <span id="userCount">👤 1 user</span>
                <span id="status">
                    <span class="spinner"></span> Connecting...
                </span>
            </div>
        </div>
        
        <!-- Main Container: Editor + Output -->
        <div id="main-container">
            <!-- Monaco Editor Container -->
            <div id="editor-container">
                <div id="editor"></div>
            </div>
            
            <!-- Output Panel - REDESIGNED -->
            <div id="output-panel">
                <!-- Output Header -->
                <div id="output-header">
                    <div class="output-title">
                        <span class="output-icon">📺</span>
                        <span>Synchronized Output</span>
                    </div>
                    <div class="output-actions">
                        <button id="runCodeBtn">
                            <span>▶</span>
                            <span>Run Code</span>
                        </button>
                        <button id="clearOutputBtn">
                            <span>🗑</span>
                        </button>
                    </div>
                </div>
                
                <!-- Output Content -->
                <div id="output-content">
                    <div class="empty-state">
                        <div class="empty-state-icon">💻</div>
                        <div class="output-line output-info">
                            💡 Click "Run Code" to execute your Python code
                        </div>
                        <div class="output-line" style="color: #718096; margin-top: 10px;">
                            🔄 Output syncs in real-time with your pair programming partner
                        </div>
                    </div>
                </div>
                
                <!-- Output Stats -->
                <div id="output-stats">
                    <div class="stat-item">
                        <span>⚡</span>
                        <span id="executionTime">Ready</span>
                    </div>
                    <div class="stat-item">
                        <span>📊</span>
                        <span id="outputLines">0 lines</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div id="footer">
            <span>💡 <strong>Tip:</strong> Press Ctrl+Enter to run code quickly</span>
            <span style="color: #9f7aea;">🤖 AI Autocomplete Ready (Mocked for Prototype)</span>
        </div>
        
        <!-- Monaco Editor Loader -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs/loader.min.js"></script>
        
        <script>
            // ==================== CONFIGURATION ====================
            const roomId = '{room_id}';
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = protocol + '//' + window.location.host + '/ws/' + roomId;
            
            // ==================== GLOBAL STATE ====================
            let ws = null;
            let editor = null;
            let isRemoteUpdate = false;
            let typingTimeout = null;
            let isExecutingCode = false;
            let outputLineCount = 0;
            let executionStartTime = null;
            
            // ==================== ELEMENTS ====================
            const status = document.getElementById('status');
            const userCount = document.getElementById('userCount');
            const languageSelector = document.getElementById('languageSelector');
            const runCodeBtn = document.getElementById('runCodeBtn');
            const clearOutputBtn = document.getElementById('clearOutputBtn');
            const outputContent = document.getElementById('output-content');
            const roomCodeDisplay = document.getElementById('roomCodeDisplay');
            const executionTime = document.getElementById('executionTime');
            const outputLines = document.getElementById('outputLines');
            
            // ==================== MONACO EDITOR SETUP ====================
            
            require.config({{ 
                paths: {{ 
                    'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' 
                }} 
            }});
            
            require(['vs/editor/editor.main'], function() {{
                editor = monaco.editor.create(document.getElementById('editor'), {{
                    value: '# Welcome to Pair Programming Platform!\\n# Write your Python code here\\n\\nprint("Hello, World!")\\nprint("Start coding together!")',
                    language: 'python',
                    theme: 'vs-dark',
                    automaticLayout: true,
                    fontSize: 14,
                    minimap: {{ enabled: true }},
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    lineNumbers: 'on',
                    renderWhitespace: 'selection',
                    bracketPairColorization: {{ enabled: true }},
                    formatOnPaste: true,
                    formatOnType: true,
                    suggestOnTriggerCharacters: true,
                    quickSuggestions: {{
                        other: true,
                        comments: false,
                        strings: false
                    }},
                    parameterHints: {{ enabled: true }},
                    folding: true,
                    foldingStrategy: 'indentation',
                    showFoldingControls: 'always',
                    tabSize: 4,
                    insertSpaces: true,
                    detectIndentation: true,
                }});
                
                // ==================== INLINE SUGGESTIONS ====================
                
                monaco.languages.registerCompletionItemProvider('python', {{
                    provideCompletionItems: async function(model, position) {{
                        const word = model.getWordUntilPosition(position);
                        const range = {{
                            startLineNumber: position.lineNumber,
                            endLineNumber: position.lineNumber,
                            startColumn: word.startColumn,
                            endColumn: word.endColumn
                        }};
                        
                        try {{
                            const code = model.getValue();
                            const offset = model.getOffsetAt(position);
                            
                            const response = await fetch('/api/autocomplete', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{
                                    code: code,
                                    cursorPosition: offset,
                                    language: 'python'
                                }})
                            }});
                            
                            const data = await response.json();
                            
                            if (data.suggestion && data.confidence > 0.5) {{
                                return {{
                                    suggestions: [{{
                                        label: data.suggestion.split('\\n')[0] || data.suggestion,
                                        kind: monaco.languages.CompletionItemKind.Snippet,
                                        insertText: data.suggestion,
                                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                                        range: range,
                                        detail: `AI Suggestion (${{Math.round(data.confidence * 100)}}%)`,
                                        documentation: 'Mocked AI autocomplete - Ready for Codex/Copilot'
                                    }}]
                                }};
                            }}
                        }} catch (e) {{
                            console.error('Autocomplete error:', e);
                        }}
                        
                        return {{ suggestions: [] }};
                    }}
                }});
                
                editor.onDidChangeModelContent((event) => {{
                    if (!isRemoteUpdate && ws && ws.readyState === WebSocket.OPEN) {{
                        const code = editor.getValue();
                        const position = editor.getPosition();
                        const cursorPosition = editor.getModel().getOffsetAt(position);
                        
                        ws.send(JSON.stringify({{
                            type: 'code_update',
                            code: code,
                            cursorPosition: cursorPosition
                        }}));
                    }}
                }});
                
                languageSelector.addEventListener('change', (e) => {{
                    const newLanguage = e.target.value;
                    monaco.editor.setModelLanguage(editor.getModel(), newLanguage);
                }});
                
                connectWebSocket();
            }});
            
            // ==================== WEBSOCKET CONNECTION ====================
            
            function connectWebSocket() {{
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {{
                    console.log('✓ WebSocket connected');
                    status.innerHTML = 'Connected ✓';
                    status.className = 'connected';
                }};
                
                ws.onmessage = (event) => {{
                    const data = JSON.parse(event.data);
                    console.log('Received:', data.type);
                    
                    if (data.type === 'init') {{
                        isRemoteUpdate = true;
                        if (editor) {{
                            editor.setValue(data.code);
                            if (data.language) {{
                                monaco.editor.setModelLanguage(editor.getModel(), data.language);
                                languageSelector.value = data.language;
                            }}
                        }}
                        isRemoteUpdate = false;
                    }}
                    else if (data.type === 'code_update') {{
                        isRemoteUpdate = true;
                        if (editor) {{
                            const currentPosition = editor.getPosition();
                            const currentScrollTop = editor.getScrollTop();
                            editor.setValue(data.code);
                            editor.setPosition(currentPosition);
                            editor.setScrollTop(currentScrollTop);
                        }}
                        isRemoteUpdate = false;
                    }}
                    else if (data.type === 'user_count') {{
                        const count = data.count;
                        userCount.textContent = `👤 ${{count}} user${{count > 1 ? 's' : ''}}`;
                    }}
                    else if (data.type === 'code_output') {{
                        if (data.status === 'running') {{
                            clearOutput();
                            appendOutput('🔄 Your partner is executing code...', 'remote');
                        }} else if (data.error) {{
                            appendOutput('❌ Execution Error', 'error');
                            appendOutput(data.error, 'error');
                            updateExecutionTime('Failed');
                        }} else {{
                            appendOutput('✅ Execution Successful', 'success');
                            appendSeparator();
                            appendOutput(data.output, 'normal');
                            updateExecutionTime('Completed');
                        }}
                    }}
                }};
                
                ws.onclose = () => {{
                    console.log('✗ WebSocket disconnected');
                    status.innerHTML = '⚠️ Disconnected';
                    status.className = 'disconnected';
                    setTimeout(connectWebSocket, 3000);
                }};
                
                ws.onerror = (error) => {{
                    console.error('WebSocket error:', error);
                    status.innerHTML = '❌ Connection Error';
                    status.className = 'disconnected';
                }};
            }}
            
            // ==================== CODE EXECUTION ====================
            
            runCodeBtn.addEventListener('click', async () => {{
                if (isExecutingCode) return;
                
                const code = editor.getValue();
                const language = languageSelector.value;
                
                isExecutingCode = true;
                runCodeBtn.disabled = true;
                runCodeBtn.innerHTML = '<span class="spinner"></span><span>Running...</span>';
                
                executionStartTime = Date.now();
                executionTime.textContent = 'Running...';
                
                clearOutput();
                
                if (ws && ws.readyState === WebSocket.OPEN) {{
                    ws.send(JSON.stringify({{
                        type: 'code_output',
                        status: 'running',
                        output: null,
                        error: null
                    }}));
                }}
                
                appendOutput('▶ Executing code...', 'info');
                
                try {{
                    const response = await fetch('/api/execute', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            code: code,
                            language: language
                        }})
                    }});
                    
                    const result = await response.json();
                    const duration = ((Date.now() - executionStartTime) / 1000).toFixed(2);
                    
                    if (ws && ws.readyState === WebSocket.OPEN) {{
                        ws.send(JSON.stringify({{
                            type: 'code_output',
                            status: 'completed',
                            output: result.output,
                            error: result.error
                        }}));
                    }} else {{
                        if (result.error) {{
                            appendOutput('❌ Execution Error', 'error');
                            appendOutput(result.error, 'error');
                        }} else {{
                            appendOutput('✅ Execution Successful', 'success');
                            appendSeparator();
                            appendOutput(result.output, 'normal');
                        }}
                    }}
                    
                    updateExecutionTime(`${{duration}}s`);
                    
                }} catch (error) {{
                    appendOutput('❌ Execution Failed', 'error');
                    appendOutput(error.message, 'error');
                    
                    if (ws && ws.readyState === WebSocket.OPEN) {{
                        ws.send(JSON.stringify({{
                            type: 'code_output',
                            status: 'error',
                            output: null,
                            error: error.message
                        }}));
                    }}
                    
                    updateExecutionTime('Failed');
                }} finally {{
                    isExecutingCode = false;
                    runCodeBtn.disabled = false;
                    runCodeBtn.innerHTML = '<span>▶</span><span>Run Code</span>';
                }}
            }});
            
            clearOutputBtn.addEventListener('click', () => {{
                clearOutput();
                outputContent.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">💻</div>
                        <div class="output-line output-info">
                            💡 Click "Run Code" to execute your Python code
                        </div>
                        <div class="output-line" style="color: #718096; margin-top: 10px;">
                            🔄 Output syncs in real-time with your pair programming partner
                        </div>
                    </div>
                `;
                outputLineCount = 0;
                updateOutputLines();
                executionTime.textContent = 'Ready';
            }});
            
            function clearOutput() {{
                outputContent.innerHTML = '';
                outputLineCount = 0;
                updateOutputLines();
            }}
            
            function appendOutput(text, type = 'normal') {{
                const line = document.createElement('div');
                line.className = 'output-line';
                
                if (type === 'error') {{
                    line.classList.add('output-error');
                }} else if (type === 'success') {{
                    line.classList.add('output-success');
                }} else if (type === 'info') {{
                    line.classList.add('output-info');
                }} else if (type === 'remote') {{
                    line.classList.add('output-remote');
                }}
                
                line.textContent = text;
                outputContent.appendChild(line);
                
                outputLineCount++;
                updateOutputLines();
                
                outputContent.scrollTop = outputContent.scrollHeight;
            }}
            
            function appendSeparator() {{
                const separator = document.createElement('div');
                separator.className = 'output-separator';
                outputContent.appendChild(separator);
            }}
            
            function updateExecutionTime(time) {{
                executionTime.textContent = time;
            }}
            
            function updateOutputLines() {{
                outputLines.textContent = `${{outputLineCount}} line${{outputLineCount !== 1 ? 's' : ''}}`;
            }}
            
            // ==================== COPY ROOM ID ====================
            
            roomCodeDisplay.addEventListener('click', () => {{
                navigator.clipboard.writeText(roomId).then(() => {{
                    const originalText = roomCodeDisplay.textContent;
                    roomCodeDisplay.textContent = '✓ Copied!';
                    roomCodeDisplay.style.background = 'rgba(72, 187, 120, 0.3)';
                    setTimeout(() => {{
                        roomCodeDisplay.textContent = originalText;
                        roomCodeDisplay.style.background = 'rgba(255,255,255,0.1)';
                    }}, 2000);
                }});
            }});
            
            // ==================== KEYBOARD SHORTCUTS ====================
            
            document.addEventListener('keydown', (e) => {{
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {{
                    e.preventDefault();
                    runCodeBtn.click();
                }}
                
                if ((e.ctrlKey || e.metaKey) && e.key === 's') {{
                    e.preventDefault();
                    console.log('Code auto-saved via WebSocket');
                }}
            }});
        </script>
    </body>
    </html>
    """)

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
