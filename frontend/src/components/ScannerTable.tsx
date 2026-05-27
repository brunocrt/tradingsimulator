import type { Signal } from "../lib/types";

type Props = {
  signals: Signal[];
};

export function ScannerTable({ signals }: Props) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Scanner</h2>
        <span>{signals.length} decisions</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Strategy</th>
              <th>Status</th>
              <th>Score</th>
              <th>Entry</th>
              <th>Stop</th>
              <th>Target</th>
              <th>R/R</th>
              <th>Crowding</th>
              <th>Trap</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {signals.map((signal) => (
              <tr key={`${signal.symbol}-${signal.strategy_name}`}>
                <td>{signal.symbol}</td>
                <td>{signal.strategy_name.replaceAll("_", " ")}</td>
                <td>
                  <span className={`pill ${signal.status === "APPROVED" ? "pill-good" : "pill-wait"}`}>
                    {signal.status}
                  </span>
                </td>
                <td>{signal.score}</td>
                <td>${signal.entry_price.toFixed(2)}</td>
                <td>${signal.stop_price.toFixed(2)}</td>
                <td>${signal.target_price.toFixed(2)}</td>
                <td>{signal.risk_reward_ratio.toFixed(2)}</td>
                <td>{signal.crowding_score}</td>
                <td>{signal.trap_risk_score}</td>
                <td>{signal.reasons[0] ?? "No reason logged"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

