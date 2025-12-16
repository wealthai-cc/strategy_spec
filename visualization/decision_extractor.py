"""
决策信息提取模块

从策略执行过程中提取决策信息，包括技术指标、触发条件、决策依据等。
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime


def extract_indicators_from_code(strategy_code: str) -> List[str]:
    """
    从策略代码中提取使用的技术指标
    
    Args:
        strategy_code: 策略代码字符串
    
    Returns:
        技术指标名称列表（如 ['MA5', 'MA20']）
    """
    indicators = []
    
    # 查找常见的指标计算模式
    patterns = [
        r'MA(\d+)\s*=',  # MA5 = ...
        r'MA(\d+)\s*:',  # MA5: ...
        r'ma(\d+)\s*=',  # ma5 = ...
        r'\.mean\(\)',  # .mean() - 可能是MA计算
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, strategy_code, re.IGNORECASE)
        for match in matches:
            if match.isdigit():
                indicators.append(f'MA{match}')
            elif 'mean' in pattern.lower():
                # 尝试从上下文推断MA周期
                # 查找 count= 或类似的参数
                count_match = re.search(r'count\s*=\s*(\d+)', strategy_code)
                if count_match:
                    indicators.append(f'MA{count_match.group(1)}')
    
    # 去重
    return list(set(indicators))


def extract_trigger_conditions_from_code(strategy_code: str) -> List[Dict[str, Any]]:
    """
    从策略代码中提取触发条件
    
    Args:
        strategy_code: 策略代码字符串
    
    Returns:
        触发条件列表，每个条件包含表达式和相关信息
    """
    conditions = []
    
    # 查找常见的条件判断模式
    # 例如：if (current_price > 1.01*MA5)
    patterns = [
        r'if\s*\([^)]*(?:>|<|>=|<=|==)[^)]+\)',  # if (price > MA5 * 1.01)
        r'if\s+[^:]+(?:>|<|>=|<=|==)[^:]+:',  # if price > MA5 * 1.01:
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, strategy_code)
        for match in matches:
            # 清理条件表达式
            condition_text = match.strip()
            # 移除 if 和括号
            condition_text = re.sub(r'^if\s*\(?', '', condition_text)
            condition_text = re.sub(r'\)?\s*:?$', '', condition_text)
            conditions.append({
                'expression': condition_text.strip(),
                'source': 'code_analysis'
            })
    
    return conditions


def extract_decision_reason_from_log(log_output: str) -> Optional[str]:
    """
    从日志输出中提取决策依据
    
    Args:
        log_output: 日志输出字符串
    
    Returns:
        决策依据字符串（如果找到）
    """
    # 查找常见的决策日志模式
    patterns = [
        r'价格.*?买入',
        r'价格.*?卖出',
        r'触发.*?买入',
        r'触发.*?卖出',
        r'买入.*?原因',
        r'卖出.*?原因',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, log_output, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None

