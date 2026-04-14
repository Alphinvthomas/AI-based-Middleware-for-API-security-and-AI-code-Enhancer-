"""
API Analyzer Module - Multi-Language Support
Discovers and analyzes APIs in Python, Java, JavaScript/Node, Go, C#, and other backend projects
"""
import ast
import re
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum


class ProgrammingLanguage(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    GO = "go"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    RUST = "rust"
    KOTLIN = "kotlin"
    UNKNOWN = "unknown"


@dataclass
class APIParameter:
    """Represents an API parameter"""
    name: str
    type_hint: Optional[str]
    default_value: Optional[str]
    description: Optional[str]


@dataclass
class DiscoveredAPI:
    """Represents a discovered API"""
    name: str
    function_name: str
    file_path: str
    language: str
    http_method: str
    endpoint: str
    parameters: List[APIParameter]
    source_code: str
    return_type: Optional[str]
    docstring: Optional[str]
    framework: Optional[str]  # e.g., "FastAPI", "Flask", "Express", "Spring Boot"


class APIAnalyzer:
    """Analyze projects in multiple languages to discover APIs"""
    
    # File extension to language mapping
    LANGUAGE_MAP = {
        ".py": ProgrammingLanguage.PYTHON,
        ".js": ProgrammingLanguage.JAVASCRIPT,
        ".ts": ProgrammingLanguage.JAVASCRIPT,
        ".jsx": ProgrammingLanguage.JAVASCRIPT,
        ".tsx": ProgrammingLanguage.JAVASCRIPT,
        ".java": ProgrammingLanguage.JAVA,
        ".go": ProgrammingLanguage.GO,
        ".cs": ProgrammingLanguage.CSHARP,
        ".php": ProgrammingLanguage.PHP,
        ".rb": ProgrammingLanguage.RUBY,
        ".rs": ProgrammingLanguage.RUST,
        ".kt": ProgrammingLanguage.KOTLIN,
    }
    
    # Python API framework identifiers
    PYTHON_FRAMEWORKS = {
        "fastapi": ["@app.get", "@app.post", "@app.put", "@app.delete", "@app.patch"],
        "flask": ["@app.route", "@bp.route"],
        "django": ["path(", "re_path(", "url("],
    }
    
    # JavaScript/Node.js frameworks
    JS_FRAMEWORKS = {
        "express": ["app.get", "app.post", "app.put", "app.delete", "router.get", "router.post"],
        "fastify": ["fastify.get", "fastify.post", "fastify.put", "fastify.delete"],
        "hapi": ["server.route", "server.get", "server.post"],
        "koa": ["app.use", "router.get", "router.post"],
    }
    
    # Java frameworks
    JAVA_FRAMEWORKS = {
        "spring": ["@GetMapping", "@PostMapping", "@PutMapping", "@DeleteMapping", "@RequestMapping"],
        "jaxrs": ["@GET", "@POST", "@PUT", "@DELETE", "@Path"],
    }
    
    # Go frameworks
    GO_FRAMEWORKS = {
        "gin": ["r.GET", "r.POST", "r.PUT", "r.DELETE", "engine.GET"],
        "stdlib": ["http.HandleFunc", "mux.HandleFunc"],
    }
    
    # C# frameworks
    CSHARP_FRAMEWORKS = {
        "aspnet": ["[HttpGet]", "[HttpPost]", "[HttpPut]", "[HttpDelete]", "[ApiController]"],
    }
    
    HTTP_METHODS = {
        "GET": ["get", "retriev", "fetch", "list", "retrieve", "all", "one"],
        "POST": ["post", "create", "add", "submit", "new"],
        "PUT": ["put", "update", "modify", "edit", "set"],
        "DELETE": ["delete", "remove", "destroy", "drop"],
        "PATCH": ["patch", "partial", "update"],
    }
    
    def __init__(self):
        self.discovered_apis: List[DiscoveredAPI] = []
        self.file_contents: Dict[str, str] = {}
        self.language_stats: Dict[str, int] = {}
    
    def analyze_file(self, file_path: str, content: str) -> List[DiscoveredAPI]:
        """
        Analyze a file in any supported language for APIs
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of discovered APIs
        """
        self.file_contents[file_path] = content
        apis = []
        
        try:
            # Detect language
            language = self._detect_language(file_path)
            
            if language == ProgrammingLanguage.PYTHON:
                apis = self._analyze_python_file(file_path, content)
            elif language == ProgrammingLanguage.JAVASCRIPT:
                apis = self._analyze_javascript_file(file_path, content)
            elif language == ProgrammingLanguage.JAVA:
                apis = self._analyze_java_file(file_path, content)
            elif language == ProgrammingLanguage.GO:
                apis = self._analyze_go_file(file_path, content)
            elif language == ProgrammingLanguage.CSHARP:
                apis = self._analyze_csharp_file(file_path, content)
            elif language == ProgrammingLanguage.PHP:
                apis = self._analyze_php_file(file_path, content)
            elif language == ProgrammingLanguage.RUBY:
                apis = self._analyze_ruby_file(file_path, content)
            
            # Update language stats
            lang_name = language.value
            self.language_stats[lang_name] = self.language_stats.get(lang_name, 0) + 1
            
            self.discovered_apis.extend(apis)
        
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return apis
    
    def _detect_language(self, file_path: str) -> ProgrammingLanguage:
        """Detect programming language from file extension"""
        for ext, lang in self.LANGUAGE_MAP.items():
            if file_path.lower().endswith(ext):
                return lang
        return ProgrammingLanguage.UNKNOWN
    
    # ========================================================================
    # Python Analysis
    # ========================================================================
    
    def _analyze_python_file(self, file_path: str, content: str) -> List[DiscoveredAPI]:
        """Analyze Python file for APIs"""
        apis = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    api = self._analyze_python_function(node, file_path, content)
                    if api:
                        apis.append(api)
        
        except SyntaxError:
            pass
        
        return apis
    
    def _analyze_python_function(self, func_node: ast.FunctionDef, file_path: str, content: str) -> Optional[DiscoveredAPI]:
        """Analyze a Python function to determine if it's an API"""
        decorators = self._get_python_decorators(func_node)
        
        is_api = False
        http_method = "GET"
        endpoint = None
        framework = None
        
        for decorator in decorators:
            # FastAPI detection
            if any(d in decorator for d in ["app.get", "app.post", "app.put", "app.delete", "app.patch"]):
                is_api = True
                framework = "FastAPI"
                endpoint = self._extract_endpoint_from_python_decorator(decorator)
                http_method = self._extract_http_method_from_decorator(decorator)
            
            # Flask detection
            elif "app.route" in decorator or "bp.route" in decorator:
                is_api = True
                framework = "Flask"
                endpoint = self._extract_endpoint_from_python_decorator(decorator)
                method_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", decorator)
                if method_match:
                    methods = method_match.group(1).upper()
                    http_method = methods.split(",")[0].strip("'\"").strip()
        
        if not is_api and self._infer_http_method(func_node.name):
            is_api = True
            http_method = self._infer_http_method(func_node.name)
            endpoint = f"/{func_node.name}"
        
        if not is_api:
            return None
        
        if not endpoint:
            endpoint = f"/{func_node.name}"
        
        parameters = self._extract_python_parameters(func_node)
        source_code = self._extract_function_source(func_node, content)
        docstring = ast.get_docstring(func_node)
        
        return_type = None
        if func_node.returns:
            return_type = ast.unparse(func_node.returns)
        
        return DiscoveredAPI(
            name=func_node.name,
            function_name=func_node.name,
            file_path=file_path,
            language="Python",
            http_method=http_method,
            endpoint=endpoint,
            parameters=parameters,
            source_code=source_code,
            return_type=return_type,
            docstring=docstring,
            framework=framework
        )
    
    def _get_python_decorators(self, func_node: ast.FunctionDef) -> List[str]:
        """Extract decorator names and arguments"""
        decorators = []
        for decorator in func_node.decorator_list:
            try:
                decorators.append(ast.unparse(decorator))
            except:
                pass
        return decorators
    
    def _extract_python_parameters(self, func_node: ast.FunctionDef) -> List[APIParameter]:
        """Extract parameters from Python function signature"""
        parameters = []
        
        for arg in func_node.args.args:
            param_name = arg.arg
            if param_name == "self":
                continue
            
            type_hint = None
            if arg.annotation:
                try:
                    type_hint = ast.unparse(arg.annotation)
                except:
                    type_hint = None
            
            parameters.append(APIParameter(
                name=param_name,
                type_hint=type_hint,
                default_value=None,
                description=None
            ))
        
        return parameters
    
    # ========================================================================
    # JavaScript/Node.js Analysis
    # ========================================================================
    
    def _analyze_javascript_file(self, file_path: str, content: str) -> List[DiscoveredAPI]:
        """Analyze JavaScript/Node.js file for APIs"""
        apis = []
        
        # Express.js routes
        express_patterns = [
            r"app\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
            r"router\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
        ]
        
        # Fastify routes
        fastify_patterns = [r"fastify\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"]
        
        # Search for all routes
        for pattern in express_patterns + fastify_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                http_method = match.group(1).upper()
                endpoint = match.group(2)
                
                # Extract surrounding context for source code
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(content), match.end() + 300)
                source_code = content[start_pos:end_pos]
                
                # Extract function/handler name
                handler_name = f"{http_method.lower()}_{endpoint.replace('/', '_')}"
                
                api = DiscoveredAPI(
                    name=handler_name,
                    function_name=handler_name,
                    file_path=file_path,
                    language="JavaScript",
                    http_method=http_method,
                    endpoint=endpoint,
                    parameters=[],
                    source_code=source_code,
                    return_type=None,
                    docstring=None,
                    framework="Express" if "app" in pattern or "router" in pattern else "Fastify"
                )
                apis.append(api)
        
        return apis
    
    # ========================================================================
    # Java Analysis
    # ========================================================================
    
    def _analyze_java_file(self, file_path: str, content: str) -> List[DiscoveredAPI]:
        """Analyze Java file for APIs"""
        apis = []
        
        # Spring Boot annotations
        spring_patterns = [
            (r"@GetMapping\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)", "GET"),
            (r"@PostMapping\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)", "POST"),
            (r"@PutMapping\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)", "PUT"),
            (r"@DeleteMapping\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)", "DELETE"),
            (r"@PatchMapping\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)", "PATCH"),
            (r"@RequestMapping\s*\(\s*value\s*=\s*['\"]([^'\"]+)['\"],\s*method\s*=\s*RequestMethod\.(\w+)", "CUSTOM"),
        ]
        
        for pattern, method in spring_patterns:
            for match in re.finditer(pattern, content):
                if method == "CUSTOM":
                    endpoint = match.group(1)
                    http_method = match.group(2)
                else:
                    endpoint = match.group(1) if match.group(1) else "/"
                    http_method = method
                
                # Extract method name from context
                method_match = re.search(r"public\s+(?:\w+\s+)?(\w+)\s*\(", content[max(0, match.start() - 200):match.start() + 100])
                method_name = method_match.group(1) if method_match else f"{method.lower()}_handler"
                
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(content), match.end() + 300)
                source_code = content[start_pos:end_pos]
                
                api = DiscoveredAPI(
                    name=method_name,
                    function_name=method_name,
                    file_path=file_path,
                    language="Java",
                    http_method=http_method,
                    endpoint=f"/{endpoint}" if endpoint and not endpoint.startswith("/") else endpoint,
                    parameters=[],
                    source_code=source_code,
                    return_type=None,
                    docstring=None,
                    framework="Spring Boot"
                )
                apis.append(api)
        
        return apis
    
    # ========================================================================
    # Go Analysis
    # ========================================================================
    
    def _analyze_go_file(self, file_path: str, content: str) -> List[DiscoveredAPI]:
        """Analyze Go file for APIs"""
        apis = []
        
        # Gin framework patterns
        gin_patterns = [
            (r"r\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*['\"]([^'\"]+)['\"]", "gin"),
            (r"engine\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*['\"]([^'\"]+)['\"]", "gin"),
        ]
        
        # Standard library patterns
        stdlib_patterns = [
            (r"http\.HandleFunc\s*\(\s*['\"]([^'\"]+)['\"],", "http"),
            (r"mux\.HandleFunc\s*\(\s*['\"]([^'\"]+)['\"],", "gorilla"),
        ]
        
        for pattern, framework in gin_patterns + stdlib_patterns:
            for match in re.finditer(pattern, content):
                if framework == "gin":
                    http_method = match.group(1)
                    endpoint = match.group(2)
                else:
                    endpoint = match.group(1)
                    http_method = "GET"  # Default for stdlib
                
                handler_name = f"{http_method.lower()}_{endpoint.replace('/', '_')}"
                
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(content), match.end() + 300)
                source_code = content[start_pos:end_pos]
                
                api = DiscoveredAPI(
                    name=handler_name,
                    function_name=handler_name,
                    file_path=file_path,
                    language="Go",
                    http_method=http_method,
                    endpoint=endpoint,
                    parameters=[],
                    source_code=source_code,
                    return_type=None,
                    docstring=None,
                    framework=framework.capitalize()
                )
                apis.append(api)
        
        return apis
    
    # ========================================================================
    # C# Analysis
    # ========================================================================
    
    def _analyze_csharp_file(self, file_path: str, content: str) -> List[DiscoveredAPI]:
        """Analyze C# file for APIs"""
        apis = []
        
        # ASP.NET Core patterns
        patterns = [
            (r"\[HttpGet\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)\]", "GET"),
            (r"\[HttpPost\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)\]", "POST"),
            (r"\[HttpPut\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)\]", "PUT"),
            (r"\[HttpDelete\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)\]", "DELETE"),
            (r"\[HttpPatch\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)\]", "PATCH"),
        ]
        
        for pattern, method in patterns:
            for match in re.finditer(pattern, content):
                endpoint = match.group(1) if match.group(1) else "/"
                
                # Extract method name from context
                method_match = re.search(r"public\s+(?:\w+\s+)?(\w+)\s*\(", content[max(0, match.start()):match.start() + 200])
                method_name = method_match.group(1) if method_match else f"{method.lower()}_handler"
                
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(content), match.end() + 300)
                source_code = content[start_pos:end_pos]
                
                api = DiscoveredAPI(
                    name=method_name,
                    function_name=method_name,
                    file_path=file_path,
                    language="C#",
                    http_method=method,
                    endpoint=f"/{endpoint}" if endpoint and not endpoint.startswith("/") else endpoint,
                    parameters=[],
                    source_code=source_code,
                    return_type=None,
                    docstring=None,
                    framework="ASP.NET Core"
                )
                apis.append(api)
        
        return apis
    
    # ========================================================================
    # PHP Analysis
    # ========================================================================
    
    def _analyze_php_file(self, file_path: str, content: str) -> List[DiscoveredAPI]:
        """Analyze PHP file for APIs"""
        apis = []
        
        # Laravel, Slim, and other PHP frameworks
        patterns = [
            (r"\$app\->(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]", "slim"),
            (r"Route::(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]", "laravel"),
        ]
        
        for pattern, framework in patterns:
            for match in re.finditer(pattern, content):
                http_method = match.group(1).upper()
                endpoint = match.group(2)
                
                handler_name = f"{http_method.lower()}_{endpoint.replace('/', '_')}"
                
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(content), match.end() + 300)
                source_code = content[start_pos:end_pos]
                
                api = DiscoveredAPI(
                    name=handler_name,
                    function_name=handler_name,
                    file_path=file_path,
                    language="PHP",
                    http_method=http_method,
                    endpoint=endpoint,
                    parameters=[],
                    source_code=source_code,
                    return_type=None,
                    docstring=None,
                    framework=framework.capitalize()
                )
                apis.append(api)
        
        return apis
    
    # ========================================================================
    # Ruby Analysis
    # ========================================================================
    
    def _analyze_ruby_file(self, file_path: str, content: str) -> List[DiscoveredAPI]:
        """Analyze Ruby file for APIs"""
        apis = []
        
        # Rails and Sinatra patterns
        patterns = [
            (r"(get|post|put|delete|patch)\s+['\"]([^'\"]+)['\"]", "sinatra"),
            (r"resources\s+:\s*(\w+)", "rails"),
        ]
        
        for pattern, framework in patterns:
            for match in re.finditer(pattern, content):
                if framework == "rails":
                    endpoint = f"/{match.group(1)}"
                    http_method = "GET"
                else:
                    http_method = match.group(1).upper()
                    endpoint = match.group(2)
                
                handler_name = f"{http_method.lower()}_{endpoint.replace('/', '_')}"
                
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(content), match.end() + 300)
                source_code = content[start_pos:end_pos]
                
                api = DiscoveredAPI(
                    name=handler_name,
                    function_name=handler_name,
                    file_path=file_path,
                    language="Ruby",
                    http_method=http_method,
                    endpoint=endpoint,
                    parameters=[],
                    source_code=source_code,
                    return_type=None,
                    docstring=None,
                    framework=framework.capitalize()
                )
                apis.append(api)
        
        return apis
    
    def _extract_endpoint_from_python_decorator(self, decorator: str) -> Optional[str]:
        """Extract endpoint path from Python decorator"""
        match = re.search(r'["\'](/[^"\']*)["\']', decorator)
        if match:
            return match.group(1)
        return None
    
    def _extract_http_method_from_decorator(self, decorator: str) -> str:
        """Extract HTTP method from decorator"""
        decorator_lower = decorator.lower()
        if "get" in decorator_lower:
            return "GET"
        elif "post" in decorator_lower:
            return "POST"
        elif "put" in decorator_lower:
            return "PUT"
        elif "delete" in decorator_lower:
            return "DELETE"
        elif "patch" in decorator_lower:
            return "PATCH"
        return "GET"
    
    def _infer_http_method(self, function_name: str) -> Optional[str]:
        """Infer HTTP method from function name"""
        name_lower = function_name.lower()
        
        for method, keywords in self.HTTP_METHODS.items():
            if any(keyword in name_lower for keyword in keywords):
                return method
        
        return None
    
    def _extract_function_source(self, func_node: ast.FunctionDef, content: str) -> str:
        """Extract the source code of a Python function"""
        lines = content.split("\n")
        start_line = func_node.lineno - 1
        end_line = func_node.end_lineno if hasattr(func_node, 'end_lineno') else len(lines)
        
        source_lines = lines[start_line:end_line]
        return "\n".join(source_lines)
    
    def discover_apis_in_project(self, file_contents: Dict[str, str]) -> List[DiscoveredAPI]:
        """
        Discover APIs in entire project (all supported languages)
        
        Args:
            file_contents: Dict mapping file paths to file contents
            
        Returns:
            List of discovered APIs
        """
        self.discovered_apis = []
        self.language_stats = {}
        
        for file_path, content in file_contents.items():
            if content:
                # Check if file is a supported language
                language = self._detect_language(file_path)
                if language != ProgrammingLanguage.UNKNOWN:
                    self.analyze_file(file_path, content)
        
        return self.discovered_apis
    
    def get_api_summary(self) -> Dict:
        """Get summary of discovered APIs"""
        return {
            "total_apis": len(self.discovered_apis),
            "apis_by_method": self._group_by_method(),
            "apis_by_language": self._group_by_language(),
            "apis_by_framework": self._group_by_framework(),
            "apis_by_file": self._group_by_file(),
            "language_statistics": self.language_stats,
            "all_apis": [self._api_to_dict(api) for api in self.discovered_apis]
        }
    
    def _group_by_language(self) -> Dict[str, List[str]]:
        """Group APIs by programming language"""
        grouped = {}
        for api in self.discovered_apis:
            if api.language not in grouped:
                grouped[api.language] = []
            grouped[api.language].append(api.endpoint)
        return grouped
    
    def _group_by_framework(self) -> Dict[str, List[str]]:
        """Group APIs by framework"""
        grouped = {}
        for api in self.discovered_apis:
            if api.framework:
                if api.framework not in grouped:
                    grouped[api.framework] = []
                grouped[api.framework].append(api.endpoint)
        return grouped
    
    def _group_by_method(self) -> Dict[str, List[str]]:
        """Group APIs by HTTP method"""
        grouped = {}
        for api in self.discovered_apis:
            if api.http_method not in grouped:
                grouped[api.http_method] = []
            grouped[api.http_method].append(api.endpoint)
        return grouped
    
    def _group_by_file(self) -> Dict[str, List[str]]:
        """Group APIs by file"""
        grouped = {}
        for api in self.discovered_apis:
            if api.file_path not in grouped:
                grouped[api.file_path] = []
            grouped[api.file_path].append(api.endpoint)
        return grouped
    
    def _api_to_dict(self, api: DiscoveredAPI) -> Dict:
        """Convert API object to dictionary"""
        return {
            "name": api.name,
            "function_name": api.function_name,
            "file_path": api.file_path,
            "language": api.language,
            "framework": api.framework,
            "http_method": api.http_method,
            "endpoint": api.endpoint,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type_hint,
                    "default": p.default_value
                } for p in api.parameters
            ],
            "return_type": api.return_type,
            "docstring": api.docstring
        }
    
    def get_api_by_name(self, api_name: str) -> Optional[DiscoveredAPI]:
        """Get API by name"""
        for api in self.discovered_apis:
            if api.name == api_name or api.endpoint == api_name:
                return api
        return None
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages"""
        return [lang.value for lang in ProgrammingLanguage if lang != ProgrammingLanguage.UNKNOWN]
