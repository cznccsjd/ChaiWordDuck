"""
Pydantic警告过滤配置模块

用于过滤Google GenAI SDK产生的Pydantic字段冲突警告
这些警告不会影响功能，但会在启动时产生噪音
"""

import warnings


def filter_pydantic_warnings():
    """过滤Google GenAI SDK产生的Pydantic警告"""

    # 过滤字段遮蔽警告
    warnings.filterwarnings(
        'ignore',
        category=UserWarning,
        module='pydantic._internal._fields',
        message=r'.*Field name.*shadows an attribute in parent.*'
    )

    # 过滤受保护命名空间冲突警告
    warnings.filterwarnings(
        'ignore',
        category=UserWarning,
        module='pydantic._internal._fields',
        message=r'.*has conflict with protected namespace.*'
    )

    # 过滤特定的model_相关警告
    warnings.filterwarnings(
        'ignore',
        category=UserWarning,
        module='pydantic._internal._fields',
        message=r'.*Field.*model_.*conflict.*'
    )