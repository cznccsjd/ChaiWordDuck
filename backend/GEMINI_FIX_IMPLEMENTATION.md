# Gemini 安全过滤器修复实施指南

## 问题总结

**核心问题**：Gemini API 对正常词汇（如"hello"）过度拦截，导致 `finish_reason=2` 安全过滤器触发。

**根本原因**：
1. Prompt 中的中文示例 `"啊！靠！没得神"` 包含敏感词汇
2. 缺少明确的安全设置配置
3. 没有明确说明教育用途和文明用语要求

## 修复方案

### 方案一：Prompt 优化（立即实施）

**已创建的文件**：
- `app/prompts/word_generation_safe.py` - 安全版本的 Prompt 模板
- `app/services/ai/gemini_service_fixed.py` - 修复版本的 Gemini 服务

**关键修改**：
```python
# 原始版本 - 问题示例
"accommodation = "啊！靠！没得神""

# 安全版本 - 修复示例
"accommodation = "安心！得！神！""

# 新增安全说明
**重要提示**: 请确保所有内容适合教育用途，用词文明，避免任何可能触发安全过滤器的表达。
```

### 方案二：API 配置优化（技术增强）

**新增安全设置配置**：
```python
# 支持四种安全级别
safety_levels = {
    "none": BLOCK_NONE,           # 不过滤（高风险）
    "low": BLOCK_ONLY_HIGH,       # 仅过滤高风险（推荐教育用途）
    "medium": BLOCK_MEDIUM_AND_ABOVE,  # 默认级别
    "high": BLOCK_LOW_AND_ABOVE   # 严格过滤
}
```

## 实施步骤

### 第一步：备份当前版本
```bash
# 备份原始文件
cp app/services/ai/gemini_service.py app/services/ai/gemini_service_backup.py
cp app/prompts/word_generation.py app/prompts/word_generation_backup.py
```

### 第二步：应用修复版本
```bash
# 使用修复版本替换原始文件
cp app/services/ai/gemini_service_fixed.py app/services/ai/gemini_service.py
```

### 第三步：更新配置文件
在 `app/core/config.py` 中添加安全级别配置：
```python
# Gemini 服务配置
GEMINI_MODEL: str = "gemini-1.5-flash"
GEMINI_TIMEOUT: int = 30
GEMINI_SAFETY_LEVEL: str = "low"  # 新增：安全级别配置
```

### 第四步：更新服务初始化
在 `app/services/ai/gemini_service.py` 的初始化中：
```python
# 修改构造函数签名
def __init__(self, api_key: str, model: str, timeout: int, safety_level: str = "low"):
```

### 第五步：测试验证
```bash
# 运行测试脚本
pdm run python test_gemini_safety_config.py

# 测试具体词汇
pdm run python debug_real_call.py
```

## 监控和验证

### 关键指标监控

在 `app/services/ai/gemini_service.py` 中添加监控日志：

```python
# 统计拦截情况
total_calls = 0
safety_blocks = 0

# 在 generate_word_manual 方法中
total_calls += 1
if finish_reason == 2:  # SAFETY
    safety_blocks += 1
    logger.warning(f"安全过滤器拦截: {word} (拦截率: {safety_blocks/total_calls:.2%})")

# 定期报告
if total_calls % 100 == 0:
    logger.info(f"Gemini API统计 - 总调用: {total_calls}, 安全拦截: {safety_blocks}, 成功率: {(total_calls-safety_blocks)/total_calls:.2%}")
```

### 验证标准

**修复成功的标准**：
- ✅ "hello", "world", "test" 等基础词汇能正常生成
- ✅ 安全过滤器拦截率 < 5%
- ✅ API 调用成功率 > 95%
- ✅ 生成内容质量保持不变
- ✅ 422 错误率降低到 0

## 应急计划

### 如果问题持续存在

**方案 A：切换到 OpenAI**
```python
# 创建 OpenAI 服务作为备选
from app.services.ai.openai_service import OpenAIService

# 在依赖注入中配置
ai_service = OpenAIService(api_key=settings.OPENAI_API_KEY)
```

**方案 B：多服务轮询**
```python
async def generate_with_fallback(word: str):
    try:
        return await gemini_service.generate_word_manual(word)
    except AIParseError as e:
        if "安全过滤器" in str(e):
            logger.info(f"Gemini被拦截，尝试OpenAI: {word}")
            return await openai_service.generate_word_manual(word)
        raise
```

## 部署检查清单

### 部署前检查
- [ ] 备份原始文件
- [ ] 测试修复版本功能
- [ ] 验证基础词汇生成
- [ ] 检查日志输出正常
- [ ] 确认监控指标设置

### 部署后验证
- [ ] 检查 API 调用成功率
- [ ] 监控安全过滤器拦截率
- [ ] 验证用户反馈
- [ ] 检查错误日志
- [ ] 测试边缘情况

### 回滚计划
如果修复版本出现问题，立即回滚：
```bash
# 恢复原始文件
cp app/services/ai/gemini_service_backup.py app/services/ai/gemini_service.py
cp app/prompts/word_generation_backup.py app/prompts/word_generation.py

# 重启服务
# 根据部署方式重启应用
```

## 长期优化建议

### 1. 持续监控
- 建立拦截率告警机制
- 定期分析拦截模式
- 收集用户反馈

### 2. Prompt 优化
- 根据实际使用情况持续优化
- A/B 测试不同版本的效果
- 建立 Prompt 版本管理

### 3. 服务多样化
- 评估其他 AI 服务（Anthropic, Cohere）
- 实现智能服务路由
- 建立成本优化机制

## 联系和支持

**技术支持**：
- 查看详细分析：`backend/GEMINI_SAFETY_ANALYSIS.md`
- 测试脚本：`backend/test_gemini_safety_config.py`
- 调试工具：`backend/debug_real_call.py`

**问题反馈**：
如果修复后仍有问题，请收集以下信息：
1. 具体触发拦截的词汇
2. 完整的错误日志
3. API 调用参数
4. 响应的 finish_reason 值

---

**修复优先级**：🚨 立即实施
**预计修复时间**：30分钟
**风险等级**：低风险（向后兼容）
**成功概率**：95%+