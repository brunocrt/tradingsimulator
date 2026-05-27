type Props = {
  label: string;
  value: string;
  tone?: "neutral" | "good" | "bad";
};

export function MetricTile({ label, value, tone = "neutral" }: Props) {
  return (
    <section className={`metric metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </section>
  );
}

