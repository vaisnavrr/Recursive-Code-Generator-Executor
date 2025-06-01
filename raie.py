import streamlit as st
import requests
import subprocess
import tempfile
import os
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
try:
    st.set_page_config(
        page_title="Recursive AI Executor (RAIE)",
        page_icon="🤖",
        layout="wide"
    )
except Exception as e:
    # Page config already set, continue
    pass

# Initialize session state
if 'execution_history' not in st.session_state:
    st.session_state.execution_history = []
if 'current_attempt' not in st.session_state:
    st.session_state.current_attempt = 0
if 'generated_code' not in st.session_state:
    st.session_state.generated_code = ""
if 'execution_logs' not in st.session_state:
    st.session_state.execution_logs = []
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'knowledge_base' not in st.session_state:
    st.session_state.knowledge_base = []

class ErrorAnalyzer:
    """Analyzes errors and builds knowledge for retries"""
    
    @staticmethod
    def categorize_error(stderr: str) -> Dict[str, any]:
        """Categorize error type and extract key information"""
        error_info = {
            "category": "unknown",
            "specific_issue": "",
            "line_number": None,
            "missing_imports": [],
            "syntax_issues": [],
            "runtime_issues": [],
            "suggestions": []
        }
        
        if not stderr:
            return error_info
            
        stderr_lower = stderr.lower()
        
        # Syntax errors
        if "syntaxerror" in stderr_lower:
            error_info["category"] = "syntax"
            if "invalid syntax" in stderr_lower:
                error_info["specific_issue"] = "invalid_syntax"
                error_info["suggestions"].append("Check parentheses, brackets, and indentation")
            elif "unexpected eof" in stderr_lower:
                error_info["specific_issue"] = "unexpected_eof"
                error_info["suggestions"].append("Missing closing brackets or incomplete statements")
        
        # Import errors
        elif "modulenotfounderror" in stderr_lower or "importerror" in stderr_lower:
            error_info["category"] = "import"
            # Extract module name
            import_match = re.search(r"no module named '([^']+)'", stderr_lower)
            if import_match:
                missing_module = import_match.group(1)
                error_info["missing_imports"].append(missing_module)
                error_info["suggestions"].append(f"Add import for {missing_module} or use standard library alternative")
        
        # Name errors
        elif "nameerror" in stderr_lower:
            error_info["category"] = "name"
            name_match = re.search(r"name '([^']+)' is not defined", stderr_lower)
            if name_match:
                undefined_name = name_match.group(1)
                error_info["specific_issue"] = f"undefined_variable: {undefined_name}"
                error_info["suggestions"].append(f"Define variable '{undefined_name}' before using it")
        
        # Type errors
        elif "typeerror" in stderr_lower:
            error_info["category"] = "type"
            if "takes" in stderr_lower and "positional argument" in stderr_lower:
                error_info["specific_issue"] = "wrong_arguments"
                error_info["suggestions"].append("Check function arguments and their count")
            elif "unsupported operand" in stderr_lower:
                error_info["specific_issue"] = "incompatible_types"
                error_info["suggestions"].append("Check data types in operations")
        
        # Index/Key errors
        elif "indexerror" in stderr_lower:
            error_info["category"] = "index"
            error_info["suggestions"].append("Check list/array bounds before accessing")
        elif "keyerror" in stderr_lower:
            error_info["category"] = "key"
            error_info["suggestions"].append("Check if dictionary key exists before accessing")
        
        # Indentation errors
        elif "indentationerror" in stderr_lower:
            error_info["category"] = "indentation"
            error_info["suggestions"].append("Fix indentation - use consistent spaces or tabs")
        
        # Extract line number if present
        line_match = re.search(r"line (\d+)", stderr)
        if line_match:
            error_info["line_number"] = int(line_match.group(1))
        
        return error_info
    
    @staticmethod
    def build_learning_context(all_attempts: List[Dict]) -> str:
        """Build cumulative learning context from all previous attempts"""
        if not all_attempts:
            return ""
            
        learning_context = "\n=== LEARNING FROM PREVIOUS ATTEMPTS ===\n"
        
        # Track patterns
        error_patterns = {}
        successful_patterns = []
        
        for i, attempt in enumerate(all_attempts):
            if attempt.get('success'):
                successful_patterns.append(f"Attempt {i+1} succeeded")
            else:
                error_info = ErrorAnalyzer.categorize_error(attempt.get('stderr', ''))
                category = error_info['category']
                if category not in error_patterns:
                    error_patterns[category] = []
                error_patterns[category].append({
                    'attempt': i+1,
                    'issue': error_info['specific_issue'],
                    'suggestions': error_info['suggestions']
                })
        
        # Add pattern analysis
        if error_patterns:
            learning_context += "\nREPEATED ERROR PATTERNS DETECTED:\n"
            for category, errors in error_patterns.items():
                if len(errors) > 1:
                    learning_context += f"- {category.upper()} errors occurred {len(errors)} times\n"
                    for error in errors[-2:]:  # Show last 2 instances
                        learning_context += f"  * Attempt {error['attempt']}: {error['issue']}\n"
                        for suggestion in error['suggestions']:
                            learning_context += f"    - {suggestion}\n"
        
        # Add specific improvement strategies
        learning_context += "\nIMPROVEMENT STRATEGIES:\n"
        if 'import' in error_patterns:
            learning_context += "- Use only standard library imports (avoid external packages)\n"
        if 'syntax' in error_patterns:
            learning_context += "- Double-check syntax, especially brackets and indentation\n"
        if 'name' in error_patterns:
            learning_context += "- Ensure all variables are defined before use\n"
        if 'type' in error_patterns:
            learning_context += "- Add type checking and validation\n"
            
        return learning_context

