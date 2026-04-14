"""
Threat Detection Module
Analyzes input data for security threats
"""
import re
from typing import Any, Dict, List, Tuple
from enum import Enum


class ThreatLevel(Enum):
    """Threat severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SAFE = "SAFE"


class ThreatDetectedError(Exception):
    """Raised when a threat is detected"""
    pass


class ThreatDetector:
    """Detect and block malicious inputs"""
    
    # SQL Injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"('.*\bOR\b.*')",
        r"(;\s*DROP\b)",
        r"(\bINSERT\b.*VALUES)",
        r"(\bDELETE\b.*FROM\b)",
        r"(--\s*|\#|\*\/)",  # SQL comments
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(EXEC\(|EXECUTE\()",
    ]
    
    # Command Injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"([;&|`$\(\)])",  # Shell metacharacters
        r"(\$\(.*\))",  # Command substitution
        r"(`.*`)",  # Backtick execution
        r"(;\s*\w+)",  # Command chaining
        r"(&&|(?<!-)>\s*\w)",  # Pipe/redirect
    ]
    
    # Path Traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"(\.\./)",  # Directory traversal
        r"(\.\.\\)",  # Windows path traversal
        r"(%2e%2e)",  # Encoded directory traversal
        r"(\.\.[/\\]+)",  # Multiple traversals
        r"(\.\.%[2-5];?[0-9a-fA-F])",  # Various encodings
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"(<script[^>]*>)",
        r"(javascript:)",
        r"(onerror\s*=)",
        r"(onclick\s*=)",
        r"(onload\s*=)",
        r"(<iframe[^>]*>)",
        r"(<object[^>]*>)",
        r"(<embed[^>]*>)",
    ]
    
    # LDAP Injection patterns
    LDAP_PATTERNS = [
        r"(\*|&|\|)",  # LDAP operators
        r"(\([a-z]*=[^)]*\))",  # LDAP filters
    ]
    
    # Code Injection patterns
    CODE_INJECTION_PATTERNS = [
        r"(eval\()",
        r"(exec\()",
        r"(__import__)",
        r"(pickle\.)",
        r"(subprocess\.)",
        r"(os\.system)",
        r"(os\.popen)",
    ]
    
    SUSPICIOUS_KEYWORDS = [
        "delete", "drop", "truncate", "exec", "execute",
        "system", "eval", "compile", "exec",
        "subprocess", "popen", "__import__",
    ]
    
    BLOCKED_FILE_EXTENSIONS = [
        ".exe", ".bat", ".cmd", ".sh", ".py",
        ".so", ".dll", ".bin", ".app", ".jar"
    ]
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize threat detector
        
        Args:
            strict_mode: If True, flag more potential threats
        """
        self.strict_mode = strict_mode
        self.detected_threats: List[Dict] = []
    
    def analyze_input(self, input_data: Any) -> Tuple[bool, ThreatLevel, List[Dict]]:
        """
        Analyze input for threats
        
        Args:
            input_data: Input to analyze (can be string, dict, list, etc)
            
        Returns:
            Tuple of (is_safe, threat_level, threat_details)
        """
        self.detected_threats = []
        
        if isinstance(input_data, str):
            return self._analyze_string(input_data)
        elif isinstance(input_data, dict):
            return self._analyze_dict(input_data)
        elif isinstance(input_data, list):
            return self._analyze_list(input_data)
        else:
            return True, ThreatLevel.SAFE, []
    
    def _analyze_string(self, value: str) -> Tuple[bool, ThreatLevel, List[Dict]]:
        """Analyze string input"""
        threat_level = ThreatLevel.SAFE
        
        # Check for SQL injection
        sql_threats = self._check_sql_injection(value)
        if sql_threats:
            threat_level = ThreatLevel.CRITICAL
            self.detected_threats.extend(sql_threats)
        
        # Check for command injection
        cmd_threats = self._check_command_injection(value)
        if cmd_threats:
            threat_level = ThreatLevel.CRITICAL
            self.detected_threats.extend(cmd_threats)
        
        # Check for path traversal
        path_threats = self._check_path_traversal(value)
        if path_threats:
            threat_level = ThreatLevel.CRITICAL
            self.detected_threats.extend(path_threats)
        
        # Check for XSS
        xss_threats = self._check_xss(value)
        if xss_threats:
            threat_level = ThreatLevel.HIGH
            self.detected_threats.extend(xss_threats)
        
        # Check for LDAP injection
        ldap_threats = self._check_ldap_injection(value)
        if ldap_threats:
            threat_level = ThreatLevel.HIGH
            self.detected_threats.extend(ldap_threats)
        
        # Check for code injection
        code_threats = self._check_code_injection(value)
        if code_threats:
            threat_level = ThreatLevel.CRITICAL
            self.detected_threats.extend(code_threats)
        
        # Check for suspicious keywords
        keyword_threats = self._check_suspicious_keywords(value)
        if keyword_threats and self.strict_mode:
            if threat_level == ThreatLevel.SAFE:
                threat_level = ThreatLevel.MEDIUM
            self.detected_threats.extend(keyword_threats)
        
        is_safe = threat_level == ThreatLevel.SAFE
        return is_safe, threat_level, self.detected_threats
    
    def _analyze_dict(self, data: Dict) -> Tuple[bool, ThreatLevel, List[Dict]]:
        """Analyze dictionary input"""
        threat_level = ThreatLevel.SAFE
        
        for key, value in data.items():
            # Check key
            if isinstance(key, str):
                is_safe, level, threats = self._analyze_string(key)
                if not is_safe:
                    threat_level = level if self._is_higher_threat(level, threat_level) else threat_level
                    self.detected_threats.extend(threats)
            
            # Check value
            if isinstance(value, str):
                is_safe, level, threats = self._analyze_string(value)
                if not is_safe:
                    threat_level = level if self._is_higher_threat(level, threat_level) else threat_level
                    self.detected_threats.extend(threats)
            elif isinstance(value, (dict, list)):
                is_safe, level, threats = (
                    self._analyze_dict(value) if isinstance(value, dict)
                    else self._analyze_list(value)
                )
                if not is_safe:
                    threat_level = level if self._is_higher_threat(level, threat_level) else threat_level
                    self.detected_threats.extend(threats)
        
        is_safe = threat_level == ThreatLevel.SAFE
        return is_safe, threat_level, self.detected_threats
    
    def _analyze_list(self, data: List) -> Tuple[bool, ThreatLevel, List[Dict]]:
        """Analyze list input"""
        threat_level = ThreatLevel.SAFE
        
        for item in data:
            if isinstance(item, str):
                is_safe, level, threats = self._analyze_string(item)
                if not is_safe:
                    threat_level = level if self._is_higher_threat(level, threat_level) else threat_level
                    self.detected_threats.extend(threats)
            elif isinstance(item, (dict, list)):
                is_safe, level, threats = (
                    self._analyze_dict(item) if isinstance(item, dict)
                    else self._analyze_list(item)
                )
                if not is_safe:
                    threat_level = level if self._is_higher_threat(level, threat_level) else threat_level
                    self.detected_threats.extend(threats)
        
        is_safe = threat_level == ThreatLevel.SAFE
        return is_safe, threat_level, self.detected_threats
    
    def _check_sql_injection(self, value: str) -> List[Dict]:
        """Check for SQL injection patterns"""
        threats = []
        value_upper = value.upper()
        
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                threats.append({
                    "type": "SQL_INJECTION",
                    "level": ThreatLevel.CRITICAL.value,
                    "pattern": pattern,
                    "sample": value[:100]
                })
        
        return threats
    
    def _check_command_injection(self, value: str) -> List[Dict]:
        """Check for command injection patterns"""
        threats = []
        
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                threats.append({
                    "type": "COMMAND_INJECTION",
                    "level": ThreatLevel.CRITICAL.value,
                    "pattern": pattern,
                    "sample": value[:100]
                })
        
        return threats
    
    def _check_path_traversal(self, value: str) -> List[Dict]:
        """Check for path traversal attacks"""
        threats = []
        
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append({
                    "type": "PATH_TRAVERSAL",
                    "level": ThreatLevel.CRITICAL.value,
                    "pattern": pattern,
                    "sample": value[:100]
                })
        
        return threats
    
    def _check_xss(self, value: str) -> List[Dict]:
        """Check for XSS patterns"""
        threats = []
        
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append({
                    "type": "XSS",
                    "level": ThreatLevel.HIGH.value,
                    "pattern": pattern,
                    "sample": value[:100]
                })
        
        return threats
    
    def _check_ldap_injection(self, value: str) -> List[Dict]:
        """Check for LDAP injection patterns"""
        threats = []
        
        for pattern in self.LDAP_PATTERNS:
            if re.search(pattern, value):
                threats.append({
                    "type": "LDAP_INJECTION",
                    "level": ThreatLevel.HIGH.value,
                    "pattern": pattern,
                    "sample": value[:100]
                })
        
        return threats
    
    def _check_code_injection(self, value: str) -> List[Dict]:
        """Check for code injection patterns"""
        threats = []
        value_lower = value.lower()
        
        for pattern in self.CODE_INJECTION_PATTERNS:
            if re.search(pattern, value_lower):
                threats.append({
                    "type": "CODE_INJECTION",
                    "level": ThreatLevel.CRITICAL.value,
                    "pattern": pattern,
                    "sample": value[:100]
                })
        
        return threats
    
    def _check_suspicious_keywords(self, value: str) -> List[Dict]:
        """Check for suspicious keywords"""
        threats = []
        value_lower = value.lower()
        
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in value_lower:
                threats.append({
                    "type": "SUSPICIOUS_KEYWORD",
                    "level": ThreatLevel.MEDIUM.value,
                    "keyword": keyword,
                    "sample": value[:100]
                })
        
        return threats
    
    def _is_higher_threat(self, level1: ThreatLevel, level2: ThreatLevel) -> bool:
        """Check if level1 is higher threat than level2"""
        threat_order = [ThreatLevel.SAFE, ThreatLevel.LOW, ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        return threat_order.index(level1) > threat_order.index(level2)
    
    def check_file_path(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if file path is safe
        
        Args:
            file_path: File path to check
            
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check for directory traversal
        if ".." in file_path:
            return False, "Directory traversal detected"
        
        # Check for absolute paths
        if file_path.startswith("/") or (len(file_path) > 1 and file_path[1] == ":"):
            return False, "Absolute paths not allowed"
        
        # Check for blocked extensions
        for ext in self.BLOCKED_FILE_EXTENSIONS:
            if file_path.lower().endswith(ext):
                return False, f"File extension {ext} is blocked"
        
        return True, "File path is safe"
