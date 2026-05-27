import {
  ColorType,
  CrosshairMode,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type Time,
  type UTCTimestamp
} from "lightweight-charts";
import { useEffect, useMemo, useRef } from "react";
import type { Candle, Trade } from "../lib/types";

type Props = {
  candles: Candle[];
  selectedTrade: Trade | null;
  trades: Trade[];
};

type ChartCandle = {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
};

function toChartTime(timestamp: string): UTCTimestamp {
  return Math.floor(new Date(timestamp).getTime() / 1000) as UTCTimestamp;
}

function ema(values: number[], period: number): number[] {
  const alpha = 2 / (period + 1);
  const output: number[] = [];
  let previous = values[0] ?? 0;
  for (const value of values) {
    previous = output.length === 0 ? value : alpha * value + (1 - alpha) * previous;
    output.push(previous);
  }
  return output;
}

function vwap(candles: Candle[]): number[] {
  let notional = 0;
  let volume = 0;
  return candles.map((candle) => {
    const typical = (candle.high + candle.low + candle.close) / 3;
    notional += typical * candle.volume;
    volume += candle.volume;
    return volume > 0 ? notional / volume : candle.close;
  });
}

function lineData(candles: Candle[], values: number[]): LineData[] {
  return candles.map((candle, index) => ({
    time: toChartTime(candle.timestamp),
    value: Number(values[index].toFixed(4))
  }));
}

function priceLineTitle(trade: Trade | null) {
  if (!trade) return "No trade selected";
  return `${trade.symbol} ${trade.exit_reason.replaceAll("_", " ")}`;
}

export function TradeChart({ candles, selectedTrade, trades }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const vwapSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const ema9SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const ema20SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const entryLineRef = useRef<ReturnType<ISeriesApi<"Candlestick">["createPriceLine"]> | null>(null);
  const stopLineRef = useRef<ReturnType<ISeriesApi<"Candlestick">["createPriceLine"]> | null>(null);
  const targetLineRef = useRef<ReturnType<ISeriesApi<"Candlestick">["createPriceLine"]> | null>(null);

  const chartData = useMemo<ChartCandle[]>(
    () =>
      candles.map((candle) => ({
        time: toChartTime(candle.timestamp),
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close
      })),
    [candles]
  );

  const overlays = useMemo(() => {
    const closes = candles.map((candle) => candle.close);
    return {
      vwap: lineData(candles, vwap(candles)),
      ema9: lineData(candles, ema(closes, 9)),
      ema20: lineData(candles, ema(closes, 20))
    };
  }, [candles]);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      autoSize: true,
      height: 420,
      layout: {
        background: { type: ColorType.Solid, color: "#ffffff" },
        textColor: "#4f5e56"
      },
      grid: {
        horzLines: { color: "#edf1ee" },
        vertLines: { color: "#edf1ee" }
      },
      crosshair: {
        mode: CrosshairMode.Normal
      },
      rightPriceScale: {
        borderColor: "#dbe2dd"
      },
      timeScale: {
        borderColor: "#dbe2dd",
        timeVisible: true
      }
    });

    const candlesSeries = chart.addCandlestickSeries({
      upColor: "#137a43",
      borderUpColor: "#137a43",
      wickUpColor: "#137a43",
      downColor: "#b42318",
      borderDownColor: "#b42318",
      wickDownColor: "#b42318"
    });
    vwapSeriesRef.current = chart.addLineSeries({ color: "#2f6fbb", lineWidth: 2, title: "VWAP" });
    ema9SeriesRef.current = chart.addLineSeries({ color: "#b7791f", lineWidth: 1, title: "EMA 9" });
    ema20SeriesRef.current = chart.addLineSeries({ color: "#5b6472", lineWidth: 1, title: "EMA 20" });

    chartRef.current = chart;
    candleSeriesRef.current = candlesSeries;

    return () => {
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      vwapSeriesRef.current = null;
      ema9SeriesRef.current = null;
      ema20SeriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current || !candleSeriesRef.current) return;
    candleSeriesRef.current.setData(chartData);
    vwapSeriesRef.current?.setData(overlays.vwap);
    ema9SeriesRef.current?.setData(overlays.ema9);
    ema20SeriesRef.current?.setData(overlays.ema20);
    chartRef.current.timeScale().fitContent();
  }, [chartData, overlays]);

  useEffect(() => {
    if (!candleSeriesRef.current) return;
    const markers = trades.flatMap((trade) => [
      {
        time: toChartTime(trade.entry_time) as Time,
        position: "belowBar" as const,
        color: "#137a43",
        shape: "arrowUp" as const,
        text: "Entry"
      },
      {
        time: toChartTime(trade.exit_time) as Time,
        position: "aboveBar" as const,
        color: trade.net_pnl >= 0 ? "#137a43" : "#b42318",
        shape: "arrowDown" as const,
        text: "Exit"
      }
    ]);
    candleSeriesRef.current.setMarkers(markers);
  }, [trades]);

  useEffect(() => {
    if (!candleSeriesRef.current) return;
    for (const line of [entryLineRef.current, stopLineRef.current, targetLineRef.current]) {
      if (line) candleSeriesRef.current.removePriceLine(line);
    }
    entryLineRef.current = null;
    stopLineRef.current = null;
    targetLineRef.current = null;

    if (!selectedTrade) return;
    const plannedRiskPerShare = selectedTrade.risk_amount / Math.max(selectedTrade.shares, 1);
    const plannedRewardPerShare = selectedTrade.reward_amount / Math.max(selectedTrade.shares, 1);
    entryLineRef.current = candleSeriesRef.current.createPriceLine({
      price: selectedTrade.entry_price,
      color: "#137a43",
      lineWidth: 2,
      lineStyle: 2,
      axisLabelVisible: true,
      title: "Entry"
    });
    stopLineRef.current = candleSeriesRef.current.createPriceLine({
      price: selectedTrade.entry_price - plannedRiskPerShare,
      color: "#b42318",
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: true,
      title: "Planned risk"
    });
    targetLineRef.current = candleSeriesRef.current.createPriceLine({
      price: selectedTrade.entry_price + plannedRewardPerShare,
      color: "#2f6fbb",
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: true,
      title: "Target"
    });
  }, [selectedTrade]);

  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <h2>Trade View</h2>
        <span>{priceLineTitle(selectedTrade)}</span>
      </div>
      <div className="chart-surface" ref={containerRef} />
    </section>
  );
}