class MistralAIClient:
    """Enhanced client with retry logic"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.mistral.ai/v1/chat/completions"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_code(self, prompt: str, attempt_number: int = 1, 
                     previous_attempts: List[Dict] = None) -> str:
        """Generate code with progressive intelligence"""
        
        # Base system prompt that evolves with attempts
        system_prompt = self._build_system_prompt(attempt_number, previous_attempts)
        
        # Build user prompt with learning context
        user_prompt = self._build_user_prompt(prompt, attempt_number, previous_attempts)
        
        payload = {
            "model": "mistral-large-latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1500,  # Increased for more detailed code
            "temperature": max(0.1, 0.3 - (attempt_number * 0.05))  # Reduce randomness with attempts
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            code = result['choices'][0]['message']['content'].strip()
            
            # Clean the code (remove markdown if present)
            code = self._clean_generated_code(code)
            
            return code
            
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None
    
    def _build_system_prompt(self, attempt_number: int, previous_attempts: List[Dict]) -> str:
        """Build increasingly sophisticated system prompts"""
        
        base_prompt = """You are an expert Python programmer with strong debugging skills."""
        
        if attempt_number == 1:
            return base_prompt + """
            
Generate clean, working Python code based on the user's request.

Rules:
1. Use only Python standard library (no external packages)
2. Include all necessary imports
3. Add error handling and input validation
4. Include comments explaining the logic
5. Test your code mentally before outputting
6. Return ONLY executable Python code (no markdown formatting)"""
        
        elif attempt_number <= 3:
            return base_prompt + """
            
You are now in DEBUGGING MODE. Previous attempts have failed.

Critical Rules:
1. ANALYZE the previous failures carefully
2. Use ONLY Python standard library modules
3. Add comprehensive error handling with try-except blocks
4. Validate all inputs before processing
5. Use defensive programming practices
6. Add logging/print statements for debugging
7. Test edge cases in your mind
8. Return ONLY executable Python code (no markdown)

Focus on ROBUST, DEFENSIVE code that handles edge cases."""
        
        else:  # attempt_number > 3
            return base_prompt + """
            
You are now in EXPERT RECOVERY MODE. Multiple attempts have failed.

