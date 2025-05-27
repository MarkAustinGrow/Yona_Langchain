# Yona MCP Server Installation Guide

## 🚀 **Step-by-Step Installation for Linode Server**

### **1. Pull Latest Changes**
```bash
cd /opt/yona-langchain
git pull origin master
```

### **2. Upgrade pip and Install Core Dependencies**
```bash
pip install --upgrade pip setuptools wheel
```

### **3. Install Dependencies Manually (Recommended)**
Install packages individually to isolate any issues:

```bash
# Core web server
pip install "fastapi>=0.110.0"
pip install "uvicorn>=0.27.0"

# Cryptography
pip install "cryptography>=39.0.0,<42.0"

# LangChain ecosystem (in order)
pip install langchain==0.1.20
pip install langchain-core==0.1.53
pip install langchain-community==0.0.38
pip install langsmith==0.1.27
pip install langchain-mcp==0.1.0

# Core Yona dependencies
pip install "openai>=1.17.0"
pip install "pydantic>=1.10,<2.0"
pip install supabase>=2.3.0
pip install "python-dotenv>=1.0.0"
```

### **4. Alternative: Install from requirements.txt**
```bash
pip install -r requirements.txt
```

### **5. Verify Installation**
```bash
pip check
```
Should show: "No broken requirements found."

### **6. Test Yona Functionality**
```bash
python test_yona_mcp_server.py
```

Expected results:
- ✅ Environment Setup: PASSED
- ✅ Tool Imports: PASSED  
- ✅ MCP Toolkit Compatibility: PASSED
- ✅ MCP Server Startup: PASSED

### **7. Run Yona MCP Server**
```bash
# HTTP API (recommended for Coraliser)
python yona_openai_wrapper.py
```

Server should start on `http://localhost:8002`

### **8. Create Lock File (After Success)**
```bash
pip freeze > requirements.lock.txt
```

## 🔧 **Troubleshooting**

### **If LangChain Import Fails**
```bash
pip uninstall langchain langchain-core langchain-community
pip install langchain==0.1.20 langchain-core==0.1.53 langchain-community==0.0.38
```

### **If MCP Packages Missing**
```bash
pip install langchain-mcp==0.1.0
pip install mcp>=1.7.0
```

### **If FastAPI Missing**
```bash
pip install fastapi>=0.110.0 uvicorn>=0.27.0
```

## ✅ **Success Indicators**

1. **pip check** returns no broken requirements
2. **python test_yona_mcp_server.py** shows 4/4 tests passed
3. **python yona_openai_wrapper.py** starts without errors
4. Server responds at `http://localhost:8002/health`

## 📦 **Final Package Versions**

After successful installation, your environment should have:
- langchain==0.1.20
- langchain-core==0.1.53
- langchain-community==0.0.38
- langsmith==0.1.27
- langchain-mcp==0.1.0
- fastapi>=0.110.0
- uvicorn>=0.27.0
- openai>=1.17.0
- pydantic>=1.10,<2.0
