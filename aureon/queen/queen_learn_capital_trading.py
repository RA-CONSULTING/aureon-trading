#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     👑📚 QUEEN LEARNS CAPITAL.COM CFD TRADING via Wikipedia 📚👑             ║
║                                                                              ║
║     The Queen will research and learn:                                       ║
║     • CFD Trading strategies                                                 ║
║     • Forex trading patterns                                                 ║
║     • Risk management for leverage                                           ║
║     • Capital.com specific features                                          ║
║                                                                              ║
║     Gary Leckey | January 2026 | "Let the Queen evolve"                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Queen's learning systems
try:
    from queen_loss_learning import QueenLossLearningSystem
    LOSS_LEARNING_AVAILABLE = True
except ImportError:
    QueenLossLearningSystem = None
    LOSS_LEARNING_AVAILABLE = False

try:
    from queen_online_researcher import QueenOnlineResearcher
    RESEARCHER_AVAILABLE = True
except ImportError:
    QueenOnlineResearcher = None
    RESEARCHER_AVAILABLE = False

try:
    from capital_client import CapitalClient
    CAPITAL_AVAILABLE = True
except ImportError:
    CapitalClient = None
    CAPITAL_AVAILABLE = False


class QueenCapitalLearner:
    """
    👑📚 Queen's Capital.com Learning & Trading System
    
    Combines:
    - Wikipedia research for CFD trading knowledge
    - Loss learning from failed trades
    - Online researcher for strategies
    - Capital.com API integration
    """
    
    def __init__(self):
        self.learning_active = False
        self.knowledge_base = {
            'cfd_strategies': [],
            'forex_patterns': [],
            'risk_rules': [],
            'verified_tactics': []
        }
        
        # Initialize Queen's brain modules
        if LOSS_LEARNING_AVAILABLE:
            self.loss_learner = QueenLossLearningSystem()
            logger.info("👑 Queen Loss Learning System: ACTIVE")
        else:
            self.loss_learner = None
            logger.warning("⚠️ Queen Loss Learning System: NOT AVAILABLE")
        
        if RESEARCHER_AVAILABLE:
            self.researcher = QueenOnlineResearcher()
            logger.info("👑 Queen Online Researcher: ACTIVE")
        else:
            self.researcher = None
            logger.warning("⚠️ Queen Online Researcher: NOT AVAILABLE")
        
        if CAPITAL_AVAILABLE:
            self.capital = CapitalClient()
            logger.info("👑 Capital.com Client: CONNECTED")
        else:
            self.capital = None
            logger.warning("⚠️ Capital.com Client: NOT AVAILABLE")
    
    def research_cfd_trading(self):
        """Research CFD trading strategies from Wikipedia"""
        print("\n" + "="*70)
        print("👑📚 QUEEN RESEARCHING: CFD Trading on Wikipedia")
        print("="*70)
        
        if not self.loss_learner:
            print("⚠️ Wikipedia research not available - Loss Learning System missing")
            return
        
        # Use the Queen's built-in warfare research which uses Wikipedia
        print(f"\n📚 Researching warfare tactics applied to CFD trading...")
        try:
            researched = self.loss_learner.research_warfare_tactics()
            
            if researched:
                print(f"✅ Learned {len(researched)} new tactics from Wikipedia:")
                for item in researched[:5]:  # Show first 5
                    print(f"\n  📖 Topic: {item['topic']}")
                    tactic = item.get('tactic', {})
                    trading_app = tactic.get('trading_application', 'N/A')
                    print(f"  🎯 Trading Application: {trading_app[:120]}...")
                    
                    self.knowledge_base['cfd_strategies'].append({
                        'topic': item['topic'],
                        'category': item['category'],
                        'insight': trading_app,
                        'learned_at': datetime.now().isoformat()
                    })
            else:
                print("⚠️ No tactics learned (may be cached from recent research)")
                
        except Exception as e:
            print(f"❌ Error during Wikipedia research: {e}")
            import traceback
            traceback.print_exc()
        
        # Now research CFD-specific topics using direct Wikipedia calls
        print(f"\n📚 Researching CFD-specific topics...")
        try:
            import wikipedia
            
            cfd_topics = [
                "Contract for difference",
                "Forex trading", 
                "Leverage (finance)",
                "Stop-loss order"
            ]
            
            for topic in cfd_topics:
                try:
                    print(f"\n  🔍 Researching: {topic}")
                    summary = wikipedia.summary(topic, sentences=3, auto_suggest=False)
                    
                    if summary:
                        self.knowledge_base['cfd_strategies'].append({
                            'topic': topic,
                            'insight': summary,
                            'learned_at': datetime.now().isoformat()
                        })
                        print(f"  ✅ {summary[:100]}...")
                except Exception as e:
                    print(f"  ⚠️ Could not research {topic}: {e}")
            
        except ImportError:
            print("⚠️ Wikipedia package not installed")
        except Exception as e:
            print(f"❌ Error researching CFD topics: {e}")
        
        print(f"\n✅ Research complete! Total knowledge: {len(self.knowledge_base['cfd_strategies'])} concepts")
    
    def learn_capital_capabilities(self):
        """Learn what Capital.com can trade"""
        print("\n" + "="*70)
        print("👑🔍 QUEEN LEARNING: Capital.com Capabilities")
        print("="*70)
        
        if not self.capital:
            print("⚠️ Capital.com client not available")
            return
        
        # Get account info
        try:
            accounts = self.capital.get_accounts()
            print(f"\n📊 Capital.com Accounts: {len(accounts) if accounts else 0}")
            
            if accounts:
                for acc in accounts:
                    balance = acc.get('balance', {})
                    print(f"  💰 Balance: {balance.get('balance', 0)} {balance.get('currency', 'GBP')}")
        except Exception as e:
            print(f"⚠️ Could not fetch accounts: {e}")
        
        # Get available markets
        try:
            print("\n📡 Fetching available markets...")
            markets = self.capital.get_all_markets()
            if markets:
                print(f"✅ Found {len(markets)} tradeable markets on Capital.com")
                
                # Categorize markets
                categories = {}
                for market in markets[:100]:  # First 100 for demo
                    market_type = market.get('marketType', 'UNKNOWN')
                    if market_type not in categories:
                        categories[market_type] = []
                    categories[market_type].append(market.get('instrumentName', 'Unknown'))
                
                print(f"\n📊 Market Categories:")
                for cat, items in categories.items():
                    print(f"  • {cat}: {len(items)} markets")
                    # Show 3 examples
                    for ex in items[:3]:
                        print(f"    - {ex}")
                
                self.knowledge_base['verified_tactics'].append({
                    'capability': 'capital_markets',
                    'total_markets': len(markets),
                    'categories': list(categories.keys()),
                    'learned_at': datetime.now().isoformat()
                })
            else:
                print("⚠️ No markets available")
        except Exception as e:
            print(f"⚠️ Could not fetch markets: {e}")
    
    def apply_learned_risk_rules(self):
        """Apply learned risk management rules"""
        print("\n" + "="*70)
        print("👑🛡️ QUEEN APPLYING: Risk Management Rules")
        print("="*70)
        
        # Extract risk rules from learned knowledge
        risk_rules = []
        for strategy in self.knowledge_base.get('cfd_strategies', []):
            insight = strategy.get('insight', '').lower()
            
            # Pattern match for risk-related insights
            if any(word in insight for word in ['risk', 'loss', 'stop', 'leverage', 'margin']):
                risk_rules.append({
                    'source': strategy['topic'],
                    'rule': strategy['insight']
                })
        
        if risk_rules:
            print(f"\n✅ Extracted {len(risk_rules)} risk management rules:")
            for i, rule in enumerate(risk_rules, 1):
                print(f"\n[Rule {i}] From: {rule['source']}")
                print(f"  📜 {rule['rule'][:200]}...")
            
            self.knowledge_base['risk_rules'] = risk_rules
        else:
            print("\n⚠️ No risk rules extracted yet. More research needed.")
    
    def save_knowledge(self, filepath: str = "queen_capital_knowledge.json"):
        """Save Queen's learned knowledge"""
        print(f"\n💾 Saving Queen's knowledge to {filepath}...")
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    'saved_at': datetime.now().isoformat(),
                    'knowledge_base': self.knowledge_base,
                    'total_strategies': len(self.knowledge_base.get('cfd_strategies', [])),
                    'total_risk_rules': len(self.knowledge_base.get('risk_rules', [])),
                    'capabilities_learned': len(self.knowledge_base.get('verified_tactics', []))
                }, f, indent=2)
            print(f"✅ Knowledge saved successfully!")
        except Exception as e:
            print(f"❌ Error saving knowledge: {e}")
    
    def demonstrate_learning(self):
        """Full demonstration of Queen's learning capabilities"""
        print("\n" + "="*70)
        print("👑🌟 QUEEN SERO - CAPITAL.COM LEARNING DEMONSTRATION 🌟👑")
        print("="*70)
        print("\nThe Queen will now:")
        print("  1. Research CFD trading via Wikipedia")
        print("  2. Learn Capital.com capabilities")
        print("  3. Extract and apply risk management rules")
        print("  4. Save all learned knowledge")
        print("\n" + "="*70)
        
        # Execute learning sequence
        self.research_cfd_trading()
        self.learn_capital_capabilities()
        self.apply_learned_risk_rules()
        
        # Summary
        print("\n" + "="*70)
        print("👑📊 LEARNING SESSION SUMMARY")
        print("="*70)
        print(f"  📚 CFD Strategies Learned: {len(self.knowledge_base.get('cfd_strategies', []))}")
        print(f"  🛡️ Risk Rules Extracted: {len(self.knowledge_base.get('risk_rules', []))}")
        print(f"  ✅ Capabilities Verified: {len(self.knowledge_base.get('verified_tactics', []))}")
        print("="*70)
        
        # Save knowledge
        self.save_knowledge()
        
        print("\n👑 Queen has successfully learned new Capital.com trading skills!")
        print("💎 Knowledge base updated and ready for deployment")


if __name__ == "__main__":
    print("\n🚀 Initializing Queen's Learning System...")
    
    try:
        learner = QueenCapitalLearner()
        learner.demonstrate_learning()
        
        print("\n✅ Queen learning session complete!")
        print("📖 Check 'queen_capital_knowledge.json' for saved knowledge")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Learning session interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Learning session failed: {e}")
        import traceback
        traceback.print_exc()
