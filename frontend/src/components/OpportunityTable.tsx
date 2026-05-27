import type { Opportunity } from "../lib/types";

type Props = {
  opportunities: Opportunity[];
  loading: boolean;
  universeSize?: number;
  onSelectSymbol: (symbol: string) => void;
};

function statusClass(status: string) {
  if (status === "TOP_CANDIDATE") return "pill-good";
  if (status === "WATCH") return "pill-watch";
  return "pill-wait";
}

export function OpportunityTable({ opportunities, loading, universeSize, onSelectSymbol }: Props) {
  return (
    <section className="panel opportunities-panel" aria-busy={loading}>
      <div className="panel-heading">
        <h2>Opportunities</h2>
        <span>{loading ? "Scanning" : `${opportunities.length} ranked from ${universeSize ?? 0}`}</span>
      </div>
      <div className="table-wrap">
        <table className="opportunity-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Symbol</th>
              <th>Status</th>
              <th>Opportunity</th>
              <th>Momentum</th>
              <th>Setup</th>
              <th>20P</th>
              <th>50P</th>
              <th>R/R</th>
              <th>Strategy</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {opportunities.map((candidate) => (
              <tr key={`${candidate.rank}-${candidate.symbol}`} onClick={() => onSelectSymbol(candidate.symbol)}>
                <td>{candidate.rank}</td>
                <td>
                  <strong>{candidate.symbol}</strong>
                </td>
                <td>
                  <span className={`pill ${statusClass(candidate.status)}`}>{candidate.status.replaceAll("_", " ")}</span>
                </td>
                <td>{candidate.opportunity_score}</td>
                <td>{candidate.momentum_score}</td>
                <td>{candidate.setup_score}</td>
                <td>{candidate.return_20d_pct.toFixed(2)}%</td>
                <td>{candidate.return_50d_pct.toFixed(2)}%</td>
                <td>{candidate.risk_reward_ratio.toFixed(2)}</td>
                <td>{candidate.best_strategy.replaceAll("_", " ")}</td>
                <td>{candidate.reasons[0] ?? "No reason logged"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