CRITICAL DEBUGGING PROTOCOL:
1. COMPLETELY REWRITE the approach if similar errors keep occurring
2. Use the SIMPLEST possible solution that works
3. Break complex problems into smaller, testable functions
4. Add extensive error handling and input validation
5. Use only built-in Python functions and standard library
6. Add debug prints to track execution flow
7. Consider alternative algorithms or approaches
8. Return ONLY executable Python code (no markdown)

PRIORITY: Working code over elegant code. Make it work first."""
    
    def _build_user_prompt(self, original_prompt: str, attempt_number: int, 
                                previous_attempts: List[Dict]) -> str:
        """Build user prompt with cumulative learning"""
        
        prompt = f"Original Task: {original_prompt}\n"
        
        if previous_attempts:
            # Add learning context
            learning_context = ErrorAnalyzer.build_learning_context(previous_attempts)
            prompt += learning_context
            
            # Add specific failure analysis for recent attempts
            prompt += f"\n=== ATTEMPT {attempt_number} FOCUS ===\n"
            
            if attempt_number <= 3:
                recent_attempt = previous_attempts[-1]
                if recent_attempt.get('stderr'):
                    error_info = ErrorAnalyzer.categorize_error(recent_attempt['stderr'])
                    prompt += f"Last error category: {error_info['category']}\n"
                    prompt += f"Specific issue: {error_info['specific_issue']}\n"
                    prompt += "Suggestions to fix:\n"
                    for suggestion in error_info['suggestions']:
                        prompt += f"- {suggestion}\n"
            else:
                # For later attempts, be more aggressive
                prompt += "CRITICAL: Multiple failures detected. Consider:\n"
                prompt += "- Completely different approach\n"
                prompt += "- Simpler algorithm\n"
                prompt += "- More basic implementation\n"
                prompt += "- Extensive error handling\n"
        
        prompt += f"\nGenerate working Python code for attempt {attempt_number}. "
        prompt += "Focus on CORRECTNESS over elegance."
        
        return prompt
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean generated code of markdown and other artifacts"""
        # Remove markdown code blocks
        code = re.sub(r'^```python\s*\n', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```\s*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```.*\n', '', code, flags=re.MULTILINE)
        
        # Remove leading/trailing whitespace
        code = code.strip()
        
        return code

class CodeExecutor:
    """Enhanced code executor with better error reporting"""
    
    @staticmethod
    def execute_python_code(code: str) -> Tuple[bool, str, str]:
        """Execute Python code with enhanced error reporting"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute with timeout
            process = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=15,  # Increased timeout
                cwd=tempfile.gettempdir()
            )
            
            # Clean up
            os.unlink(temp_file)
            
            success = process.returncode == 0
            stdout = process.stdout if process.stdout else ""
            stderr = process.stderr if process.stderr else ""
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            if 'temp_file' in locals():
                os.unlink(temp_file)
            return False, "", "Code execution timed out (>15 seconds)"
        except Exception as e:
            if 'temp_file' in locals():
                os.unlink(temp_file)
            return False, "", f"Execution error: {str(e)}"

def main():
    """Main application function"""
    try:
        st.title("🤖 Recursive AI Executor (RAIE)")
        st.markdown("Enhanced AI code generation with intelligent retry logic!")
        
        # Debug info
        st.write("Debug: App is loading...")
        
        # Sidebar
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # API Key handling
            api_key = os.getenv("MISTRAL_API_KEY")
            
            if api_key:
                st.success("✅ API Key loaded from environment")
                st.info(f"Using key: ...{api_key[-8:]}")
            else:
                st.warning("⚠️ No API key found in environment")
                api_key = st.text_input(
                    "Mistral AI API Key", 
                    type="password",
                    help="Enter your Mistral AI API key",
                    key="api_key_input"
                )
            
            # Configuration
            max_attempts = st.slider("Max Retry Attempts", min_value=1, max_value=10, value=5)
            show_learning = st.checkbox("Show Learning Context", value=True)
            
            if st.button("🗑️ Clear History"):
                for key in ['execution_history', 'current_attempt', 'generated_code', 
                           'execution_logs', 'knowledge_base']:
                    if key in st.session_state:
                        if 'history' in key or 'logs' in key or 'knowledge' in key:
                            st.session_state[key] = []
                        elif 'attempt' in key:
                            st.session_state[key] = 0
                        else:
                            st.session_state[key] = ""
                st.rerun()
        
        # Main interface
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.header("📝 Prompt Input")
            
            prompt = st.text_area(
                "Enter your programming task:",
                placeholder="e.g., Create a function to find prime numbers up to n=100 and display them",
                height=150,
                key="prompt_input"
            )
            
            # Button with unique key
            run_button = st.button(
                "🚀 Generate & Execute", 
                disabled=(st.session_state.get('is_running', False) or not api_key),
                key="run_button"
            )
            
            if run_button:
                if prompt and prompt.strip():
                    execute_recursive_ai(prompt, api_key, max_attempts, show_learning)
                else:
                    st.error("Please enter a prompt!")
            
            # Enhanced status
            if st.session_state.get('is_running', False):
                current_attempt = st.session_state.get('current_attempt', 0)
                st.info(f"🧠 Processing... Attempt {current_attempt}/{max_attempts}")
                if current_attempt > 1:
                    st.warning(f"🔍 Learning from {current_attempt - 1} previous failures")
            
            # Intelligence metrics
            execution_logs = st.session_state.get('execution_logs', [])
            if execution_logs:
                total_attempts = len(execution_logs)
                successful_attempts = sum(1 for log in execution_logs if log.get('success', False))
                if total_attempts > 0:
                    success_rate = (successful_attempts / total_attempts) * 100
                    st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col2:
            st.header("💻 Generated Code")
            
            generated_code = st.session_state.get('generated_code', '')
            if generated_code:
                st.code(generated_code, language="python")
                
                st.download_button(
                    label="📥 Download Code",
                    data=generated_code,
                    file_name=f"Code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                    mime="text/python",
                    key="download_code"
                )
            else:
                st.info("Generated code will appear here after running...")
        
        # Enhanced execution logs with learning insights
        execution_logs = st.session_state.get('execution_logs', [])
        if execution_logs:
            st.header("🧠 Execution Analysis")
            
            for i, log in enumerate(execution_logs):
                success = log.get('success', False)
                status = "✅ Success" if success else "❌ Failed"
                learning_indicator = "🧠 Learning Applied" if i > 0 else "🌱 Initial Attempt"
                
                with st.expander(f"Attempt {i + 1} - {status} - {learning_indicator}"):
                    
                    error_analysis = log.get('error_analysis')
                    if error_analysis:
                        st.subheader("🔍 Error Analysis:")
                        st.write(f"**Category:** {error_analysis.get('category', 'unknown')}")
                        st.write(f"**Issue:** {error_analysis.get('specific_issue', 'N/A')}")
                        suggestions = error_analysis.get('suggestions', [])
                        if suggestions:
                            st.write("**AI Suggestions:**")
                            for suggestion in suggestions:
                                st.write(f"- {suggestion}")
                    
                    stdout = log.get('stdout', '')
                    if stdout:
                        st.subheader("📤 Output:")
                        st.code(stdout, language="text")
                    
                    stderr = log.get('stderr', '')
                    if stderr:
                        st.subheader("⚠️ Errors:")
                        st.code(stderr, language="text")
                    
                    timestamp = log.get('timestamp', 'Unknown')
                    st.caption(f"Executed at: {timestamp}")
        
        # Execution history
        execution_history = st.session_state.get('execution_history', [])
        if execution_history:
            st.header("📚 Execution History")
            
            for i, entry in enumerate(reversed(execution_history)):
                prompt_preview = entry.get('prompt', '')[:50]
                with st.expander(f"Session {len(execution_history) - i}: {prompt_preview}..."):
                    st.write(f"**Prompt:** {entry.get('prompt', 'N/A')}")
                    st.write(f"**Attempts:** {entry.get('attempts', 0)}")
                    st.write(f"**Success:** {'✅ Yes' if entry.get('success', False) else '❌ No'}")
                    st.write(f"**Learning Applied:** {'Yes' if entry.get('learning_applied', False) else 'No'}")
                    st.write(f"**Timestamp:** {entry.get('timestamp', 'Unknown')}")
        
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.write("Please check the console for detailed error information.")
        import traceback
        st.code(traceback.format_exc())

def execute_recursive_ai(prompt: str, api_key: str, max_attempts: int, show_learning: bool):
    """Enhanced execution with progressive learning"""
    
    try:
        st.session_state.is_running = True
        st.session_state.current_attempt = 0
        st.session_state.execution_logs = []
        
        # Initialize AI client
        ai_client = MistralAIClient(api_key)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Track all attempts for learning
        all_attempts = []
        success = False  # Initialize success flag
        
        for attempt in range(max_attempts):
            st.session_state.current_attempt = attempt + 1
            progress = (attempt + 1) / max_attempts
            progress_bar.progress(progress)
            
            # Status updates
            if attempt == 0:
                status_text.text(f"🌱 Initial attempt: Generating code...")
            elif attempt == 1:
                status_text.text(f"🔍 Learning from failure: Analyzing and improving...")
            else:
                status_text.text(f"🧠 Advanced retry #{attempt + 1}: Applying accumulated knowledge...")
            
            # Generate code with progressive intelligence
            generated_code = ai_client.generate_code(
                prompt, 
                attempt_number=attempt + 1, 
                previous_attempts=all_attempts
            )
            
            if not generated_code:
                st.error("❌ Failed to generate code from AI")
                break
            
            st.session_state.generated_code = generated_code
            
            status_text.text(f"⚡ Executing code (attempt {attempt + 1})...")
            
            # Execute code
            success, stdout, stderr = CodeExecutor.execute_python_code(generated_code)
            
            # Analyze errors for learning
            error_analysis = ErrorAnalyzer.categorize_error(stderr) if stderr else None
            
            # Record attempt
            attempt_record = {
                "attempt": attempt + 1,
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
                "code": generated_code,
                "error_analysis": error_analysis,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            all_attempts.append(attempt_record)
            st.session_state.execution_logs.append(attempt_record)
            
            if success:
                status_text.text(f"✅ Code Execution succeeded on attempt {attempt + 1}!")
                break
            else:
                # Show learning progress
                if show_learning and error_analysis:
                    st.info(f"🔍 Detected {error_analysis['category']} error: {error_analysis['specific_issue']}")
                
                status_text.text(f"🧠 Learning from attempt {attempt + 1} failure...")
                time.sleep(0.5)  # Brief pause to show learning
        
        # Finalize
        st.session_state.is_running = False
        progress_bar.empty()
        
        if success:
            status_text.text("✅ Execution completed successfully!")
        else:
            status_text.text("❌ All retry attempts exhausted")
        
        # Record to history with enhanced metadata
        history_entry = {
            "prompt": prompt,
            "generated_code": st.session_state.generated_code,
            "attempts": st.session_state.current_attempt,
            "success": success,
            "logs": st.session_state.execution_logs.copy(),  # Create a copy
            "learning_applied": len(all_attempts) > 1,
            "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
        }
        
        st.session_state.execution_history.append(history_entry)
        
    except Exception as e:
        st.session_state.is_running = False
        st.error(f"Execution Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Critical Application Error: {str(e)}")
        st.write("**Debug Information:**")
        import traceback
        st.code(traceback.format_exc())
        st.write("**Please check:**")
        st.write("1. Python version compatibility")
        st.write("2. Required packages installed: streamlit, requests, python-dotenv")
        st.write("3. File permissions")
        st.write("4. Network connectivity")