# 🤖 Recursive AI Executor (RAIE)

An intelligent Python code generation and execution platform that learns from failures and progressively improves code quality through recursive AI-powered debugging.

## ✨ Features

### 🧠 Intelligent Retry Logic
- **Progressive Learning**: Each failed attempt informs the next generation cycle
- **Error Pattern Recognition**: Automatically categorizes and learns from different error types
- **Adaptive System Prompts**: AI prompts become more sophisticated with each retry
- **Success Rate Tracking**: Monitor improvement over time

### 🔍 Advanced Error Analysis
- **Automatic Error Categorization**: Syntax, Import, Name, Type, Index, Key, and Indentation errors
- **Context-Aware Suggestions**: Tailored recommendations based on error patterns
- **Line Number Extraction**: Pinpoint exact error locations
- **Cumulative Learning**: Builds knowledge from all previous attempts

### 💻 Code Execution Engine
- **Sandboxed Execution**: Safe code execution in temporary files
- **Timeout Protection**: Prevents infinite loops with 15-second timeout
- **Comprehensive Error Reporting**: Detailed stdout/stderr capture
- **Real-time Status Updates**: Live progress tracking during execution

### 📊 Enhanced Analytics
- **Execution History**: Complete record of all code generation sessions
- **Learning Insights**: Visual indicators of when AI learning is applied
- **Performance Metrics**: Success rates and attempt statistics
- **Detailed Logs**: Comprehensive debugging information for each attempt

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- Mistral AI API key

### Setup

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd raie
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   MISTRAL_API_KEY=your_mistral_api_key_here
   ```
   
   Alternatively, you can enter the API key directly in the web interface.

4. **Run the application**
   ```bash
   streamlit run raie.py
   ```

5. **Access the web interface**
   
   Open your browser and navigate to `http://localhost:8501`

## 🎯 Usage

### Basic Workflow

1. **Enter Your Programming Task**
   - Describe what you want the code to do
   - Be specific about requirements and expected behavior
   - Example: "Create a function to find prime numbers up to n=100 and display them"

2. **Configure Settings** (Optional)
   - Adjust maximum retry attempts (1-10)
   - Enable/disable learning context display
   - Monitor success rates and metrics

3. **Generate & Execute**
   - Click "🚀 Generate & Execute"
   - Watch the AI progressively improve code through multiple attempts
   - View real-time error analysis and learning insights

4. **Review Results**
   - Examine generated code and execution output
   - Download successful code for later use
   - Analyze execution logs for debugging insights

### Example Prompts

```
✅ Good Prompts:
- "Create a password generator with customizable length and character sets"
- "Build a CSV file reader that handles missing values and calculates statistics"
- "Write a web scraper for extracting product prices from HTML"
- "Generate a simple calculator with error handling for division by zero"

❌ Avoid:
- Vague requests: "write some code"
- Requiring external APIs without credentials
- Tasks needing non-standard libraries (RAIE uses only Python standard library)
```

## 🏗️ Architecture

### Core Components

#### 🔧 ErrorAnalyzer
- **Purpose**: Categorizes and analyzes execution errors
- **Key Methods**:
  - `categorize_error()`: Classifies error types and extracts metadata
  - `build_learning_context()`: Creates cumulative learning from all attempts

#### 🤖 MistralAIClient
- **Purpose**: Handles AI code generation with progressive intelligence
- **Key Methods**:
  - `generate_code()`: Creates code with attempt-aware prompting
  - `_build_system_prompt()`: Constructs increasingly sophisticated system prompts
  - `_clean_generated_code()`: Removes markdown artifacts from generated code

#### ⚡ CodeExecutor
- **Purpose**: Safely executes Python code in sandboxed environment
- **Key Methods**:
  - `execute_python_code()`: Runs code with timeout and error capture

### Learning Progression

```
Attempt 1: Basic code generation
    ↓
Attempt 2-3: Debugging mode with error analysis
    ↓
Attempt 4+: Expert recovery mode with complete rewrites
```

## 🔧 Configuration

### Environment Variables
```env
MISTRAL_API_KEY=your_api_key_here    # Required: Mistral AI API key
```

### Runtime Settings
- **Max Retry Attempts**: 1-10 (default: 5)
- **Show Learning Context**: Display AI learning insights
- **Success Rate Tracking**: Monitor performance metrics

## 📊 Error Categories

RAIE automatically recognizes and learns from these error types:

| Category | Examples | AI Learning Response |
|----------|----------|---------------------|
| **Syntax** | Invalid syntax, unexpected EOF | Enhanced syntax checking |
| **Import** | ModuleNotFoundError | Standard library alternatives |
| **Name** | Undefined variables | Variable definition validation |
| **Type** | Wrong argument counts | Type checking and validation |
| **Index** | List index out of range | Bounds checking |
| **Key** | Dictionary key errors | Key existence validation |
| **Indentation** | Inconsistent spacing | Formatting corrections |

## 🔒 Security Features

- **Sandboxed Execution**: Code runs in temporary files with limited permissions
- **Timeout Protection**: 15-second execution limit prevents runaway processes
- **No External Dependencies**: Uses only Python standard library for safety
- **Input Validation**: Comprehensive error handling throughout the application

## 🤝 Contributing

### Code Structure
```
raie.py
├── ErrorAnalyzer        # Error categorization and learning
├── MistralAIClient     # AI code generation
├── CodeExecutor        # Safe code execution
└── main()              # Streamlit interface
```

### Development Guidelines
- Follow Python PEP 8 style guidelines
- Add comprehensive error handling
- Include docstrings for all classes and methods
- Test edge cases and error conditions

## 📈 Performance Tips

### For Better Results
- **Be Specific**: Detailed prompts generate better code
- **Include Context**: Mention expected inputs, outputs, and constraints
- **Error Tolerance**: Let RAIE learn from failures - don't stop at first error
- **Review Logs**: Use execution analytics to understand AI learning patterns

### Troubleshooting
- **API Errors**: Verify Mistral AI API key and network connectivity
- **Execution Timeouts**: Simplify complex algorithms or increase timeout
- **Memory Issues**: Restart application if session state becomes corrupted

## 📄 License

This project is open source. Please check the license file for specific terms.

## 🆘 Support

If you encounter issues:

1. Check the execution logs for detailed error information
2. Verify your Mistral AI API key is valid
3. Ensure all dependencies are installed correctly
4. Review the troubleshooting section above

## 🔄 Version History

### Current Features
- ✅ Recursive AI-powered code generation
- ✅ Progressive error learning
- ✅ Comprehensive execution analytics
- ✅ Real-time status updates
- ✅ Code download functionality

### Roadmap
- 🔄 Support for additional AI models
- 🔄 Custom error pattern training
- 🔄 Code performance optimization suggestions
- 🔄 Integration with version control systems

---

**Built with ❤️ and powered by AI intelligence that gets smarter with every failure!**
