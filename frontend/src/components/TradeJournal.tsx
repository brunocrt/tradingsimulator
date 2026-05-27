import type { Trade } from "../lib/types";

type Props = {
  trades: Trade[];
  selectedTrade: Trade | null;
  onSelectTrade: (trade: Trade) => void;
};

export function TradeJournal({ trades, selectedTrade, onSelectTrade }: Props) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Trade Journal</h2>
        <span>{trades.length} closed trades</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Strategy</th>
              <th>Shares</th>
              <th>Entry</th>
              <th>Exit</th>
              <th>Net P&L</th>
              <th>Costs</th>
              <th>Exit</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade, index) => (
              <tr
                className={selectedTrade === trade ? "selected-row" : ""}
                key={`${trade.symbol}-${trade.exit_time}-${index}`}
                onClick={() => onSelectTrade(trade)}
              >
                <td>{trade.symbol}</td>
                <td>{trade.strategy.replaceAll("_", " ")}</td>
                <td>{trade.shares}</td>
                <td>${trade.entry_price.toFixed(2)}</td>
                <td>${trade.exit_price.toFixed(2)}</td>
                <td className={trade.net_pnl >= 0 ? "money-good" : "money-bad"}>
                  ${trade.net_pnl.toFixed(2)}
                </td>
                <td>${(trade.fees + trade.slippage * trade.shares).toFixed(2)}</td>
                <td>{trade.exit_reason.replaceAll("_", " ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
