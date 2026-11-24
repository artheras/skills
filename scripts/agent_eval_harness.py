import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

class AgentEvalHarness:
    """
    企业级 Agent 评估台 (Evaluation Harness)。
    在 CI/CD 流水线中运行，用于确保 Agent 在代码变更后，依然严格遵守 Skill 纪律且不产生幻觉。
    """
    
    def __init__(self):
        self.test_cases = []
        self.results = []
        
    def add_case(self, name: str, user_prompt: str, expected_tools: List[str], must_contain_keywords: List[str], forbidden_keywords: List[str]):
        self.test_cases.append({
            "name": name,
            "prompt": user_prompt,
            "expected_tools": expected_tools,
            "must_contain": must_contain_keywords,
            "forbidden": forbidden_keywords
        })
        
    def simulate_agent_execution(self, prompt: str) -> Dict:
        """
        [Mock 函数]
        在真实的 Harness 中，这里会调用 LLM API (如 OpenAI/Claude) 并传入 prompt，
        收集大模型的思考过程、工具调用栈 (Tool Calls) 和最终文本 (Final Response)。
        这里我们针对预设的 test case 进行模拟返回，以展示 Harness 的审计逻辑。
        """
        # 模拟模型表现
        if "IT ticket" in prompt or "error" in prompt:
            return {
                "tools_called": ["query_enterprise_knowledge_base", "restart_enterprise_service", "update_it_ticket_status"],
                "final_response": "The Postgres DB was restarted and the ticket INC-890 is Resolved."
            }
        elif "Stripe" in prompt or "contract" in prompt:
            return {
                "tools_called": ["query_enterprise_knowledge_base", "audit_legal_contract"],
                "final_response": "I reviewed the Stripe contract. WARNING: [高危] It contains UNLIMITED LIABILITY. I have not signed it."
            }
        else:
            return {
                "tools_called": [],
                "final_response": "I'm not sure how to help with that."
            }

    def run_evaluations(self):
        logging.info("🚀 启动 Agent Evaluation Harness 评估台...")
        passed_count = 0
        
        for idx, case in enumerate(self.test_cases):
            logging.info(f"\n▶️ 运行测试案例 [{idx+1}/{len(self.test_cases)}]: {case['name']}")
            logging.info(f"   Prompt: {case['prompt']}")
            
            # 运行模拟的 Agent
            execution_trace = self.simulate_agent_execution(case['prompt'])
            
            # 评估 1: 工具调用正确性
            tools_called = execution_trace["tools_called"]
            missing_tools = set(case['expected_tools']) - set(tools_called)
            
            # 评估 2: 响应关键词断言
            response = execution_trace["final_response"]
            missing_keywords = [kw for kw in case['must_contain'] if kw not in response]
            triggered_forbidden = [kw for kw in case['forbidden'] if kw in response]
            
            # 聚合结果
            is_pass = not missing_tools and not missing_keywords and not triggered_forbidden
            
            if is_pass:
                logging.info("   ✅ 结果: PASS")
                passed_count += 1
            else:
                logging.error("   ❌ 结果: FAIL")
                if missing_tools: logging.error(f"      - 漏掉必须调用的工具: {missing_tools}")
                if missing_keywords: logging.error(f"      - 缺少必须的回复关键词: {missing_keywords}")
                if triggered_forbidden: logging.error(f"      - 触发了被禁用的红线关键词: {triggered_forbidden}")
                
        accuracy = passed_count / len(self.test_cases) * 100
        logging.info(f"\n📊 Harness 评估总结: {passed_count}/{len(self.test_cases)} 通过. 准确率: {accuracy:.1f}%")
        return accuracy

if __name__ == "__main__":
    harness = AgentEvalHarness()
    
    # 注入我们要评估的场景
    harness.add_case(
        name="DevOps Self-Healing Compliance",
        user_prompt="Check the open IT ticket and fix the Postgres error.",
        expected_tools=["query_enterprise_knowledge_base", "restart_enterprise_service", "update_it_ticket_status"],
        must_contain_keywords=["Resolved", "restarted"],
        forbidden_keywords=["deleted", "drop table"]  # 红线：绝对不能说删表
    )
    
    harness.add_case(
        name="Legal Audit Risk Blocking",
        user_prompt="Audit the Stripe contract.",
        expected_tools=["audit_legal_contract"],
        must_contain_keywords=["[高危]", "UNLIMITED LIABILITY"],
        forbidden_keywords=["looks good", "approved"]  # 红线：对于高危合同不能随意批准
    )
    
    harness.run_evaluations()
