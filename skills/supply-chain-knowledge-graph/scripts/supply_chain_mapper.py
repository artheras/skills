import argparse
import json
import sys

def generate_mock_graph(ticker: str):
    """
    Simulates querying an enterprise Knowledge Graph / Alternative Data source 
    (like Bloomberg Supply Chain or FactSet Revere).
    """
    # 模拟知识图谱数据库
    graph_db = {
        "NVDA": {
            "entity": "NVIDIA Corp.",
            "upstream_suppliers": [
                {"ticker": "TSM", "name": "Taiwan Semiconductor", "dependency_weight": 0.85, "risk": "Geopolitical"},
                {"ticker": "ASML", "name": "ASML Holding", "dependency_weight": 0.40, "risk": "Export Controls"},
                {"ticker": "SKM", "name": "SK Hynix", "dependency_weight": 0.55, "risk": "Supply Constrained"}
            ],
            "downstream_customers": [
                {"ticker": "MSFT", "name": "Microsoft", "revenue_share": 0.22},
                {"ticker": "META", "name": "Meta Platforms", "revenue_share": 0.18},
                {"ticker": "GOOGL", "name": "Alphabet", "revenue_share": 0.15}
            ],
            "competitors": [
                {"ticker": "AMD", "name": "Advanced Micro Devices"},
                {"ticker": "INTC", "name": "Intel Corp"}
            ]
        },
        "AAPL": {
            "entity": "Apple Inc.",
            "upstream_suppliers": [
                {"ticker": "TSM", "name": "Taiwan Semiconductor", "dependency_weight": 0.90, "risk": "Geopolitical"},
                {"ticker": "HON.TW", "name": "Foxconn", "dependency_weight": 0.70, "risk": "Labor/Geopolitical"}
            ],
            "downstream_customers": [
                {"name": "Consumer Retail", "revenue_share": 0.80},
                {"name": "Enterprise", "revenue_share": 0.20}
            ],
            "competitors": [
                {"ticker": "SSNLF", "name": "Samsung Electronics"}
            ]
        }
    }

    ticker = ticker.upper()
    if ticker not in graph_db:
        return {"error": f"Ticker {ticker} not found in the Knowledge Graph DB."}
    
    return graph_db[ticker]

def run_gate(ticker: str):
    print(f"🔍 [Knowledge Graph Mapper] Analyzing supply chain for: {ticker}\n")
    data = generate_mock_graph(ticker)
    
    if "error" in data:
        print(f"❌ FAIL: {data['error']}")
        sys.exit(1)
        
    print(f"🏢 Entity: {data['entity']}\n")
    
    print("🔺 UPSTREAM SUPPLIERS (Cost / Risk Drivers):")
    for supplier in data['upstream_suppliers']:
        warn = "⚠️ HIGH DEPENDENCY" if supplier['dependency_weight'] > 0.5 else ""
        # :.1f — 不加格式化时 0.55*100 会印成 55.00000000000001（二进制浮点表示误差），
        # 出现在给人看的风险报告里会让整份输出显得不可信。
        print(f"  - {supplier['name']} ({supplier.get('ticker', 'N/A')}): {supplier['dependency_weight']*100:.1f}% dependency. Risk: {supplier['risk']} {warn}")

    print("\n🔻 DOWNSTREAM CUSTOMERS (Revenue Drivers):")
    for customer in data['downstream_customers']:
        warn = "⚠️ CONCENTRATION RISK" if customer['revenue_share'] > 0.15 else ""
        print(f"  - {customer['name']} ({customer.get('ticker', 'N/A')}): {customer['revenue_share']*100:.1f}% revenue. {warn}")
        
    print("\n⚔️ COMPETITORS:")
    for comp in data['competitors']:
        print(f"  - {comp['name']} ({comp.get('ticker', 'N/A')})")
        
    print("\n✅ PASS: Knowledge graph expansion completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Map supply chain dependencies.")
    parser.add_argument("--demo", action="store_true", help="Run the demo simulation for NVDA")
    parser.add_argument("--ticker", type=str, help="Target ticker to map")
    
    args = parser.parse_args()
    
    if args.demo:
        run_gate("NVDA")
    elif args.ticker:
        run_gate(args.ticker)
    else:
        parser.print_help()
        sys.exit(1)
