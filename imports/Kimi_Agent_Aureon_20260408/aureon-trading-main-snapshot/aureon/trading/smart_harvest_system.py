from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            """Check if stream is already a UTF-8 TextIOWrapper."""
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            """Check if stream buffer is valid and not closed."""
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        # Only wrap if not already UTF-8 wrapped AND buffer is valid (prevents re-wrapping + closed buffer errors)
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Assuming these imports from the existing system. We will validate and adjust as we build.
# from aureon_barter_navigator import BarterNavigator
# from exchange_clients import UnifiedExchangeClient # Placeholder
# from queen_loss_learning import WinOutcome 
# from real_portfolio_tracker import RealPortfolioSnapshot

logger = logging.getLogger(__name__)

# Define preferred stablecoins in order of preference
PREFERRED_STABLES = ["USDC", "USDT", "ZUSD", "USD"]

@dataclass
class HarvestResult:
    """Result of a single harvest operation."""
    success: bool
    amount_harvested_usd: float
    stablecoin_received: float
    stablecoin_asset: str
    exchange: str
    message: str
    trade_id: Optional[str] = None

@dataclass
class SmartHarvestManager:
    """
    Manages the 10-9-1 profit harvesting and reinvestment loop.

    This system intercepts realized profits, splits them according to the 10-9-1 model,
    converts the harvested portion to stablecoins, and manages a treasury for future
    reinvestment.
    """
    barter_navigator: 'BarterNavigator'
    exchange_client: 'UnifiedExchangeClient' # A unified interface for all exchanges
    
    harvest_rate: float = 0.10  # Default 10% harvest rate
    reinvestment_threshold_usd: float = 10.0  # Minimum treasury amount to trigger reinvestment
    
    # Internal state
    _last_harvest_time: float = field(default=0.0, repr=False)
    _active_harvests: Dict[str, HarvestResult] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        logger.info(
            f"SmartHarvestManager initialized. Harvest Rate: {self.harvest_rate*100}%, "
            f"Reinvestment Threshold: ${self.reinvestment_threshold_usd}"
        )

    def process_profit(self, outcome: 'WinOutcome', portfolio: 'RealPortfolioSnapshot') -> Optional[HarvestResult]:
        """
        Processes a winning trade, harvests profit, and updates the portfolio.
        This is the primary entry point for the harvesting process.
        """
        if not outcome.is_win or outcome.net_profit_usd <= 0.01:
            return None

        profit_to_harvest = outcome.net_profit_usd * self.harvest_rate
        profit_to_compound = outcome.net_profit_usd - profit_to_harvest

        logger.info(
            f"Processing profit of ${outcome.net_profit_usd:.4f}. "
            f"Harvesting ${profit_to_harvest:.4f} (10%), Compounding ${profit_to_compound:.4f} (90%)."
        )

        # The compound portion is implicitly left in the original asset's value pool.
        # We now focus on converting the harvested amount to a stablecoin.

        # This is a placeholder for the conversion logic.
        # In the full implementation, this would find the best path from the profit asset to a stablecoin.
        harvest_result = self._convert_to_stablecoin(
            profit_to_harvest, 
            from_asset=outcome.to_asset, 
            exchange=outcome.exchange
        )

        if harvest_result and harvest_result.success:
            logger.info(f"Harvest successful: {harvest_result.message}")
            # Here we would update the RealPortfolioSnapshot with the new treasury funds.
            # portfolio.add_to_treasury(harvest_result.stablecoin_asset, harvest_result.stablecoin_received)
        else:
            logger.error(f"Harvest failed: {harvest_result.message if harvest_result else 'Unknown error'}")

        return harvest_result

    def _convert_to_stablecoin(self, amount_usd: float, from_asset: str, exchange: str) -> HarvestResult:
        """
        Finds the best path to a preferred stablecoin and executes the conversion.
        """
        if from_asset in PREFERRED_STABLES:
            return HarvestResult(
                success=True,
                amount_harvested_usd=amount_usd,
                stablecoin_received=amount_usd, # Assuming 1:1 for stables
                stablecoin_asset=from_asset,
                exchange=exchange,
                message="Profit was already in a stablecoin."
            )

        # 1. Find best stablecoin target on the given exchange
        # target_stable = self.barter_navigator.find_best_stable_on_exchange(exchange, PREFERRED_STABLES)
        target_stable = "USDC" # Placeholder

        if not target_stable:
            return HarvestResult(success=False, amount_harvested_usd=amount_usd, message=f"No suitable stablecoin target found on {exchange}.", exchange=exchange, stablecoin_received=0, stablecoin_asset='')

        # 2. Use BarterNavigator to find the best conversion path
        # path = self.barter_navigator.find_best_path(from_asset, target_stable, exchange)
        
        # 3. Execute the trade(s) via the exchange client
        # trade_result = self.exchange_client.execute_conversion_path(path)

        # This is a mock result for now.
        logger.info(f"Mock conversion: Converting ${amount_usd:.4f} of {from_asset} to {target_stable} on {exchange}.")
        time.sleep(0.1) # Simulate network latency
        
        # Simulate a small conversion fee/slippage
        final_amount = amount_usd * 0.999
        
        return HarvestResult(
            success=True,
            amount_harvested_usd=amount_usd,
            stablecoin_received=final_amount,
            stablecoin_asset=target_stable,
            exchange=exchange,
            message=f"Successfully converted {from_asset} to {target_stable}.",
            trade_id=f"mock_trade_{int(time.time())}"
        )

    def check_reinvestment_opportunities(self, portfolio: 'RealPortfolioSnapshot'):
        """
        Checks if the treasury has enough funds and if there are opportunities to deploy capital.
        """
        if portfolio.treasury_usd < self.reinvestment_threshold_usd:
            return

        logger.info(f"Treasury balance (${portfolio.treasury_usd:.2f}) exceeds threshold. Looking for reinvestment opportunities.")

        # 1. Query the Queen Hive Mind for top-rated opportunities
        # opportunities = self.queen_hive.get_best_opportunities(count=5)

        # 2. Allocate treasury funds to the best opportunity
        # best_opp = opportunities[0]
        # self.exchange_client.execute_trade(
        #     symbol=best_opp.symbol,
        #     side="buy",
        #     amount=self.reinvestment_threshold_usd,
        #     from_asset="USDC" # From treasury
        # )

        # portfolio.deploy_from_treasury(self.reinvestment_threshold_usd, "USDC")
        logger.info(f"Mock deployment: Deployed ${self.reinvestment_threshold_usd} from treasury into a new opportunity.")

        return
